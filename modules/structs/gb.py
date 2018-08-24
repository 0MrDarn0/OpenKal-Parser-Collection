#!/usr/bin/python3.5

import io
import sys
import utility
import numpy as np

from struct import unpack
from utility import ValidationError
from utility import VersionError


class GBArmature(object):
    __slots__ = [
        'bones',
    ]

    def parse(self, stream, b_count):
        self.bones = []
        for _ in range(b_count):
            self.bones.append(GBBone().parse(stream))

        return self

    def write(self, stream):
        raise NotImplementedError


class GBBone(object):
    __slots__ = [
        'matrix',
        'parent',  #  no parent: 0xFF
    ]

    def parse(self, stream):
        self.matrix = utility.read_d3dx_matrix4(stream)
        self.parent = unpack('<B', stream.read(1))[0]
        return self

    def write(self, stream):
        raise NotImplementedError


class GBAnimation(object):
    __slots__ = [
        'option',
        'keyframes',
        'keyframe_frames',
        'keyframe_events'
    ]

    def parse_descriptor(self, descriptor):
        self.option = utility.read_string_zero(descriptor, self.option)

        for i, index in enumerate(self.keyframe_events):
            self.keyframe_events[i] = (
                    utility.read_string_zero(descriptor, index))

    def write_descriptor(self, descriptor):
        raise NotImplementedError

    def parse(self, stream, b_count):
        self.option, k_count = unpack('<IH', stream.read(6))

        self.keyframes = []
        self.keyframe_frames = []
        self.keyframe_events = []

        for _ in range(k_count):
            self.keyframe_frames.append(unpack('<H', stream.read(2))[0])
            self.keyframe_events.append(unpack('<I', stream.read(4))[0])

        for _ in range(k_count):
            self.keyframes.append(
                    np.frombuffer(stream.read(2 * b_count), np.uint16))

        return self

    def write(self, stream):
        raise NotImplementedError


class GBTransformation(object):
    __slots__ = [
        'position',
        'rotation',
        'scale',
    ]

    def parse(self, stream):
        self.position = utility.read_d3dx_vector3(stream)
        self.rotation = utility.read_d3dx_quaternion(stream)
        self.scale = utility.read_d3dx_vector3(stream)
        return self

    def write(self, stream):
        raise NotImplementedError


class GBMaterial(object):
    __slots__ = [
        'texture',
        'options',
        'frames',
    ]

    OPTIONS = {
        0x1   : 'TWOSIDED',
        0x2   : 'OPACITY',
        0x4   : 'ARGB',
        0x8   : 'SPECULAR',
        0x20  : 'LIGHT',
        0x100 : 'LIGHTMAP',
        0x200 : 'FX',
    }

    def parse_descriptor(self, descriptor, frame_count):
        descriptor.seek(self.frames)

        self.frames = []
        for _ in range(frame_count):
            self.frames.append(GBMaterialFrame().parse(descriptor))

        self.texture = utility.read_string_zero(descriptor, self.texture)

    def write_descriptor(self, descriptor):
        raise NotImplementedError

    def parse(self, stream):
        self.texture, \
        self.options, \
        _,            \
        _,            \
        self.frames = unpack('<IHIfI', stream.read(18))

        # Create option set
        options = set()
        for v in GBMaterial.OPTIONS:
            if self.options & v:
                options.add(GBMaterial.OPTIONS[v])

        self.options = options

        return self

    def write(self, stream):
        raise NotImplementedError

    @property
    def provides_animation(self):
        return len(self.frames) > 1

    @property
    def frame(self):
        return self.frames[0]


class GBMaterialFrame(object):
    __slots__ = [
        'texture_off',
        'texture_rot',
        'light_a',  # ambient
        'light_d',  # diffuse
        'light_s',  # specular
        'opacity',
    ]

    def parse(self, stream):
        self.light_a = utility.read_d3d_color(stream)
        self.light_d = utility.read_d3d_color(stream)
        self.light_s = utility.read_d3d_color(stream)
        self.opacity = unpack('<f', stream.read(4))[0]

        self.texture_off = utility.read_d3dx_vector2(stream)
        self.texture_rot = utility.read_d3dx_vector3(stream)

        return self

    def write(self, stream):
        raise NotImplementedError


class GBMesh(object):
    __slots__ = [
        'name',
        'material',
        'verts',
        'faces',
        'bones',
    ]

    # Face types
    _FT_LIST  = 0
    _FT_STRIP = 1
    _FT_END   = 2

    # Vertex types
    _VT_RIGID        = 0
    _VT_BLEND1       = 1
    _VT_BLEND2       = 2
    _VT_BLEND3       = 3
    _VT_BLEND4       = 4
    _VT_RIGID_DOUBLE = 5
    _VT_END          = 6

    def mkfaces(indexes):
        result = []
        # Example: [0,1,2,3,4,5] -> [(0,1,2),(3,4,5)]
        for a, b, c in zip(*[iter(indexes)] * 3):
            if a == b or a == c or b == c:
                continue

            result.append((a, b, c))

        return result

    def unstrip(indexes):
        """Converts an index strip to an index list."""
        result = []
        for i in range(len(indexes) - 2):
            if i & 1:
                result.extend([indexes[i], indexes[i + 2], indexes[i + 1]])
            else:
                result.extend([indexes[i], indexes[i + 1], indexes[i + 2]])

        return result

    def rmdupes(faces):
        """Removes duplicates ignoring order, e.g. (0, 1, 2) == (2, 1, 0)."""
        mask = []
        seen = set()
        for s in map(frozenset, faces):
            if s in seen:
                mask.append(False)
            else:
                mask.append(True)

            seen.add(s)

        return np.array(faces)[np.array(mask)]

    def _parse_vertex(self, stream, v_type):
        vertex = {'v' : utility.read_d3dx_vector3(stream)}

        # Bone weights
        if 2 <= v_type <= 4:
            vertex['weights'] = np.frombuffer(
                    stream.read(4 * v_type - 4), np.float32)

        # Bone indexes which influence this vertex
        if 1 <= v_type <= 4:
            vertex['indexes'] = np.frombuffer(stream.read(4), np.uint8)

        # Texture coordinate(s) and vertex normal
        vertex['vn'] = utility.read_d3dx_vector3(stream)
        vertex['t0'] = utility.read_d3dx_vector2(stream)

        if v_type >= 5:
            vertex['t1'] = utility.read_d3dx_vector2(stream)

        return vertex

    def _write_vertex(self, stream, v_type):
        raise NotImplementedError

    def parse_descriptor(self, descriptor):
        self.name = utility.read_string_zero(descriptor, self.name)

    def write_descriptor(self, descriptor):
        raise NotImplementedError

    def parse(self, stream, gb_version):
        # The sources define material as a signed integer.
        # However, it can safely be read as an unsigned one.

        self.name, self.material = unpack('<II', stream.read(8))

        v_type,  \
        f_type,  \
        v_count, \
        f_count, \
        b_count = unpack('<BBHHB', stream.read(7))

        # Type definition changed in version 12
        if gb_version < 11 and v_type > 0:
            v_type = v_type - 1

        self.verts = []
        self.faces = []
        self.bones = []

        for _ in range(b_count):
            self.bones.append(unpack('<B', stream.read(1))[0])

        for _ in range(v_count):
            self.verts.append(self._parse_vertex(stream, v_type))

        for _ in range(f_count):
            self.faces.append(unpack('<H', stream.read(2))[0])

        if f_type != GBMesh._FT_LIST:
            self.faces = GBMesh.unstrip(self.faces)

        self.faces = GBMesh.mkfaces(self.faces)
        self.faces = GBMesh.rmdupes(self.faces)

        return self

    def write(self, stream, gb_version):
        raise NotImplementedError


class GBCollision(object):
    __slots__ = [
        'bounding_box_min',
        'bounding_box_max',
        'verts',
        'faces',
        'nodes',
    ]

    def parse(self, stream, gb_version,
            bounding_box_min=None,
            bounding_box_max=None):
        v_count, f_count = unpack('<HH', stream.read(4))

        if gb_version < 11:
            self.bounding_box_min = utility.read_d3dx_vector3(stream)
            self.bounding_box_max = utility.read_d3dx_vector3(stream)
        else:
            self.bounding_box_min = bounding_box_min
            self.bounding_box_max = bounding_box_max
            stream.read(24)

        self.verts = np.frombuffer(stream.read(6 * v_count), (np.uint16, 3))
        self.faces = np.frombuffer(stream.read(6 * f_count), (np.uint16, 3))

        self.nodes = []
        for _ in range(f_count - 1):
            self.nodes.append(GBCollisionNode().parse(stream))

        # Create vertices
        self.verts = [{'v' : v} for v in
                self.scale * self.verts + self.bounding_box_min]

        self.faces = GBMesh.rmdupes(self.faces) // 3

        return self

    def write(self, stream, gb_version):
        raise NotImplementedError

    @property
    def scale(self):
        return (self.bounding_box_max - self.bounding_box_min) / 0xFFFF


class GBCollisionNode(object):
    __slots__ = [
        'flags',
        'min',
        'max',
        'child_l',
        'child_r',
    ]

    L_LEAF   = 0x1
    R_LEAF   = 0x2
    X_MIN    = 0x4
    X_MAX    = 0x8
    Y_MIN    = 0x10
    Y_MAX    = 0x20
    Z_MIN    = 0x40
    Z_MAX    = 0x80
    L_HIDDEN = 0x100
    R_HIDDEN = 0x200
    L_CAMERA = 0x400
    R_CAMERA = 0x800
    L_NOPICK = 0x1000
    R_NOPICK = 0x2000
    L_FLOOR  = 0x4000
    R_FLOOR  = 0x8000

    def parse(self, stream):
        self.flags = unpack('<H', stream.read(2))

        self.min = list(unpack('<3B', stream.read(3)))
        self.max = list(unpack('<3B', stream.read(3)))

        self.child_l, \
        self.child_r = unpack('<HH', stream.read(4))

        return self

    def write(self, stream):
        raise NotImplementedError


class GBFile(object):
    __slots__ = [
        'bounding_box_min',
        'bounding_box_max',
        'armature',
        'meshes',
        'animations',
        'transformations',
        'collision',
    ]

    _MODEL_BONE = 1

    def parse(self, stream):
        version,    \
        bone_count, \
        bone,       \
        mesh_count = unpack('<4B', stream.read(4))

        if version < 8 or version > 12:
            raise VersionError('GB version %d is unsupported' % version)

        if version >= 10:
            checksum = unpack('<I', stream.read(4))

        if version >= 12:
            name = stream.read(64) # encrypted, key 4

        option = unpack('<I', stream.read(4))[0]

        # The vertex, face, bone and keyframe counts are unused

        if version >= 9:
            vertex_count = list(unpack('<12H', stream.read(24)))
        else:
            vertex_count = list(unpack('<6H', stream.read(12)))

        face_index_count, \
        bone_index_count, \
        keyframe_count = unpack('<3H', stream.read(6))

        if version >= 9:
            _, descriptor_size, cls_size = unpack('<HII', stream.read(10))
        else:
            _, descriptor_size, cls_size = unpack('<HHH', stream.read(6))

        transformation_count, \
        animation_count = unpack('<HB', stream.read(3))

        if version >= 9:
            stream.read(1)

        material_count, \
        material_frame_count = unpack('<HH', stream.read(4))

        if not material_count:
            material_frame_count = 0

        if version >= 11:
            self.bounding_box_min = utility.read_d3dx_vector3(stream)
            self.bounding_box_max = utility.read_d3dx_vector3(stream)
        else:
            self.bounding_box_min = None
            self.bounding_box_max = None

        if version >= 9:
            stream.read(16)

        # Data

        if bone & GBFile._MODEL_BONE:
            self.armature = GBArmature().parse(stream, bone_count)
        else:
            self.armature = None

        materials = []
        for _ in range(material_count):
            materials.append(GBMaterial().parse(stream))

        self.meshes = []
        for _ in range(mesh_count):
            self.meshes.append(GBMesh().parse(stream, version))

        self.animations = []
        for i in range(animation_count):
            self.animations.append(GBAnimation().parse(stream, bone_count))

        self.transformations = []
        for i in range(transformation_count):
            self.transformations.append(GBTransformation().parse(stream))

        if cls_size:
            self.collision = GBCollision().parse(stream, version,
                    self.bounding_box_min,
                    self.bounding_box_max)
        else:
            self.collision = None

        # Parse descriptor
        descriptor = io.BytesIO(stream.read(descriptor_size))

        for anim in self.animations:
            anim.parse_descriptor(descriptor)

        for mesh in self.meshes:
            mesh.parse_descriptor(descriptor)

        for mtrl in materials:
            mtrl.parse_descriptor(descriptor, material_frame_count)

        # Replace material indexes with materials
        for mesh in self.meshes:
            mesh.material = materials[mesh.material]

        # Verify
        if stream.read(1):
            raise ValidationError('Too many bytes in GB structure')

        return self

    def write(self, stream):
        raise NotImplementedError
