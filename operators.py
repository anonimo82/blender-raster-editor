import bpy
from .engine import rebuild_node_tree

class RASTER_OT_create_canvas(bpy.types.Operator):
    bl_idname = "raster.create_canvas"
    bl_label = "Create Canvas"
    bl_description = "Crea un piano pronto per la pittura"

    def execute(self, context):
        bpy.ops.mesh.primitive_plane_add(size=2, enter_editmode=False, align='WORLD')
        obj = context.active_object
        
        mat = bpy.data.materials.new(name="CanvasMaterial")
        mat.use_nodes = True
        obj.data.materials.append(mat)
        
        # Pulisce i layer vecchi e ne crea uno di base
        obj.raster_layers.clear()
        base_layer = obj.raster_layers.add()
        base_layer.name = "Background"
        
        rebuild_node_tree(obj)
        return {'FINISHED'}

class RASTER_OT_add_layer(bpy.types.Operator):
    bl_idname = "raster.add_layer"
    bl_label = "Add Layer"
    
    def execute(self, context):
        obj = context.active_object
        new_layer = obj.raster_layers.add()
        new_layer.name = f"Layer {len(obj.raster_layers)}"
        rebuild_node_tree(obj)
        return {'FINISHED'}

class RASTER_OT_remove_layer(bpy.types.Operator):
    bl_idname = "raster.remove_layer"
    bl_label = "Remove Layer"
    index: bpy.props.IntProperty()
    
    def execute(self, context):
        obj = context.active_object
        obj.raster_layers.remove(self.index)
        
        if obj.raster_active_index >= len(obj.raster_layers):
            obj.raster_active_index = max(0, len(obj.raster_layers) - 1)
            
        rebuild_node_tree(obj)
        return {'FINISHED'}

class RASTER_OT_move_layer(bpy.types.Operator):
    bl_idname = "raster.move_layer"
    bl_label = "Move Layer"
    index: bpy.props.IntProperty()
    direction: bpy.props.EnumProperty(items=[('UP', "Up", ""), ('DOWN', "Down", "")])

    def execute(self, context):
        obj = context.active_object
        new_index = self.index - 1 if self.direction == 'UP' else self.index + 1
        
        if 0 <= new_index < len(obj.raster_layers):
            obj.raster_layers.move(self.index, new_index)
            # Mantieni il focus sul layer spostato se era attivo
            if obj.raster_active_index == self.index:
                obj.raster_active_index = new_index
            elif obj.raster_active_index == new_index:
                obj.raster_active_index = self.index
                
            rebuild_node_tree(obj)
        return {'FINISHED'}

class RASTER_OT_duplicate_layer(bpy.types.Operator):
    bl_idname = "raster.duplicate_layer"
    bl_label = "Duplicate Layer"
    index: bpy.props.IntProperty()

    def execute(self, context):
        obj = context.active_object
        layers = obj.raster_layers
        src_layer = layers[self.index]
        
        new_layer = layers.add()
        new_layer.name = src_layer.name + " Copy"
        new_layer.image = src_layer.image
        new_layer.is_visible = src_layer.is_visible
        new_layer.opacity = src_layer.opacity
        new_layer.blend_type = src_layer.blend_type
        # Lasciamo group_name e maschera vuoti per generarli in modo indipendente
        
        new_index = self.index + 1
        layers.move(len(layers) - 1, new_index)
        
        rebuild_node_tree(obj)
        return {'FINISHED'}

class RASTER_OT_sync_layers(bpy.types.Operator):
    bl_idname = "raster.sync_layers"
    bl_label = "Apply Changes"
    bl_description = "Forza l'aggiornamento dei nodi (utile per l'opacità)"

    def execute(self, context):
        rebuild_node_tree(context.active_object)
        return {'FINISHED'}

class RASTER_OT_merge_visible(bpy.types.Operator):
    bl_idname = "raster.merge_visible"
    bl_label = "Merge Visible"
    bl_description = "Bake dei layer visibili in una nuova immagine"
    bl_options = {'REGISTER', 'UNDO'}

    resolution: bpy.props.IntProperty(name="Resolution", default=1024, min=256, max=4096)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        obj = context.active_object
        if not obj or not obj.active_material:
            self.report({'ERROR'}, "No active object/material.")
            return {'CANCELLED'}

        rebuild_node_tree(obj)
        mat = obj.active_material
        nodes = mat.node_tree.nodes
        visible_layers = [l for l in obj.raster_layers if l.is_visible]

        if len(visible_layers) <= 1:
            self.report({'WARNING'}, "At least 2 visible layers are needed to merge.")
            return {'CANCELLED'}

        orig_engine = context.scene.render.engine
        context.scene.render.engine = 'CYCLES'
        context.scene.cycles.bake_type = 'DIFFUSE'
        context.scene.render.bake.use_pass_direct = False
        context.scene.render.bake.use_pass_indirect = False
        context.scene.render.bake.use_pass_color = True
        
        img_name = f"Merged_Canvas_{len(bpy.data.images)}"
        merged_img = bpy.data.images.new(name=img_name, width=self.resolution, height=self.resolution)
        
        bake_node = nodes.new('ShaderNodeTexImage')
        bake_node.image = merged_img
        bake_node.select = True
        nodes.active = bake_node

        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        context.view_layer.objects.active = obj

        try:
            bpy.ops.object.bake(type='DIFFUSE', save_mode='INTERNAL')
        except Exception as e:
            self.report({'ERROR'}, f"Bake failed: {e}")
            nodes.remove(bake_node)
            context.scene.render.engine = orig_engine
            return {'CANCELLED'}

        nodes.remove(bake_node)
        context.scene.render.engine = orig_engine

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

class RASTER_OT_set_active_layer(bpy.types.Operator):
    bl_idname = "raster.set_active_layer"
    bl_label = "Set Active Layer"
    index: bpy.props.IntProperty()
    is_mask: bpy.props.BoolProperty(default=False)

    def execute(self, context):
        obj = context.active_object
        obj.raster_active_index = self.index
        obj.raster_active_is_mask = self.is_mask
        rebuild_node_tree(obj)
        return {'FINISHED'}

class RASTER_OT_create_mask(bpy.types.Operator):
    bl_idname = "raster.create_mask"
    bl_label = "Create Mask"
    index: bpy.props.IntProperty()

    def execute(self, context):
        obj = context.active_object
        layer = obj.raster_layers[self.index]
        if not layer.mask_image:
            img_name = f"{layer.name}_Mask"
            mask_img = bpy.data.images.new(name=img_name, width=1024, height=1024, alpha=False)
            mask_img.generated_color = (1.0, 1.0, 1.0, 1.0)
            layer.mask_image = mask_img
            layer.use_mask = True
            
            obj.raster_active_index = self.index
            obj.raster_active_is_mask = True
            
        rebuild_node_tree(obj)
        return {'FINISHED'}

class RASTER_OT_remove_mask(bpy.types.Operator):
    bl_idname = "raster.remove_mask"
    bl_label = "Remove Mask"
    index: bpy.props.IntProperty()

    def execute(self, context):
        obj = context.active_object
        layer = obj.raster_layers[self.index]
        layer.mask_image = None
        
        if obj.raster_active_index == self.index and obj.raster_active_is_mask:
            obj.raster_active_is_mask = False
            
        rebuild_node_tree(obj)
        return {'FINISHED'}

classes = (
    RASTER_OT_create_canvas,
    RASTER_OT_add_layer,
    RASTER_OT_remove_layer,
    RASTER_OT_move_layer,
    RASTER_OT_duplicate_layer,
    RASTER_OT_sync_layers,
    RASTER_OT_merge_visible,
    RASTER_OT_set_active_layer,
    RASTER_OT_create_mask,
    RASTER_OT_remove_mask
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)