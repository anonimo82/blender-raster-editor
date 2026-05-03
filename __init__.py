bl_info = {
    "name": "Raster Layer Engine",
    "author": "Gemini",
    "version": (1, 0),
    "blender": (3, 4, 0),
    "location": "View3D > Sidebar (N) > Paint Layers",
    "description": "Non-destructive raster layer compositing engine",
    "category": "Paint",
}

import bpy
from . import properties
from . import operators
from . import ui

def register():
    properties.register()
    operators.register()
    ui.register()

def unregister():
    ui.unregister()
    operators.unregister()
    properties.unregister()

if __name__ == "__main__":
    register()