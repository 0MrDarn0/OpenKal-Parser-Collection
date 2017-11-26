import bpy
import bmesh
import math
import mathutils

import struct_gb
import utility

def create_mesh(gb, mesh, mesh_name):
    bm = bmesh.new()

    # Vertices
    for v in mesh.vertices:
        bm.verts.new(v['v'])

    bm.verts.index_update()
    bm.verts.ensure_lookup_table()

    # Faces
    for f in mesh.face_indexes:
        bm.faces.new(bm.verts[i] for i in f)

    bm.faces.index_update()
    bm.faces.ensure_lookup_table()

    # Texture coordinates
    uv_layer = bm.loops.layers.uv.verify()

    for i, f in enumerate(bm.faces):
        for j, l in enumerate(f.loops):
            v_index = mesh.face_indexes[i][j]

            uv = l[uv_layer].uv
            uv[0] = mesh.vertices[v_index]['t0'][0]
            uv[1] = mesh.vertices[v_index]['t0'][1]

    # Create Blender mesh
    mesh = bpy.data.meshes.new(mesh_name)

    bm.to_mesh(mesh)
    bm.free()

    return mesh


def create_objects(gb):
    result = []

    for i, mesh in enumerate(gb.meshes):
        i = str(i)

        result.append(bpy.data.objects.new('object_' + i,
                create_mesh(gb, mesh, 'mesh_' + i)))

    return result

def parse(context, stream):
    gb = struct_gb.GBFile().parse(stream)

    rot_x_pos90 = mathutils.Matrix.Rotation(math.pi/2.0, 4, 'X')

    scene = context.scene

    for obj in create_objects(gb):
        obj.matrix_world = rot_x_pos90 * obj.matrix_world

        scene.objects.link(obj)

    scene.update()


    return {'FINISHED'}
