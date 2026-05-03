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

class RASTER_OT_create_canvas(bpy.types.Operator):
    bl_idname = "raster.create_canvas"
    bl_label = "Create Canvas"
    bl_description = "Genera un piano, gli assegna il materiale e imposta la vista su Material Preview"

    def execute(self, context):
        # 1. Salva il materiale corrente (se esiste)
        current_mat = None
        if context.active_object and context.active_object.active_material:
            current_mat = context.active_object.active_material

        # 2. Crea il piano (la tela)
        bpy.ops.mesh.primitive_plane_add(size=2, enter_editmode=False, align='WORLD', location=(0, 0, 0))
        canvas = context.active_object
        canvas.name = "Raster_Canvas"

        # 3. Assegna il materiale
        if current_mat:
            canvas.data.materials.append(current_mat)
        else:
            # Se non c'è materiale, creane uno nuovo pronto per i nodi
            new_mat = bpy.data.materials.new(name="Raster_Material")
            new_mat.use_nodes = True
            canvas.data.materials.append(new_mat)

        # 4. Imposta la vista 3D su 'MATERIAL' (Material Preview)
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.shading.type = 'MATERIAL'

        return {'FINISHED'}

class RASTER_OT_merge_visible(bpy.types.Operator):
    bl_idname = "raster.merge_visible"
    bl_label = "Merge Visible"
    bl_description = "Bake visible layers into a new single raster image"
    bl_options = {'REGISTER', 'UNDO'}

    # Proprietà per scegliere la risoluzione nel popup
    resolution: bpy.props.IntProperty(
        name="Resolution", 
        default=1024, 
        min=256, 
        max=4096,
        description="Risoluzione della nuova immagine fusa"
    )

    def invoke(self, context, event):
        # Mostra un popup prima di eseguire il codice
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        obj = context.active_object
        if not obj or not obj.active_material:
            self.report({'ERROR'}, "No active object/material.")
            return {'CANCELLED'}

        # 1. Sincronizziamo i nodi prima di cuocere per sicurezza
        rebuild_node_tree(obj)

        mat = obj.active_material
        nodes = mat.node_tree.nodes

        visible_layers = [l for l in obj.raster_layers if l.is_visible]
        if len(visible_layers) <= 1:
            self.report({'WARNING'}, "At least 2 visible layers are needed to merge.")
            return {'CANCELLED'}

        # 2. Setup temporaneo del Render Engine per il Bake
        orig_engine = context.scene.render.engine
        context.scene.render.engine = 'CYCLES'
        
        # Estraiamo solo il Colore Base ignorando luci e ombre
        context.scene.cycles.bake_type = 'DIFFUSE'
        context.scene.render.bake.use_pass_direct = False
        context.scene.render.bake.use_pass_indirect = False
        context.scene.render.bake.use_pass_color = True
        
        # 3. Creazione della nuova Immagine
        img_name = f"Merged_Canvas_{len(bpy.data.images)}"
        merged_img = bpy.data.images.new(name=img_name, width=self.resolution, height=self.resolution)
        
        # 4. Nodo Target per il Bake
        # Blender ha bisogno di un nodo immagine "Selezionato e Attivo" per sapere dove salvare il bake
        bake_node = nodes.new('ShaderNodeTexImage')
        bake_node.image = merged_img
        bake_node.select = True
        nodes.active = bake_node

        # Assicuriamoci che l'oggetto corretto sia selezionato nel Viewport
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        context.view_layer.objects.active = obj

        # 5. Eseguiamo il Bake!
        try:
            bpy.ops.object.bake(type='DIFFUSE', save_mode='INTERNAL')
        except Exception as e:
            self.report({'ERROR'}, f"Bake failed: {e}")
            nodes.remove(bake_node)
            context.scene.render.engine = orig_engine
            return {'CANCELLED'}

        # 6. Pulizia e Ripristino Engine
        nodes.remove(bake_node)
        context.scene.render.engine = orig_engine

        # 7. Logica dei Layer: Nascondi i vecchi, crea il nuovo in cima
        for layer in visible_layers:
            layer.is_visible = False
            
        new_layer = obj.raster_layers.add()
        new_layer.name = "Merged Layer"
        new_layer.image = merged_img
        new_layer.is_visible = True
        new_layer.opacity = 1.0
        new_layer.blend_type = 'MIX'
        
        rebuild_node_tree(obj)
        self.report({'INFO'}, "Layers successfully merged!")
        
        return {'FINISHED'}

class RASTER_OT_duplicate_layer(bpy.types.Operator):
    bl_idname = "raster.duplicate_layer"
    bl_label = "Duplicate Layer"
    index: bpy.props.IntProperty()

    def execute(self, context):
        obj = context.active_object
        layers = obj.raster_layers
        src_layer = layers[self.index]
        
        # 1. Crea il nuovo layer in fondo alla lista
        new_layer = layers.add()
        new_layer.name = src_layer.name + " Copy"
        new_layer.image = src_layer.image
        new_layer.is_visible = src_layer.is_visible
        new_layer.opacity = src_layer.opacity
        new_layer.blend_type = src_layer.blend_type
        # Lasciamo intenzionalmente group_name vuoto per fargli generare un nodo indipendente
        
        # 2. Sposta il nuovo layer appena sopra quello originale
        # L'ultimo elemento ha indice len(layers) - 1. Lo spostiamo a self.index + 1
        new_index = self.index + 1
        layers.move(len(layers) - 1, new_index)
        
        # 3. Ricostruisci i nodi
        rebuild_node_tree(obj)
        return {'FINISHED'}

def register():
    bpy.utils.register_class(RASTER_OT_add_layer)
    bpy.utils.register_class(RASTER_OT_remove_layer)
    bpy.utils.register_class(RASTER_OT_move_layer)
    bpy.utils.register_class(RASTER_OT_sync_layers)
    bpy.utils.register_class(RASTER_OT_create_canvas)
    bpy.utils.register_class(RASTER_OT_merge_visible)
    bpy.utils.register_class(RASTER_OT_duplicate_layer) # <-- Aggiunto

def unregister():
    bpy.utils.unregister_class(RASTER_OT_duplicate_layer) # <-- Aggiunto
    bpy.utils.unregister_class(RASTER_OT_merge_visible)
    bpy.utils.unregister_class(RASTER_OT_create_canvas)
    bpy.utils.unregister_class(RASTER_OT_sync_layers)
    bpy.utils.unregister_class(RASTER_OT_move_layer)
    bpy.utils.unregister_class(RASTER_OT_remove_layer)
    bpy.utils.unregister_class(RASTER_OT_add_layer)