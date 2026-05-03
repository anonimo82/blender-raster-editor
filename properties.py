import bpy

class RasterLayerItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Name", default="New Layer")
    opacity: bpy.props.FloatProperty(name="Opacity", default=1.0, min=0.0, max=1.0)
    blend_type: bpy.props.EnumProperty(
        name="Blend Mode",
        items=[
            ('MIX', "Mix", ""), 
            ('MULTIPLY', "Multiply", ""),
            ('SCREEN', "Screen", ""), 
            ('OVERLAY', "Overlay", ""),
            ('ADD', "Add", "")
        ],
        default='MIX'
    )
    # Internal reference to the Node Group dedicated to this layer
    group_name: bpy.props.StringProperty()

def register():
    bpy.utils.register_class(RasterLayerItem)
    bpy.types.Object.raster_layers = bpy.props.CollectionProperty(type=RasterLayerItem)

def unregister():
    del bpy.types.Object.raster_layers
    bpy.utils.unregister_class(RasterLayerItem)