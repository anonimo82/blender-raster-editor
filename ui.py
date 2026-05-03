import bpy

class VIEW3D_PT_raster_layers(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Paint Layers'
    bl_label = "Layer Manager"

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        
        if not obj or not obj.active_material:
            layout.label(text="Select an object with a Material", icon='ERROR')
            return

        layout.operator("raster.add_layer", icon='ADD')
        layout.separator()

        # Draw the layer list in reverse (layer 0 at the bottom like Photoshop)
        for i in reversed(range(len(obj.raster_layers))):
            layer = obj.raster_layers[i]
            box = layout.box()
            
            row = box.row(align=True)
            row.prop(layer, "name", text="")
            
            # Up/Down Buttons
            up_btn = row.operator("raster.move_layer", text="", icon='TRIA_UP')
            up_btn.direction = 'DOWN' # Visually inverted
            up_btn.index = i
            
            down_btn = row.operator("raster.move_layer", text="", icon='TRIA_DOWN')
            down_btn.direction = 'UP' # Visually inverted
            down_btn.index = i
            
            # Remove Button
            rm_btn = row.operator("raster.remove_layer", text="", icon='X')
            rm_btn.index = i

            # Only layers from the second one upwards get blend modes and opacity
            if i > 0:
                col = box.column(align=True)
                col.prop(layer, "blend_type", text="")
                col.prop(layer, "opacity", slider=True)

        layout.separator()
        layout.operator("raster.sync_layers", icon='FILE_REFRESH', text="Apply Changes")

def register():
    bpy.utils.register_class(VIEW3D_PT_raster_layers)

def unregister():
    bpy.utils.unregister_class(VIEW3D_PT_raster_layers)