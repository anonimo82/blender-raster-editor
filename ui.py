import bpy

class VIEW3D_PT_raster_layers(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Paint Layers'
    bl_label = "Layer Manager"

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        
        layout.operator("raster.create_canvas", icon='MESH_PLANE', text="Create Canvas")
        layout.separator()
        
        if not obj or not obj.active_material:
            layout.label(text="Select an object with a Material", icon='ERROR')
            return

        layout.operator("raster.add_layer", icon='ADD')
        layout.separator()

        for i in reversed(range(len(obj.raster_layers))):
            layer = obj.raster_layers[i]
            box = layout.box()
            
            row = box.row(align=True)
            
            is_active_main = (obj.raster_active_index == i and not obj.raster_active_is_mask)
            paint_icon = 'BRUSH_DATA' if is_active_main else 'RADIOBUT_OFF'
            btn_main = row.operator("raster.set_active_layer", text="", icon=paint_icon, depress=is_active_main)
            btn_main.index = i
            btn_main.is_mask = False
            
            eye_icon = 'HIDE_OFF' if layer.is_visible else 'HIDE_ON'
            row.prop(layer, "is_visible", text="", icon=eye_icon)
            
            row.prop(layer, "name", text="")
            
            up_btn = row.operator("raster.move_layer", text="", icon='TRIA_UP'); up_btn.direction = 'DOWN'; up_btn.index = i
            dn_btn = row.operator("raster.move_layer", text="", icon='TRIA_DOWN'); dn_btn.direction = 'UP'; dn_btn.index = i
            dup_btn = row.operator("raster.duplicate_layer", text="", icon='COPYDOWN'); dup_btn.index = i
            rm_btn = row.operator("raster.remove_layer", text="", icon='X'); rm_btn.index = i

            box.template_ID(layer, "image", new="image.new", open="image.open")

            mask_row = box.row(align=True)
            if layer.mask_image:
                is_active_mask = (obj.raster_active_index == i and obj.raster_active_is_mask)
                mask_icon = 'BRUSH_DATA' if is_active_mask else 'RADIOBUT_OFF'
                btn_mask = mask_row.operator("raster.set_active_layer", text="", icon=mask_icon, depress=is_active_mask)
                btn_mask.index = i
                btn_mask.is_mask = True
                
                mask_row.prop(layer, "use_mask", text="", icon='MOD_MASK')
                mask_row.template_ID(layer, "mask_image", new="image.new", open="image.open")
                
                rm_mask_btn = mask_row.operator("raster.remove_mask", text="", icon='X')
                rm_mask_btn.index = i
            else:
                mask_row.label(text="", icon='BLANK1')
                add_mask_btn = mask_row.operator("raster.create_mask", text="Add Mask", icon='MOD_MASK')
                add_mask_btn.index = i

            if i > 0:
                col = box.column(align=True)
                col.prop(layer, "blend_type", text="")
                col.prop(layer, "opacity", slider=True)

        layout.separator()
        
        box_utils = layout.box()
        col = box_utils.column(align=True)
        col.scale_y = 1.2
        col.operator("raster.sync_layers", icon='FILE_REFRESH', text="Apply Opacity")
        
        row = col.row(align=True)
        row.operator("raster.merge_visible", icon='IMAGE_BACKGROUND', text="Merge")
        row.operator("raster.resize_canvas", icon='FULLSCREEN_ENTER', text="Resize Canvas")
        
        col.operator("raster.setup_camera", icon='OUTLINER_OB_CAMERA', text="Frame Camera")

        if context.mode == 'PAINT_TEXTURE':
            layout.separator()
            layout.label(text="Paint Settings", icon='TOOL_SETTINGS')
            settings = context.tool_settings.image_paint
            layout.template_ID(settings, "brush", new="brush.add")
            
            brush = settings.brush
            if brush:
                box = layout.box()
                col = box.column(align=True)
                col.prop(brush, "color", text="Color")
                col.separator()
                col.prop(brush, "size", text="Radius")
                col.prop(brush, "strength", slider=True)
                col.separator()
                col.prop(brush, "blend", text="Mode") 

def register():
    bpy.utils.register_class(VIEW3D_PT_raster_layers)

def unregister():
    bpy.utils.unregister_class(VIEW3D_PT_raster_layers)