import bpy
from .engine import rebuild_node_tree

def auto_update_tree(self, context):
    if context.active_object:
        rebuild_node_tree(context.active_object)

class RasterLayerItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Name", default="New Layer")
    image: bpy.props.PointerProperty(
        name="Image", 
        type=bpy.types.Image,
        description="The image or texture of this layer",
        update=auto_update_tree
    )
    is_visible: bpy.props.BoolProperty(
        name="Visible", 
        default=True,
        description="Hide/Show the layer",
        update=auto_update_tree
    )
    blend_type: bpy.props.EnumProperty(
        name="Blend Mode",
        items=[
            ('MIX', "Mix", ""), 
            ('MULTIPLY', "Multiply", ""),
            ('SCREEN', "Screen", ""), 
            ('OVERLAY', "Overlay", ""),
            ('ADD', "Add", "")
        ],
        default='MIX',
        update=auto_update_tree
    )
    opacity: bpy.props.FloatProperty(name="Opacity", default=1.0, min=0.0, max=1.0)
    group_name: bpy.props.StringProperty()


class RASTER_OT_set_active_layer(bpy.types.Operator):
    bl_idname = "raster.set_active_layer"
    bl_label = "Set Active Layer"
    bl_description = "Seleziona questo layer per dipingerci sopra"
    index: bpy.props.IntProperty()

    def execute(self, context):
        obj = context.active_object
        obj.raster_active_index = self.index
        # Ricostruiamo l'albero per forzare la selezione dei nodi corretti
        rebuild_node_tree(obj)
        return {'FINISHED'}

def register():
    bpy.utils.register_class(RasterLayerItem)
    bpy.types.Object.raster_layers = bpy.props.CollectionProperty(type=RasterLayerItem)
    # --- NUOVA PROPRIETÀ: Salva l'indice del layer su cui stiamo dipingendo ---
    bpy.types.Object.raster_active_index = bpy.props.IntProperty(default=0)
    bpy.utils.register_class(RASTER_OT_set_active_layer)

def unregister():
    bpy.utils.unregister_class(RASTER_OT_set_active_layer)
    del bpy.types.Object.raster_active_index
    del bpy.types.Object.raster_layers
    bpy.utils.unregister_class(RasterLayerItem)