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


def add_armature(self, obj):
    bpy.context.scene.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')

    # Inverted permutation matrix
    p = Matrix([
        [ 0, 1, 0, 0],
        [-1, 0, 0, 0],
        [ 0, 0, 1, 0],
        [ 0, 0, 0, 1],
    ])

    for i, bone in enumerate(self.bones):
        edit = obj.data.edit_bones.new('Bone_%03d' % i)

        if bone.parent != 0xFF:
            edit.parent = obj.data.edit_bones['Bone_%03d' % bone.parent]

        # Prevents automatic deletion due to a length of zero
        edit.head = Vector([0, 0, 0])
        edit.tail = Vector([1, 0, 0])

        edit.matrix = Matrix(bone.matrix).inverted() * p

    bpy.ops.object.mode_set(mode='OBJECT')


def add_animation(self, obj, pose_matrices):
    bpy.context.scene.objects.active = obj
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

    for keyframe, frame, event in zipped:
        frame = (frame / 1000) * 24

        for i, m in enumerate(keyframe):
            pose = obj.pose.bones['Bone_%03d' % i]

            matrix = pose_matrices[m]

            for parent in pose.parent_recursive:
                matrix = pose_matrices[keyframe[int(parent.name[-3:])]] * matrix

            pose.matrix = matrix * p

            bpy.context.scene.update()

            pose.keyframe_insert('location', frame=frame)
            pose.keyframe_insert('rotation_quaternion', frame=frame)
            pose.keyframe_insert('scale', frame=frame)

    bpy.ops.object.mode_set(mode='OBJECT')


def add_mesh(self, obj):
    bm = bmesh.new()

    # Vertices
    for v in self.verts:
        bm.verts.new(v['v'])

    bm.verts.index_update()
    bm.verts.ensure_lookup_table()

    # Faces
    for f in self.faces:
        bm.faces.new(bm.verts[i] for i in f)

    bm.faces.index_update()
    bm.faces.ensure_lookup_table()

    # Texture coordinates
    if getattr(self, 'material', False):
        uv_layer = bm.loops.layers.uv.verify()

        for i, f in enumerate(bm.faces):
            for j, l in enumerate(f.loops):
                v_index = self.faces[i][j]

                uv = l[uv_layer].uv
                uv[0] = +self.verts[v_index]['t0'][0]
                uv[1] = -self.verts[v_index]['t0'][1]

    bm.to_mesh(obj.data)
    bm.free()


def add_groups(self, obj):
    groups = []
    for index in self.bones:
        groups.append(obj.vertex_groups.new('Bone_%03d' % index))

    for i, v in enumerate(self.verts):
        if 'weights' in v:
            weights = [w for w in v['weights'] if w != 0]

            if sum(weights) != 1:
                weights.append(1 - sum(weights))

            for index, weight in zip(v['indexes'], weights):
                groups[index].add([i], weight, 'ADD')
        else:
            for group in groups:
                group.add([i], 1.0, 'ADD')


def add_materials(self, obj, image=None):
    mat = bpy.data.materials.new('Material')
    mat.use_nodes = True

    obj.data.materials.append(mat)

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Clear existing nodes
    nodes.clear()
    links.clear()

    # Create nodes
    node_coord = nodes.new('ShaderNodeTexCoord')
    node_coord.location.x = -980
    node_coord.location.y = 0
    node_coord.object = obj

    node_mapping = nodes.new('ShaderNodeMapping')
    node_mapping.name = 'Mapping'
    node_mapping.location.x = -780
    node_mapping.location.y = 0
    node_mapping.vector_type = 'TEXTURE'
    node_mapping.translation[0] = self.material.frames[0].texture_off[0]
    node_mapping.translation[1] = self.material.frames[0].texture_off[1]
    node_mapping.rotation[0] = self.material.frames[0].texture_rot[0]
    node_mapping.rotation[1] = self.material.frames[0].texture_rot[1]
    node_mapping.rotation[2] = self.material.frames[0].texture_rot[2]

    node_image = nodes.new('ShaderNodeTexImage')
    node_image.location.x = -400
    node_image.location.y = 0
    node_image.image = image

    node_diffuse = nodes.new('ShaderNodeBsdfDiffuse')
    node_diffuse.location.x = -200
    node_diffuse.location.y = 100

    node_alpha_a = nodes.new('ShaderNodeBsdfTransparent')
    node_alpha_a.location.x = -200
    node_alpha_a.location.y = -80

    node_mixer_a = nodes.new('ShaderNodeMixShader')
    node_mixer_a.location.x = 20
    node_mixer_a.location.y = 0

    node_alpha_o = nodes.new('ShaderNodeBsdfTransparent')
    node_alpha_o.location.x = 20
    node_alpha_o.location.y = 100

    node_mixer_o = nodes.new('ShaderNodeMixShader')
    node_mixer_o.name = 'Opacity'
    node_mixer_o.location.x = 220
    node_mixer_o.location.y = 0
    node_mixer_o.inputs[0].default_value = (
            self.material.frames[0].opacity
    )

    node_output = nodes.new('ShaderNodeOutputMaterial')
    node_output.location.x = 420
    node_output.location.y = 0

    # Create links
    links.new(node_output.inputs[0], node_mixer_o.outputs[0])
    links.new(node_mixer_o.inputs[1], node_alpha_o.outputs[0])
    links.new(node_mixer_o.inputs[2], node_mixer_a.outputs[0])
    links.new(node_mixer_a.inputs[0], node_image.outputs[1])
    links.new(node_mixer_a.inputs[1], node_alpha_a.outputs[0])
    links.new(node_mixer_a.inputs[2], node_diffuse.outputs[0])
    links.new(node_diffuse.inputs[0], node_image.outputs[0])
    links.new(node_image.inputs[0], node_mapping.outputs[0])
    links.new(node_mapping.inputs[0], node_coord.outputs[2])


@property
def matrix(self):
    mat_rot = Quaternion(self.rotation).to_matrix().to_4x4()

    mat_sca = Matrix([
        [self.scale[0], 0, 0],
        [0, self.scale[1], 0],
        [0, 0, self.scale[2]],
    ]).to_4x4()

    return Matrix.Translation(self.position) * mat_rot * mat_sca


def read_image(path, name):
    # Search in the object-relative and common texture directory
    for path in [path, utility.get_common_path(path)]:
        try:
            return bpy.data.images.load(
                    os.path.join(path, 'tex', name))

        except RuntimeError:
            print('Warning: Could not open "%s".' %
                    os.path.join(path, 'tex', name))

    return None


def setup():
    """Adds custom Blender import methods to GB objects"""
    struct_gb.GBAnimation.add_animation = add_animation
    struct_gb.GBArmature.add_armature = add_armature
    struct_gb.GBTransformation.matrix = matrix
    struct_gb.GBCollision.add_mesh = add_mesh
    struct_gb.GBMesh.add_mesh = add_mesh
    struct_gb.GBMesh.add_groups = add_groups
    struct_gb.GBMesh.add_materials = add_materials


def auto_import(context, filepath, parent,
        import_dds=False,
        import_sfx=False):

    setup()

    # The cycles renderer is needed for material nodes
    bpy.context.scene.render.engine = 'CYCLES'

    # Load GB
    with open(filepath, 'rb') as stream:
        gb = struct_gb.GBFile().parse(stream)

    # Get existing or create new parent object
    if parent not in bpy.data.objects:
        parent = bpy.data.objects.new(parent, None)

        # Converts DirectX/OpenGL coordinate system difference
        parent.matrix_world = Matrix.Rotation(math.pi / 2, 4, 'X')

        context.scene.objects.link(parent)
        context.scene.objects.active = parent
    else:
        parent = bpy.data.objects[parent]

    # Get path and name without extension
    path = os.path.dirname(filepath)
    name = os.path.splitext(
            os.path.basename(filepath))[0]

    # Add armature
    if gb.armature is not None:
        dat = bpy.data.armatures.new('Armature')
        obj = bpy.data.objects.new(name + '_Armature', dat)

        context.scene.objects.link(obj)
        context.scene.objects.active = obj
        obj.parent = parent

        gb.armature.add_armature(obj)

        # Link to existing meshes
        for mesh in parent.children:
            if mesh.type == 'MESH':
                mesh.modifiers.new('Armature', 'ARMATURE').object = obj

    # Get armature object if it exists
    for armature in parent.children:
        if armature.type == 'ARMATURE':
            break
    else:
        armature = None

    # Add meshes
    for mesh in gb.meshes:
        dat = bpy.data.meshes.new('Mesh')
        obj = bpy.data.objects.new(name + '_Mesh', dat)

        context.scene.objects.link(obj)
        context.scene.objects.active = obj
        obj.parent = parent

        mesh.add_mesh(obj)
        mesh.add_groups(obj)

        if import_dds:
            image = read_image(path, mesh.material.texture.lower())
        else:
            image = None

        mesh.add_materials(obj, image)

        # Link to existing armature
        if armature is not None:
            obj.modifiers.new('Armature', 'ARMATURE').object = armature

    # Add animations
    if gb.animations:
        pose_matrices = [t.matrix for t in gb.transformations]

        if armature is None:
            print('Info: Imported animation without existing armature.')
        else:
            for animation in gb.animations:
                armature.animation_data_create()
                armature.animation_data.action = (
                        bpy.data.actions.new(name=name))

                animation.add_animation(armature, pose_matrices)

    # Add collision
    if gb.collision is not None:
        dat = bpy.data.meshes.new('Mesh')
        obj = bpy.data.objects.new(name + '_Collision', dat)

        context.scene.objects.link(obj)
        context.scene.objects.active = obj
        obj.parent = parent

        # Hide collision object
        obj.hide_render = True
        obj.hide = True

        gb.collision.add_mesh(obj)

    return {'FINISHED'}
