import bpy

def auto_update_tree(self, context):
    if context.active_object:
        from .engine import rebuild_node_tree
        rebuild_node_tree(context.active_object)

class RasterLayerItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Name", default="New Layer")
    
    image: bpy.props.PointerProperty(
        name="Image", 
        type=bpy.types.Image,
        update=auto_update_tree
    )
    
    # Masks
    mask_image: bpy.props.PointerProperty(
        name="Mask", 
        type=bpy.types.Image,
        update=auto_update_tree
    )
    use_mask: bpy.props.BoolProperty(
        name="Enable Mask", 
        default=True,
        update=auto_update_tree
    )
    
    is_visible: bpy.props.BoolProperty(
        name="Visible", 
        default=True,
        update=auto_update_tree
    )
    
    blend_type: bpy.props.EnumProperty(
        name="Blend Mode",
        items=[
            ('MIX', "Mix", ""), 
            ('DARKEN', "Darken", ""), 
            ('MULTIPLY', "Multiply", ""),
            ('BURN', "Color Burn", ""), 
            ('LIGHTEN', "Lighten", ""), 
            ('SCREEN', "Screen", ""),
            ('DODGE', "Color Dodge", ""), 
            ('ADD', "Add", ""), 
            ('OVERLAY', "Overlay", ""),
            ('SOFT_LIGHT', "Soft Light", ""), 
            ('LINEAR_LIGHT', "Linear Light", ""), 
            ('DIFFERENCE', "Difference", ""),
            ('EXCLUSION', "Exclusion", ""), 
            ('SUBTRACT', "Subtract", ""), 
            ('DIVIDE', "Divide", ""),
            ('HUE', "Hue", ""), 
            ('SATURATION', "Saturation", ""), 
            ('COLOR', "Color", ""), 
            ('VALUE', "Value", "")
        ],
        default='MIX',
        update=auto_update_tree
    )
    
    opacity: bpy.props.FloatProperty(name="Opacity", default=1.0, min=0.0, max=1.0)
    group_name: bpy.props.StringProperty()

def register():
    bpy.utils.register_class(RasterLayerItem)
    bpy.types.Object.raster_layers = bpy.props.CollectionProperty(type=RasterLayerItem)
    bpy.types.Object.raster_active_index = bpy.props.IntProperty(default=0)
    bpy.types.Object.raster_active_is_mask = bpy.props.BoolProperty(default=False)

def unregister():
    del bpy.types.Object.raster_active_is_mask
    del bpy.types.Object.raster_active_index
    del bpy.types.Object.raster_layers
    bpy.utils.unregister_class(RasterLayerItem)