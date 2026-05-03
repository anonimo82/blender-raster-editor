import bpy

class VIEW3D_PT_raster_layers(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Paint Layers'
    bl_label = "Layer Manager"

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        
        # --- 1. SETUP CANVAS ---
        layout.operator("raster.create_canvas", icon='MESH_PLANE', text="Create Canvas")
        layout.separator()
        
        if not obj or not obj.active_material:
            layout.label(text="Select an object with a Material", icon='ERROR')
            return

        layout.operator("raster.add_layer", icon='ADD')
        layout.separator()

        # --- 2. LISTA DEI LAYER ---
        for i in reversed(range(len(obj.raster_layers))):
            layer = obj.raster_layers[i]
            box = layout.box()
            
            row = box.row(align=True)
            
            # Pulsante Layer Attivo (Icona Pennello/Radio button)
            is_active = (obj.raster_active_index == i)
            paint_icon = 'BRUSH_DATA' if is_active else 'RADIOBUT_OFF'
            active_btn = row.operator("raster.set_active_layer", text="", icon=paint_icon, depress=is_active)
            active_btn.index = i
            
            # Visibilità (Occhio)
            eye_icon = 'HIDE_OFF' if layer.is_visible else 'HIDE_ON'
            row.prop(layer, "is_visible", text="", icon=eye_icon)
            
            # Nome Layer
            row.prop(layer, "name", text="")
            
            # Spostamento Su
            up_btn = row.operator("raster.move_layer", text="", icon='TRIA_UP')
            up_btn.direction = 'DOWN' # Invertito visivamente per emulare Photoshop
            up_btn.index = i
            
            # Spostamento Giù
            down_btn = row.operator("raster.move_layer", text="", icon='TRIA_DOWN')
            down_btn.direction = 'UP' # Invertito visivamente per emulare Photoshop
            down_btn.index = i
            
            # Duplica Layer
            dup_btn = row.operator("raster.duplicate_layer", text="", icon='COPYDOWN')
            dup_btn.index = i
            
            # Rimuovi Layer
            rm_btn = row.operator("raster.remove_layer", text="", icon='X')
            rm_btn.index = i

            # Selettore Immagine
            box.prop(layer, "image", text="")

            # Opzioni di Fusione e Opacità (escluso il layer di base 0)
            if i > 0:
                col = box.column(align=True)
                col.prop(layer, "blend_type", text="")
                col.prop(layer, "opacity", slider=True)

        layout.separator()
        
        # --- 3. AZIONI GLOBALI (In fondo alla lista) ---
        row = layout.row(align=True)
        row.scale_y = 1.5 
        row.operator("raster.sync_layers", icon='FILE_REFRESH', text="Apply")
        row.operator("raster.merge_visible", icon='IMAGE_BACKGROUND', text="Merge")

        # --- 4. STRUMENTI PENNELLO AVANZATI ---
        if context.mode == 'PAINT_TEXTURE':
            layout.separator()
            layout.label(text="Paint Settings", icon='TOOL_SETTINGS')
            
            settings = context.tool_settings.image_paint
            layout.template_ID(settings, "brush", new="brush.add")
            
            brush = settings.brush
            if brush:
                box = layout.box()
                col = box.column(align=True)
                
                # Selettore Colore (Funziona sia per Pennello che per Secchiello)
                col.prop(brush, "color", text="Color")
                col.separator()
                
                col.prop(brush, "size", text="Radius")
                col.prop(brush, "strength", slider=True)
                
                col.separator()
                col.prop(brush, "blend", text="Mode") 
                
                # Nascondiamo lo Stroke Method se stiamo usando il secchiello
                if hasattr(brush, "image_tool") and brush.image_tool == 'DRAW':
                    col.prop(brush, "stroke_method", text="Stroke")
                
                # Mostra la texture collegata al pennello
                if brush.texture:
                    col.separator()
                    col.label(text=f"Texture: {brush.texture.name}", icon='TEXTURE')

def register():
    bpy.utils.register_class(VIEW3D_PT_raster_layers)

def unregister():
    bpy.utils.unregister_class(VIEW3D_PT_raster_layers)