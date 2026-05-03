import bpy
from .engine import rebuild_node_tree

class RASTER_OT_add_layer(bpy.types.Operator):
    bl_idname = "raster.add_layer"
    bl_label = "Add Layer"

    def execute(self, context):
        obj = context.active_object
        item = obj.raster_layers.add()
        item.name = f"Layer {len(obj.raster_layers)}"
        rebuild_node_tree(obj)
        return {'FINISHED'}

class RASTER_OT_remove_layer(bpy.types.Operator):
    bl_idname = "raster.remove_layer"
    bl_label = "Remove Layer"
    index: bpy.props.IntProperty()

    def execute(self, context):
        obj = context.active_object
        obj.raster_layers.remove(self.index)
        rebuild_node_tree(obj)
        return {'FINISHED'}

class RASTER_OT_move_layer(bpy.types.Operator):
    bl_idname = "raster.move_layer"
    bl_label = "Move Layer"
    direction: bpy.props.StringProperty() # 'UP' or 'DOWN'
    index: bpy.props.IntProperty()

    def execute(self, context):
        obj = context.active_object
        layers = obj.raster_layers
        new_index = self.index - 1 if self.direction == 'UP' else self.index + 1
        
        if 0 <= new_index < len(layers):
            layers.move(self.index, new_index)
            rebuild_node_tree(obj)
        return {'FINISHED'}

class RASTER_OT_sync_layers(bpy.types.Operator):
    bl_idname = "raster.sync_layers"
    bl_label = "Apply Changes"
    bl_description = "Rebuilds the node tree applying opacity and blend modes"

    def execute(self, context):
        rebuild_node_tree(context.active_object)
        return {'FINISHED'}

def register():
    bpy.utils.register_class(RASTER_OT_add_layer)
    bpy.utils.register_class(RASTER_OT_remove_layer)
    bpy.utils.register_class(RASTER_OT_move_layer)
    bpy.utils.register_class(RASTER_OT_sync_layers)

def unregister():
    bpy.utils.unregister_class(RASTER_OT_sync_layers)
    bpy.utils.unregister_class(RASTER_OT_move_layer)
    bpy.utils.unregister_class(RASTER_OT_remove_layer)
    bpy.utils.unregister_class(RASTER_OT_add_layer)