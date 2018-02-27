#!/usr/bin/python3.5

import io
import sys
import utility

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
        'parent',
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
            self.keyframes.append(list(
                unpack('<%dH' % b_count, stream.read(2 * b_count))))

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
        'texture_off',
        'texture_rot',
        'options',
        'light_a',
        'light_d',
        'light_s',
        'opacity',
    ]

    _OPTION_TWOSIDED      = 1
    _OPTION_MAP_OPACITY   = 2
    _OPTION_MAP_ALPHA_RGB = 4
    _OPTION_SPECULAR      = 8
    _OPTION_LIGHT         = 32
    _OPTION_LIGHTMAP      = 256
    _OPTION_FX            = 512

    def parse_descriptor(self, descriptor):
        self.texture = utility.read_string_zero(descriptor, self.texture)

        descriptor.seek(self.light_a)
        self.light_a = utility.read_d3d_color(descriptor) # ambient
        self.light_d = utility.read_d3d_color(descriptor) # diffuse
        self.light_s = utility.read_d3d_color(descriptor) # specular
        self.opacity = unpack('<f', descriptor.read(4))[0]

        self.texture_off = utility.read_d3dx_vector2(descriptor)
        self.texture_rot = utility.read_d3dx_vector3(descriptor)

        if not self.texture_off.any():
            self.texture_off = None

        if not self.texture_rot.any():
            self.texture_rot = None

    def write_descriptor(self, descriptor):
        raise NotImplementedError

    def parse(self, stream):
        # Texture, option and light_a are descriptor indexes
        # _ (1) = option
        # _ (2) = power

        self.texture, \
        self.options, \
        _,            \
        _,            \
        self.light_a = unpack('<IHIfI', stream.read(18))

        return self

    def write(self, stream):
        raise NotImplementedError


class GBMesh(object):
    __slots__ = [
        'name',
        'material',
        'vertices',
        'bone_indexes',
        'face_indexes',
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

    def _correct(self, indexes):
        result = []
        for a, b, c in zip(*[iter(indexes)] * 3):
            if a == b or a == c or b == c:
                continue

            result.append((a, b, c))

        return result

    def _unstrip(self, indexes):
        """Converts an index strip to a index list."""
        result = []
        for i in range(len(indexes) - 2):
            if i & 1:
                result.extend([indexes[i], indexes[i + 1], indexes[i + 2]])
            else:
                result.extend([indexes[i], indexes[i + 2], indexes[i + 1]])

        return result

    def _parse_vertex(self, stream, v_type):
        vertex = {'v' : utility.read_d3dx_vector3(stream)}

        # See: Direct3D 9 - Indexed Vertex Blending
        if v_type >= 1 and v_type <= 4:
            vertex['indexes'] = unpack('<I', stream.read(4))

        if v_type == 2:
            vertex['blend'] = list(unpack('<1f', stream.read(4)))
        elif v_type == 3:
            vertex['blend'] = list(unpack('<2f', stream.read(8)))
        elif v_type == 4:
            vertex['blend'] = list(unpack('<3f', stream.read(12)))

        # Texture coordinate(s) and vertex normal
        vertex['vn'] = utility.read_d3dx_vector3(stream)
        vertex['t0'] = utility.read_d3dx_vector2(stream)

        # Flip v-coordinate
        vertex['t0'][1] = -vertex['t0'][1]

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

        self.vertices = []
        self.bone_indexes = []
        self.face_indexes = []

        for _ in range(b_count):
            self.bone_indexes.append(unpack('<B', stream.read(1))[0])

        for _ in range(v_count):
            self.vertices.append(self._parse_vertex(stream, v_type))

        for _ in range(f_count):
            self.face_indexes.append(unpack('<H', stream.read(2))[0])

        # _FT_STRIP and _FT_END must be unstripped, correction is optional
        if f_type:
            self.face_indexes = self._unstrip(self.face_indexes)
            self.face_indexes = self._correct(self.face_indexes)
        else:
            self.face_indexes = self._correct(self.face_indexes)

        return self

    def write(self, stream, gb_version):
        raise NotImplementedError


class GBCollisionMesh(object):
    __slots__ = [
        'minimum',
        'maximum',
        'vertices',
        'face_indexes',
    ]

    def parse(self, stream):
        v_count, \
        f_count = unpack('<HH', stream.read(4))

        self.minimum = utility.read_d3dx_vector3(stream)
        self.maximum = utility.read_d3dx_vector3(stream)

        self.vertices = []
        for _ in range(v_count):
            self.vertices.append(list(unpack('<3H', stream.read(6))))

        self.face_indexes = []
        for _ in range(f_count):
            self.face_indexes.append(list(unpack('<3H', stream.read(6))))

        # Discard OctTree
        stream.read((f_count - 1) * 12)

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
        'collision_mesh',
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
        material_count_frame = unpack('<HH', stream.read(4))

        if version >= 11:
            self.bounding_box_min = utility.read_d3dx_vector3(stream)
            self.bounding_box_max = utility.read_d3dx_vector3(stream)

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

        self.animations =  []
        for i in range(animation_count):
            self.animations.append(GBAnimation().parse(stream, bone_count))

        self.transformations = []
        for i in range(transformation_count):
            self.transformations.append(GBTransformation().parse(stream))

        if cls_size:
            self.collision_mesh = GBCollisionMesh().parse(stream)

        # Parse descriptor
        descriptor = io.BytesIO(stream.read(descriptor_size))

        for anim in self.animations:
            anim.parse_descriptor(descriptor)

        for mesh in self.meshes:
            mesh.parse_descriptor(descriptor)

        for mtrl in materials:
            mtrl.parse_descriptor(descriptor)

        # Replace material indexes with materials
        for mesh in self.meshes:
            mesh.material = materials[mesh.material]

        # Verify
        if stream.read(1):
            raise ValidationError('Too many bytes in GB structure')

        return self

    def write(self, stream):
        raise NotImplementedError


def main(path):
    with open(path, 'rb') as stream:
        try:
            gb = GBFile().parse(stream)

        except (VersionError, ValidationError) as e:
            print(str(e) + ' in ' + path)


# Usage: python struct_gb.py path; performs a parse check, nothing else
if __name__ == '__main__':
    main(sys.argv[1])
