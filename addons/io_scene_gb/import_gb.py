import bpy
import bmesh
import math
import os
import utility

from mathutils import Matrix, Vector, Quaternion

if 'struct_gb' in locals():
    import importlib

    importlib.reload(struct_gb)
else:
    import struct_gb


def armature_to_bstruct(self, arm):
    bpy.ops.object.mode_set(mode='EDIT')

    # Inverted permutation matrix
    p = Matrix([
        [ 0, 1, 0, 0],
        [-1, 0, 0, 0],
        [ 0, 0, 1, 0],
        [ 0, 0, 0, 1],
    ])

    for i, bone in enumerate(self.bones):
        edit = arm.edit_bones.new('bone_%03d' % i)

        if bone.parent != 0xFF:
            edit.parent = arm.edit_bones['bone_%03d' % bone.parent]

        # The Bone will be deleted otherwise
        edit.head = Vector([0, 0, 0])
        edit.tail = Vector([1, 0, 0])

        edit.matrix = Matrix(bone.matrix).inverted() * p

    bpy.ops.object.mode_set(mode='OBJECT')


def material_to_bstruct(self, path, name):
    mtrl = bpy.data.materials.new('material')
    mtrl.use_transparency = True
    mtrl.alpha = 0

    tex = bpy.data.textures.new('texture', 'IMAGE')

    # Textures are either in the tex dir, or in the common dir
    try:
        tex.image = bpy.data.images.load(
                os.path.join(path, 'tex', self.texture))

    except:
        path = utility.get_common_path(path)

        tex.image = bpy.data.images.load(
                os.path.join(path, 'tex', self.texture))

    mtex = mtrl.texture_slots.add()
    mtex.texture_coords = 'UV'
    mtex.texture = tex
    mtex.use_map_alpha = True
    mtex.alpha_factor = 1

    return mtrl


def mesh_to_bstruct(self):
    bm = bmesh.new()

    # Vertices
    for v in self.vertices:
        bm.verts.new(v['v'])

    bm.verts.index_update()
    bm.verts.ensure_lookup_table()

    # Faces
    for f in self.face_indexes:
        bm.faces.new(bm.verts[i] for i in f)

    bm.faces.index_update()
    bm.faces.ensure_lookup_table()

    # Texture coordinates
    uv_layer = bm.loops.layers.uv.verify()

    for i, f in enumerate(bm.faces):
        for j, l in enumerate(f.loops):
            v_index = self.face_indexes[i][j]

            uv = l[uv_layer].uv
            uv[0] = self.vertices[v_index]['t0'][0]
            uv[1] = self.vertices[v_index]['t0'][1]

    # Create Blender mesh
    mesh = bpy.data.meshes.new('mesh')

    bm.to_mesh(mesh)
    bm.free()

    return mesh


def to_matrix(self):
    mat_rot = Quaternion(self.rotation).to_matrix().to_4x4()

    mat_sca = Matrix([
        [self.scale[0], 0, 0],
        [0, self.scale[1], 0],
        [0, 0, self.scale[2]],
    ]).to_4x4()

    return Matrix.Translation(self.position) * mat_rot * mat_sca


struct_gb.GBTransformation.to_matrix = to_matrix


def apply_animation(self, pose_matrices, obj):
    bpy.ops.object.mode_set(mode='POSE')

    p = Matrix([
        [ 0, 1, 0, 0],
        [-1, 0, 0, 0],
        [ 0, 0, 1, 0],
        [ 0, 0, 0, 1],
    ])

    zipped = zip(
        self.keyframes,
        self.keyframe_frames,
        self.keyframe_events
    )

    for i, (keyframe, frame, event) in enumerate(zipped):
        frame = (frame / 1000) * 24

        for j, m in enumerate(keyframe):
            pose = obj.pose.bones['bone_%03d' % j]

            matrix = pose_matrices[m]

            for parent in pose.parent_recursive:
                matrix = pose_matrices[keyframe[int(parent.name[-3:])]] * matrix

            pose.matrix = matrix * p

            bpy.context.scene.update()

            pose.keyframe_insert('location', frame=frame)
            pose.keyframe_insert('rotation_quaternion', frame=frame)
            pose.keyframe_insert('scale', frame=frame)


    bpy.context.scene.frame_start = self.keyframe_frames[0] / 1000 * 24
    bpy.context.scene.frame_end = self.keyframe_frames[-1] / 1000 * 24

    bpy.ops.object.mode_set(mode='OBJECT')


struct_gb.GBAnimation.apply_animation = apply_animation

struct_gb.GBArmature.to_bstruct = armature_to_bstruct
struct_gb.GBMaterial.to_bstruct = material_to_bstruct
struct_gb.GBMesh.to_bstruct     = mesh_to_bstruct


def scene_import(context, path):
    # Fixes DirectX axes
    rot_x_pos90 = Matrix.Rotation(math.pi / 2.0, 4, 'X')

    with open(path, 'rb') as stream:
        gb = struct_gb.GBFile().parse(stream)

        name = os.path.basename(path)
        name = os.path.splitext(name)[0]
        path = os.path.dirname(path)

        scene = context.scene

        # Load meshes plus materials
        for i, mesh in enumerate(gb.meshes):
            obj = bpy.data.objects.new(
                    name + '_' + str(i), mesh.to_bstruct())

            obj.data.materials.append(
                    mesh.material.to_bstruct(path, name))

            obj.matrix_world = rot_x_pos90 * obj.matrix_world

            scene.objects.link(obj)

        # Load armature
        if gb.armature:
            arm = bpy.data.armatures.new('armature')
            obj = bpy.data.objects.new(name + '_armature', arm)

            obj.matrix_world = rot_x_pos90 * obj.matrix_world

            scene.objects.link(obj)
            scene.objects.active = obj

            gb.armature.to_bstruct(arm)

        # TODO Create separate animation action
        if gb.animations:
            pose_matrices = [m.to_matrix() for m in gb.transformations]

            gb.animations[0].apply_animation(
                    pose_matrices, bpy.context.object)


    return {'FINISHED'}
