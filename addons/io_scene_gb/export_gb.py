import bpy
import utility

if 'struct_gb' in locals():
    import importlib

    importlib.reload(struct_gb)
else:
    import struct_gb


def scene_export(context, filepath):
    raise NotImplementedError
