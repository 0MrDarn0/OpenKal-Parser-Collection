import bpy
import bmesh
import math
import mathutils
import os

import struct_gb
import utility


def to_bstruct(self, path, name):
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


struct_gb.GBMesh.to_bstruct = to_bstruct


def scene_import(context, path):
    rot_x_pos90 = mathutils.Matrix.Rotation(math.pi / 2.0, 4, 'X')

    with open(path, 'rb') as stream:
        gb = struct_gb.GBFile().parse(stream)

        name = os.path.basename(path)
        name = os.path.splitext(name)[0]
        path = os.path.dirname(path)

        scene = context.scene

        for i, mesh in enumerate(gb.meshes):
            obj = bpy.data.objects.new(name + '_' + str(i),
                    mesh.to_bstruct(path, name))

            obj.matrix_world = rot_x_pos90 * obj.matrix_world

            scene.objects.link(obj)

    return {'FINISHED'}
