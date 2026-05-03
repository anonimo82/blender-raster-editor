import bpy
import numpy as np
from .engine import rebuild_node_tree

class RASTER_OT_create_canvas(bpy.types.Operator):
    bl_idname = "raster.create_canvas"
    bl_label = "Create Canvas"
    bl_description = "Creates a plane ready for painting"

    def execute(self, context):
        bpy.ops.mesh.primitive_plane_add(size=2, enter_editmode=False, align='WORLD')
        obj = context.active_object
        
        mat = bpy.data.materials.new(name="CanvasMaterial")
        mat.use_nodes = True
        obj.data.materials.append(mat)
        
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
        
        new_index = self.index + 1
        layers.move(len(layers) - 1, new_index)
        
        rebuild_node_tree(obj)
        return {'FINISHED'}

class RASTER_OT_sync_layers(bpy.types.Operator):
    bl_idname = "raster.sync_layers"
    bl_label = "Apply Changes"
    bl_description = "Force node tree update (useful for opacity)"

    def execute(self, context):
        rebuild_node_tree(context.active_object)
        return {'FINISHED'}

class RASTER_OT_merge_visible(bpy.types.Operator):
    bl_idname = "raster.merge_visible"
    bl_label = "Merge Visible"
    bl_description = "Bake visible layers into a new image"
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
    bl_description = "Select this layer to paint on it"
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
    bl_description = "Adds a white mask to the layer"
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

class RASTER_OT_resize_canvas(bpy.types.Operator):
    bl_idname = "raster.resize_canvas"
    bl_label = "Resize Canvas"
    bl_description = "Change resolution of all layers (adds empty space, no stretching)"
    bl_options = {'REGISTER', 'UNDO'}

    new_width: bpy.props.IntProperty(name="Width", default=1024, min=1)
    new_height: bpy.props.IntProperty(name="Height", default=1024, min=1)

    def invoke(self, context, event):
        obj = context.active_object
        if obj and obj.raster_layers:
            for layer in obj.raster_layers:
                if layer.image and layer.image.source not in {'MOVIE', 'SEQUENCE'}:
                    self.new_width = layer.image.size[0]
                    self.new_height = layer.image.size[1]
                    break
        return context.window_manager.invoke_props_dialog(self)

    def resize_image_canvas(self, image):
        if not image or image.source in {'MOVIE', 'SEQUENCE'}: 
            return image
            
        old_w, old_h = image.size
        if old_w == self.new_width and old_h == self.new_height:
            return image

        old_pixels = np.empty(old_w * old_h * 4, dtype=np.float32)
        image.pixels.foreach_get(old_pixels)
        old_pixels = old_pixels.reshape((old_h, old_w, 4))

        new_pixels = np.zeros((self.new_height, self.new_width, 4), dtype=np.float32)

        y_off = max((self.new_height - old_h) // 2, 0)
        x_off = max((self.new_width - old_w) // 2, 0)
        old_start_y = max((old_h - self.new_height) // 2, 0)
        old_start_x = max((old_w - self.new_width) // 2, 0)

        copy_h = min(old_h, self.new_height)
        copy_w = min(old_w, self.new_width)

        new_pixels[y_off:y_off+copy_h, x_off:x_off+copy_w] = \
            old_pixels[old_start_y:old_start_y+copy_h, old_start_x:old_start_x+copy_w]

        new_img = bpy.data.images.new(name=f"{image.name}_Resized", width=self.new_width, height=self.new_height, alpha=True)
        new_img.pixels.foreach_set(new_pixels.ravel())
        return new_img

    def execute(self, context):
        obj = context.active_object
        
        for layer in obj.raster_layers:
            layer.image = self.resize_image_canvas(layer.image)
            layer.mask_image = self.resize_image_canvas(layer.mask_image)

        ratio = self.new_width / self.new_height
        max_dim = max(obj.dimensions.x, obj.dimensions.y)
        if ratio >= 1:
            obj.dimensions.x = max_dim
            obj.dimensions.y = max_dim / ratio
        else:
            obj.dimensions.y = max_dim
            obj.dimensions.x = max_dim * ratio

        rebuild_node_tree(obj)
        self.report({'INFO'}, "Canvas resized successfully!")
        return {'FINISHED'}

class RASTER_OT_setup_camera(bpy.types.Operator):
    bl_idname = "raster.setup_camera"
    bl_label = "Frame Camera"
    bl_description = "Frames the canvas with an Orthographic camera and adjusts render resolution"

    def execute(self, context):
        obj = context.active_object
        if not obj:
            self.report({'WARNING'}, "Select the Canvas first.")
            return {'CANCELLED'}

        cam_obj = next((ob for ob in context.scene.objects if ob.type == 'CAMERA'), None)
        if not cam_obj:
            cam_data = bpy.data.cameras.new("Canvas_Camera")
            cam_obj = bpy.data.objects.new("Canvas_Camera", cam_data)
            context.collection.objects.link(cam_obj)
        
        context.scene.camera = cam_obj

        cam_obj.location = (obj.location.x, obj.location.y, obj.location.z + 5.0)
        cam_obj.rotation_euler = (0.0, 0.0, 0.0)
        cam_obj.data.type = 'ORTHO'
        
        max_dim = max(obj.dimensions.x, obj.dimensions.y)
        cam_obj.data.ortho_scale = max_dim

        render = context.scene.render
        if obj.dimensions.y > 0 and obj.dimensions.x > 0:
            ratio = obj.dimensions.x / obj.dimensions.y
            if ratio >= 1:
                render.resolution_x = 1920
                render.resolution_y = int(1920 / ratio)
            else:
                render.resolution_y = 1920
                render.resolution_x = int(1920 * ratio)

        # Cambia automaticamente la vista alla Telecamera
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces[0].region_3d.view_perspective = 'CAMERA'
                break

        self.report({'INFO'}, "Camera framed perfectly!")
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
    RASTER_OT_remove_mask,
    RASTER_OT_resize_canvas,
    RASTER_OT_setup_camera
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)