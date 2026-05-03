bl_info = {
    "name": "Blender Raster Editor",
    "author": "Gemini & User",
    "version": (1, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Paint Layers",
    "description": "Non-destructive layer system for hand-painting and rotoscoping",
    "category": "Paint",
}

import bpy
from . import properties, engine, operators, ui

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