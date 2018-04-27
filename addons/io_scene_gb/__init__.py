bl_info = {
    'name' : 'OpenKal GB Format', 'category': 'Import-Export',
}


if 'bpy' in locals():
    import importlib

    if 'import_gb' in locals():
        importlib.reload(import_gb)

    if 'export_gb' in locals():
        importlib.reload(export_gb)


import bpy

from . import import_gb
from . import export_gb

from bpy_extras.io_utils import ImportHelper
from bpy_extras.io_utils import ExportHelper


class ImportGB(bpy.types.Operator, ImportHelper):
    """Import a KalOnline GB file"""
    bl_idname = 'openkal.import_gb'
    bl_label  = 'Import GB'

    parent = bpy.props.StringProperty(
        name='Object Name', default='Untitled',
    )

    import_dds = bpy.props.BoolProperty(name='Import DDS')
    import_sfx = bpy.props.BoolProperty(name='Import SFX', options={'HIDDEN'})

    filename_ext = '.gb'
    filter_glob = bpy.props.StringProperty(
        default='*.gb', options={'HIDDEN'},
    )

    def execute(self, context):
        return import_gb.auto_import(context,
                **self.as_keywords(ignore=('filter_glob',)))


class ExportGB(bpy.types.Operator, ExportHelper):
    """Export a KalOnline GB file"""
    bl_idname = 'openkal.export_gb'
    bl_label  = 'Export GB'

    filename_ext = '.gb'
    filter_glob = bpy.props.StringProperty(
        default='*.gb', options={'HIDDEN'},
    )

    def execute(self, context):
        return export_gb.auto_export(context,
                **self.as_keywords(ignore=('filter_glob',)))


def menu_func_import(self, context):
    self.layout.operator(ImportGB.bl_idname, text='OpenKal Geometry (.gb)')


def menu_func_export(self, context):
    self.layout.operator(ExportGB.bl_idname, text='OpenKal Geometry (.gb)')


classes = (
    ImportGB,
    ExportGB,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.INFO_MT_file_import.append(menu_func_import)
    bpy.types.INFO_MT_file_export.append(menu_func_export)


def unregister():
    bpy.types.INFO_MT_file_import.remove(menu_func_import)
    bpy.types.INFO_MT_file_export.remove(menu_func_export)

    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == '__main__':
    register()
