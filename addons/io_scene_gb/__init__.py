bl_info = {
    "name" : "OpenKal GB Format", "category": "Import-Export",
}


if "bpy" in locals():
    import importlib

    if "import_gb" in locals():
        importlib.reload(import_gb)

    if "export_gb" in locals():
        importlib.reload(export_gb)


import bpy

from . import import_gb
from . import export_gb

from bpy_extras.io_utils import ImportHelper
from bpy_extras.io_utils import ExportHelper


class ImportGB(bpy.types.Operator, ImportHelper):
    bl_idname = "openkal.import_gb"
    bl_label  = "Import GB"

    filter_glob = bpy.props.StringProperty(
        default = "*.gb",
    )

    filename_ext = ".gb"

    def execute(self, context):
        path = self.properties.filepath

        with open(path, 'rb') as stream:
            return import_gb.parse(context, stream)


class ExportGB(bpy.types.Operator, ExportHelper):
    bl_idname = "openkal.export_gb"
    bl_label  = "Export GB"

    filter_glob = bpy.props.StringProperty(
        default = "*.gb",
    )

    filename_ext = ".gb"

    def execute(self, context):
        path = self.properties.filepath

        with open(path, 'wb') as stream:
            return export_gb.write(context, stream)


def menu_func_import(self, context):
    self.layout.operator(ImportGB.bl_idname, text="OpenKal Geometry (.gb)")


def menu_func_export(self, context):
    self.layout.operator(ExportGB.bl_idname, text="OpenKal Geometry (.gb)")


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


if __name__ == "__main__":
    register()
