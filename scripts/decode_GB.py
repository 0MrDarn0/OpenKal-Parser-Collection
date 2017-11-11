import sys
import utility
import pyassimp
import ctypes

from struct import unpack

class GBBone:
    def __init__(self, stream):
        self.matrix = utility.read_d3dx_matrix4(stream)
        self.parent = unpack('<B', stream.read(1))


class GBMaterialKey:
    def __init__(self, stream):
        self.texture,   \
        self.mapoption, \
        self.option,    \
        self.power,     \
        self.frame = unpack('<IHIfI', stream.read(18))


class GBMesh:
    __FT_LIST = 0

    def __init__(self, stream, version):
        # Header

        self.name,             \
        self.material_ref,     \
        self.vertex_type,      \
        self.face_type,        \
        self.vertex_count,     \
        self.face_index_count, \
        self.bone_index_count = unpack('<IiBBHHB', stream.read(15))

        if version < 11 and self.vertex_type > 0:
            self.vertex_type -= 1

        # Data

        self.vertices = []
        self.bone_indexes = []
        self.face_indexes = []

        for _ in range(self.bone_index_count):
            self.bone_indexes.append(unpack('<B', stream.read(1)))

        for _ in range(self.vertex_count):
            vertex = {'v' : utility.read_d3dx_vector3(stream)}

            if self.vertex_type >= 1 and self.vertex_type <= 4:
                vertex['indices'] = unpack('<I', stream.read(4))

            if self.vertex_type == 2:
                vertex['blend'] = list(unpack('<1f', stream.read(4)))
            elif self.vertex_type == 3:
                vertex['blend'] = list(unpack('<2f', stream.read(8)))
            elif self.vertex_type == 4:
                vertex['blend'] = list(unpack('<3f', stream.read(12)))

            vertex['n'] = utility.read_d3dx_vector3(stream)
            vertex['t'] = utility.read_d3dx_vector2(stream)

            if self.vertex_type >= 5:
                vertex['t'] = utility.read_d3dx_vector2(stream)

            self.vertices.append(vertex)

        for _ in range(self.face_index_count):
            self.face_indexes.append(unpack('<H', stream.read(2))[0])

# Encodes GB_ANIM_HEADER and GB_KEYFRAME
class GBAnimFile:
    def __init__(self, stream, bone_count):
        self.option, self.keyframe_count = unpack('<IH', stream.read(6))

        self.keyframes = []
        for _ in range(keyframe_count):
            keyframe = {
                'time'   : unpack('<H', stream.read(2))[0],
                'option' : unpack('<I', stream.read(4))[0]
            }

            self.keyframes.append(keyframe)

        self.animation_indexes = []
        for _ in range(keyframe_count):
            for _ in range(bone_count):
                self.animations.append(unpack('<H', stream.read(2)))


class GBAnim:
    def __init__(self, stream):
        self.position = utility.read_d3dx_vector3(stream)
        self.rotation = utility.read_d3dx_vector4(stream)
        self.scale = utility.read_d3dx_vector3(stream)


class GBCollisionMesh:
    def __init__(self, stream):
        self.vertex_count, self.face_count = unpack('<HH', stream.read(4))

        self.minimum = utility.read_d3dx_vector3(stream)
        self.maximum = utility.read_d3dx_vector3(stream)

        self.vertices = []
        for _ in range(self.vertex_count):
            self.vertices.append(list(unpack('<3H', stream.read(6))))

        self.faces = []
        for _ in range(self.face_count):
            self.faces.append(list(unpack('<3H', stream.read(6))))

        # Discard OctTree
        stream.read((self.face_count - 1) * 12)


class GBFile:

    __MODEL_BONE = 1


    def __init__(self, stream):
        # Header

        self.version,    \
        self.bone_count, \
        self.bone,       \
        self.mesh_count = unpack('<4B', stream.read(4))

        if self.version >= 10:
            self.checksum = unpack('<I', stream.read(4))

        if self.version >= 12:
            self.name = utility.read_string_var(stream, 64) # encrypted, key 4

        self.option = unpack('<I', stream.read(4))[0]

        if self.version >= 9:
            self.vertex_count = list(unpack('<12H', stream.read(24)))
        else:
            self.vertex_count = list(unpack('<6H', stream.read(12)))

        self.index_count,      \
        self.index_count_bone, \
        self.keyframe_count = unpack('<3H', stream.read(6))

        if self.version >= 9:
            _, self.string_size, self.cls_size = unpack('<HII', stream.read(10))
        else:
            _, self.string_size, self.cls_size = unpack('<HHH', stream.read(6))

        self.anim_count, \
        self.anim_count_file = unpack('<HB', stream.read(3))

        if self.version >= 9:
            stream.read(1)

        self.material_count, \
        self.material_count_frame = unpack('<HH', stream.read(4))

        if self.version >= 11:
            self.bounding_box_min = utility.read_d3dx_vector3(stream)
            self.bounding_box_max = utility.read_d3dx_vector3(stream)

        if self.version >= 9:
            stream.read(16)

        # Data

        if self.bone & GBFile.__MODEL_BONE:
            self.bones = []

            for _ in range(self.bone_count):
                self.bones.append(GBBone(stream))

        self.materials_keys = []
        for _ in range(self.material_count):
            self.materials_keys.append(GBMaterialKey(stream))

        self.meshes = []
        for _ in range(self.mesh_count):
            self.meshes.append(GBMesh(stream, self.version))

        self.anim_files = []
        for _ in range(self.anim_count_file):
            self.anim_files.append(GBAnimFile(stream, self.bone_count))

        self.anim = []
        for _ in range(self.anim_count):
            self.anim.append(GBAnim(stream))

        if self.cls_size:
            self.collision_mesh = GBCollisionMesh(stream)

        self.string = utility.read_string_var(stream, self.string_size)

        # Verify
        if stream.read(1):
            sys.exit('Unable to parse GB, too many bytes')


def main(path):
    with open(path, 'rb') as stream:
        gb = GBFile(stream)

# Usage: python decode_GB.py path
if __name__ == '__main__':
    main(sys.argv[1])
