"""
Blender operators for the Raster Layer system.
Handles all user-triggered actions: layer management, baking, canvas setup, etc.
"""

import logging
from typing import Optional

import numpy as np
import bpy
from bpy.types import Operator, Object, Context

from .constants import *
from .engine import rebuild_node_tree

logger = logging.getLogger(__name__)


class BaseOperator(Operator):
    """Base class for all raster operators with common validation."""

    @staticmethod
    def _validate_active_object(context: Context) -> Object:
        """
        Validate that an active object exists.

        Args:
            context: Blender context

        Returns:
            Active object

        Raises:
            RuntimeError if no active object
        """
        obj = context.active_object
        if not obj:
            raise RuntimeError(ERROR_NO_ACTIVE_OBJECT)
        return obj

    @staticmethod
    def _validate_active_material(obj: Object) -> None:
        """
        Validate that object has an active material with nodes.

        Args:
            obj: Object to validate

        Raises:
            RuntimeError if validation fails
        """
        if not obj.active_material:
            raise RuntimeError(ERROR_NO_MATERIAL)
        if not obj.active_material.use_nodes:
            raise RuntimeError(ERROR_NO_NODES)

    def _report_error(self, message: str) -> None:
        """Report an error to the user."""
        self.report({'ERROR'}, message)
        logger.error(message)

    def _report_warning(self, message: str) -> None:
        """Report a warning to the user."""
        self.report({'WARNING'}, message)
        logger.warning(message)

    def _report_info(self, message: str) -> None:
        """Report info to the user."""
        self.report({'INFO'}, message)
        logger.info(message)


class RASTER_OT_create_canvas(BaseOperator):
    """Create a new canvas ready for painting."""

    bl_idname = "raster.create_canvas"
    bl_label = "Create Canvas"
    bl_description = "Creates a plane ready for painting"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context: Context):
        try:
            # Create plane
            bpy.ops.mesh.primitive_plane_add(
                size=DEFAULT_CANVAS_SIZE,
                enter_editmode=False,
                align='WORLD'
            )
            obj = context.active_object
            obj.name = DEFAULT_CANVAS_NAME
            if obj.name != DEFAULT_CANVAS_NAME:
                # Fix J: Blender silently renamed the object because DEFAULT_CANVAS_NAME
                # was already in use. Warn the user so they are not confused.
                logger.warning(
                    f"An object named '{DEFAULT_CANVAS_NAME}' already exists in the scene. "
                    f"New canvas was created as '{obj.name}'."
                )
                self._report_warning(
                    f"'{DEFAULT_CANVAS_NAME}' already exists — new canvas created as '{obj.name}'"
                )

            # Create material
            mat = bpy.data.materials.new(name=DEFAULT_MATERIAL_NAME)
            mat.use_nodes = True
            obj.data.materials.append(mat)

            # Initialize layers
            obj.raster_layers.clear()
            base_layer = obj.raster_layers.add()
            base_layer.name = "Background"

            # Rebuild node tree
            if not rebuild_node_tree(obj):
                self._report_warning("Canvas created but node tree setup had issues")
            else:
                self._report_info(INFO_CANVAS_CREATED)

            return {'FINISHED'}
        except Exception as e:
            self._report_error(f"Failed to create canvas: {str(e)}")
            return {'CANCELLED'}


class RASTER_OT_add_layer(BaseOperator):
    """Add a new layer to the current canvas."""

    bl_idname = "raster.add_layer"
    bl_label = "Add Layer"
    bl_description = "Adds a new layer"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context: Context):
        try:
            obj = self._validate_active_object(context)
            self._validate_active_material(obj)

            new_layer = obj.raster_layers.add()
            new_layer.name = f"{DEFAULT_LAYER_NAME} {len(obj.raster_layers)}"

            rebuild_node_tree(obj)
            self._report_info(INFO_LAYER_ADDED)
            return {'FINISHED'}
        except RuntimeError as e:
            self._report_error(str(e))
            return {'CANCELLED'}


class RASTER_OT_remove_layer(BaseOperator):
    """Remove a layer from the canvas."""

    bl_idname = "raster.remove_layer"
    bl_label = "Remove Layer"
    bl_options = {'REGISTER', 'UNDO'}

    index: bpy.props.IntProperty(
        name="Layer Index",
        description="Index of layer to remove",
        min=0
    )

    def execute(self, context: Context):
        try:
            obj = self._validate_active_object(context)

            if not (0 <= self.index < len(obj.raster_layers)):
                raise RuntimeError(f"Invalid layer index: {self.index}")

            # Fix V: capture active_index BEFORE remove() so that the
            # is_mask reset below compares against the original active
            # layer, not the post-clamp value. Without this, deleting a
            # non-active layer whose index coincidentally matches the
            # clamped active_index would incorrectly reset is_mask on
            # the surviving active layer (regression introduced by Fix T).
            was_active_index = obj.raster_active_index

            obj.raster_layers.remove(self.index)

            # Update active index
            if obj.raster_active_index >= len(obj.raster_layers):
                obj.raster_active_index = max(0, len(obj.raster_layers) - 1)

            # Fix T (corrected by Fix V): reset is_mask only when the
            # deleted layer was actually the active paint target.
            if self.index == was_active_index:
                obj.raster_active_is_mask = False

            rebuild_node_tree(obj)
            return {'FINISHED'}
        except RuntimeError as e:
            self._report_error(str(e))
            return {'CANCELLED'}


class RASTER_OT_move_layer(BaseOperator):
    """Move a layer up or down in the stack."""

    bl_idname = "raster.move_layer"
    bl_label = "Move Layer"
    bl_options = {'REGISTER', 'UNDO'}

    index: bpy.props.IntProperty(
        name="Layer Index",
        description="Index of layer to move",
        min=0
    )
    direction: bpy.props.EnumProperty(
        name="Direction",
        items=[('UP', "Up", ""), ('DOWN', "Down", "")],
        default='UP'
    )

    def execute(self, context: Context):
        try:
            obj = self._validate_active_object(context)
            layers = obj.raster_layers

            if not (0 <= self.index < len(layers)):
                raise RuntimeError(f"Invalid layer index: {self.index}")

            new_index = self.index - 1 if self.direction == 'UP' else self.index + 1

            if not (0 <= new_index < len(layers)):
                return {'FINISHED'}  # Already at boundary

            # Move layer
            layers.move(self.index, new_index)

            # Update active index
            if obj.raster_active_index == self.index:
                obj.raster_active_index = new_index
            elif obj.raster_active_index == new_index:
                obj.raster_active_index = self.index

            rebuild_node_tree(obj)
            return {'FINISHED'}
        except RuntimeError as e:
            self._report_error(str(e))
            return {'CANCELLED'}


class RASTER_OT_duplicate_layer(BaseOperator):
    """Duplicate a layer."""

    bl_idname = "raster.duplicate_layer"
    bl_label = "Duplicate Layer"
    bl_options = {'REGISTER', 'UNDO'}

    index: bpy.props.IntProperty(
        name="Layer Index",
        description="Index of layer to duplicate",
        min=0
    )

    def execute(self, context: Context):
        try:
            obj = self._validate_active_object(context)
            layers = obj.raster_layers

            if not (0 <= self.index < len(layers)):
                raise RuntimeError(f"Invalid layer index: {self.index}")

            src_layer = layers[self.index]

            # Create new layer
            new_layer = layers.add()
            new_layer.name = f"{src_layer.name} Copy"
            new_layer.image = src_layer.image
            new_layer.mask_image = src_layer.mask_image
            new_layer.is_visible = src_layer.is_visible
            new_layer.opacity = src_layer.opacity
            new_layer.blend_type = src_layer.blend_type
            new_layer.use_mask = src_layer.use_mask
            # Fix E: explicitly clear group_name so create_or_update_layer_group()
            # always creates a fresh, independent NodeGroup for the duplicate.
            # Sharing group_name with the source would cause both layers to
            # mutate the same node group, corrupting each other's state.
            new_layer.group_name = ""

            # Move to position after source
            new_index = self.index + 1
            layers.move(len(layers) - 1, new_index)

            rebuild_node_tree(obj)
            return {'FINISHED'}
        except RuntimeError as e:
            self._report_error(str(e))
            return {'CANCELLED'}


class RASTER_OT_set_active_layer(BaseOperator):
    """Set the active layer for painting."""

    bl_idname = "raster.set_active_layer"
    bl_label = "Set Active Layer"
    bl_description = "Select this layer to paint on it"
    bl_options = {'REGISTER'}

    index: bpy.props.IntProperty(
        name="Layer Index",
        description="Index of layer to activate",
        min=0
    )
    is_mask: bpy.props.BoolProperty(
        name="Is Mask",
        description="Whether to activate the mask or main image",
        default=False
    )

    def execute(self, context: Context):
        try:
            obj = self._validate_active_object(context)

            if not (0 <= self.index < len(obj.raster_layers)):
                raise RuntimeError(f"Invalid layer index: {self.index}")

            obj.raster_active_index = self.index
            obj.raster_active_is_mask = self.is_mask

            rebuild_node_tree(obj)
            return {'FINISHED'}
        except RuntimeError as e:
            self._report_error(str(e))
            return {'CANCELLED'}


class RASTER_OT_create_mask(BaseOperator):
    """Create a mask for a layer."""

    bl_idname = "raster.create_mask"
    bl_label = "Create Mask"
    bl_description = "Adds a white mask to the layer"
    bl_options = {'REGISTER', 'UNDO'}

    index: bpy.props.IntProperty(
        name="Layer Index",
        description="Index of layer to add mask to",
        min=0
    )

    def execute(self, context: Context):
        try:
            obj = self._validate_active_object(context)

            if not (0 <= self.index < len(obj.raster_layers)):
                raise RuntimeError(f"Invalid layer index: {self.index}")

            layer = obj.raster_layers[self.index]

            if not layer.mask_image:
                img_name = f"{layer.name}_Mask"
                mask_img = bpy.data.images.new(
                    name=img_name,
                    width=DEFAULT_MASK_RESOLUTION,
                    height=DEFAULT_MASK_RESOLUTION,
                    # FIX #6: use the dedicated MASK_IMAGE_ALPHA constant
                    # instead of the confusing `not DEFAULT_IMAGE_ALPHA` expression.
                    alpha=MASK_IMAGE_ALPHA
                )
                mask_img.generated_color = DEFAULT_MASK_COLOR
                layer.mask_image = mask_img
                layer.use_mask = True

                obj.raster_active_index = self.index
                obj.raster_active_is_mask = True

            rebuild_node_tree(obj)
            return {'FINISHED'}
        except RuntimeError as e:
            self._report_error(str(e))
            return {'CANCELLED'}


class RASTER_OT_remove_mask(BaseOperator):
    """Remove a layer's mask."""

    bl_idname = "raster.remove_mask"
    bl_label = "Remove Mask"
    bl_options = {'REGISTER', 'UNDO'}

    index: bpy.props.IntProperty(
        name="Layer Index",
        description="Index of layer to remove mask from",
        min=0
    )

    def execute(self, context: Context):
        try:
            obj = self._validate_active_object(context)

            if not (0 <= self.index < len(obj.raster_layers)):
                raise RuntimeError(f"Invalid layer index: {self.index}")

            layer = obj.raster_layers[self.index]
            layer.mask_image = None

            if obj.raster_active_index == self.index and obj.raster_active_is_mask:
                obj.raster_active_is_mask = False

            rebuild_node_tree(obj)
            return {'FINISHED'}
        except RuntimeError as e:
            self._report_error(str(e))
            return {'CANCELLED'}


class RASTER_OT_sync_layers(BaseOperator):
    """Sync layer properties with the node tree."""

    bl_idname = "raster.sync_layers"
    bl_label = "Apply Changes"
    bl_description = "Force node tree update (useful for opacity)"
    bl_options = {'REGISTER'}

    def execute(self, context: Context):
        try:
            obj = self._validate_active_object(context)
            if not rebuild_node_tree(obj):
                self._report_warning("Node tree update had issues")
            return {'FINISHED'}
        except RuntimeError as e:
            self._report_error(str(e))
            return {'CANCELLED'}


class RASTER_OT_resize_canvas(BaseOperator):
    """Resize all layers' canvas."""

    bl_idname = "raster.resize_canvas"
    bl_label = "Resize Canvas"
    bl_description = "Change resolution of all layers (adds empty space, no stretching)"
    bl_options = {'REGISTER', 'UNDO'}

    new_width: bpy.props.IntProperty(
        name="Width",
        description="New canvas width",
        default=1024,
        min=1
    )
    new_height: bpy.props.IntProperty(
        name="Height",
        description="New canvas height",
        default=1024,
        min=1
    )

    def invoke(self, context: Context, event):
        """Set default dimensions from first layer."""
        obj = context.active_object
        if obj and obj.raster_layers:
            for layer in obj.raster_layers:
                if layer.image and layer.image.source not in {IMAGE_SOURCE_MOVIE, IMAGE_SOURCE_SEQUENCE}:
                    self.new_width, self.new_height = layer.image.size
                    break
        return context.window_manager.invoke_props_dialog(self)

    @staticmethod
    def _resize_image_canvas(image, new_width: int, new_height: int):
        """
        Resize an image canvas without stretching.

        Args:
            image: Image to resize
            new_width: New width
            new_height: New height

        Returns:
            Resized image or original if invalid
        """
        if not image or image.source in {IMAGE_SOURCE_MOVIE, IMAGE_SOURCE_SEQUENCE}:
            return image

        old_w, old_h = image.size
        if old_w == new_width and old_h == new_height:
            return image

        try:
            # Read old pixels
            old_pixels = np.empty(old_w * old_h * 4, dtype=np.float32)
            image.pixels.foreach_get(old_pixels)
            old_pixels = old_pixels.reshape((old_h, old_w, 4))

            # Create new canvas
            new_pixels = np.zeros((new_height, new_width, 4), dtype=np.float32)

            # Calculate positioning
            y_off = max((new_height - old_h) // 2, 0)
            x_off = max((new_width - old_w) // 2, 0)
            old_start_y = max((old_h - new_height) // 2, 0)
            old_start_x = max((old_w - new_width) // 2, 0)

            copy_h = min(old_h - old_start_y, new_height - y_off)
            copy_w = min(old_w - old_start_x, new_width - x_off)

            # Copy pixels
            if copy_h > 0 and copy_w > 0:
                new_pixels[y_off:y_off + copy_h, x_off:x_off + copy_w] = \
                    old_pixels[old_start_y:old_start_y + copy_h, old_start_x:old_start_x + copy_w]

            # Create new image
            new_img = bpy.data.images.new(
                name=f"{image.name}_Resized",
                width=new_width,
                height=new_height,
                alpha=DEFAULT_IMAGE_ALPHA
            )
            new_img.pixels.foreach_set(new_pixels.ravel())
            return new_img
        except Exception as e:
            logger.error(f"Failed to resize image '{image.name}': {e}")
            return image

    def execute(self, context: Context):
        try:
            obj = self._validate_active_object(context)
            # FIX #2: validate the material before proceeding, so a missing
            # material produces a clear user-facing error instead of a silent
            # False return from rebuild_node_tree() at the end.
            self._validate_active_material(obj)

            # Resize all layer images
            for layer in obj.raster_layers:
                layer.image = self._resize_image_canvas(layer.image, self.new_width, self.new_height)
                layer.mask_image = self._resize_image_canvas(layer.mask_image, self.new_width, self.new_height)

            # Adjust object dimensions to match aspect ratio
            if self.new_width > 0 and self.new_height > 0:
                ratio = self.new_width / self.new_height
                max_dim = max(obj.dimensions.x, obj.dimensions.y)
                if ratio >= 1:
                    obj.dimensions.x = max_dim
                    obj.dimensions.y = max_dim / ratio
                else:
                    obj.dimensions.y = max_dim
                    obj.dimensions.x = max_dim * ratio

            rebuild_node_tree(obj)
            self._report_info(INFO_CANVAS_RESIZED)
            return {'FINISHED'}
        except RuntimeError as e:
            self._report_error(str(e))
            return {'CANCELLED'}


class RASTER_OT_merge_visible(BaseOperator):
    """Merge all visible layers into a single baked image."""

    bl_idname = "raster.merge_visible"
    bl_label = "Merge Visible"
    bl_description = "Bake visible layers into a new image"
    bl_options = {'REGISTER', 'UNDO'}

    resolution: bpy.props.IntProperty(
        name="Resolution",
        description="Output resolution",
        default=DEFAULT_MERGE_RESOLUTION,
        min=256,
        max=4096
    )

    def invoke(self, context: Context, event):
        """Show resolution dialog."""
        return context.window_manager.invoke_props_dialog(self)

    def _setup_bake(self, context: Context) -> None:
        """Configure render engine for baking."""
        context.scene.render.engine = BAKE_ENGINE
        context.scene.cycles.bake_type = BAKE_TYPE
        context.scene.render.bake.use_pass_direct = False
        context.scene.render.bake.use_pass_indirect = False
        context.scene.render.bake.use_pass_color = True

    def execute(self, context: Context):
        try:
            obj = self._validate_active_object(context)
            self._validate_active_material(obj)

            # Fix I: compute visible_layers before the initial rebuild so the
            # same snapshot is used both for the minimum-layer check and later
            # for hiding originals — avoiding any inconsistency if a property
            # callback were to mutate the layer list during rebuild.
            visible_layers = [l for l in obj.raster_layers if l.is_visible]

            if len(visible_layers) < MIN_VISIBLE_LAYERS_FOR_MERGE:
                raise RuntimeError(ERROR_INSUFFICIENT_LAYERS)

            rebuild_node_tree(obj)
            mat = obj.active_material
            nodes = mat.node_tree.nodes

            # Save original state
            orig_engine = context.scene.render.engine

            try:
                # Setup baking
                self._setup_bake(context)

                # Create output image
                img_name = f"Merged_Canvas_{len(bpy.data.images)}"
                merged_img = bpy.data.images.new(
                    name=img_name,
                    width=self.resolution,
                    height=self.resolution
                )

                # Create bake node
                bake_node = nodes.new(NODE_TYPE_TEX_IMAGE)
                bake_node.image = merged_img
                bake_node.select = True
                nodes.active = bake_node

                try:
                    # Setup object for baking
                    bpy.ops.object.select_all(action='DESELECT')
                    obj.select_set(True)
                    context.view_layer.objects.active = obj

                    # Perform bake
                    bpy.ops.object.bake(type=BAKE_TYPE, save_mode='INTERNAL')
                finally:
                    # Fix D: always remove the bake node, even if bake() raises
                    # an exception (e.g. Cycles unavailable, missing UVs).
                    # Without this the temporary node corrupts the tree permanently.
                    if bake_node and bake_node.name in nodes:
                        nodes.remove(bake_node)

                # Hide original layers
                for layer in visible_layers:
                    layer.is_visible = False

                # Create merged layer
                new_layer = obj.raster_layers.add()
                new_layer.name = "Merged Layer"
                new_layer.image = merged_img
                new_layer.is_visible = True
                new_layer.opacity = DEFAULT_OPACITY
                new_layer.blend_type = DEFAULT_BLEND_MODE

                rebuild_node_tree(obj)
                self._report_info(INFO_LAYERS_MERGED)
                return {'FINISHED'}

            except Exception as e:
                self._report_error(f"{ERROR_BAKE_FAILED}: {str(e)}")
                return {'CANCELLED'}

            finally:
                context.scene.render.engine = orig_engine

        except RuntimeError as e:
            self._report_error(str(e))
            return {'CANCELLED'}


class RASTER_OT_setup_camera(BaseOperator):
    """Setup an orthographic camera framing the canvas."""

    bl_idname = "raster.setup_camera"
    bl_label = "Frame Camera"
    bl_description = "Frames the canvas with an Orthographic camera"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context: Context):
        try:
            obj = self._validate_active_object(context)

            # Find or create camera
            cam_obj = next(
                (ob for ob in context.scene.objects if ob.type == OBJECT_TYPE_CAMERA),
                None
            )
            if not cam_obj:
                cam_data = bpy.data.cameras.new(DEFAULT_CAMERA_NAME)
                cam_obj = bpy.data.objects.new(DEFAULT_CAMERA_NAME, cam_data)
                context.collection.objects.link(cam_obj)

            context.scene.camera = cam_obj

            # Position camera
            cam_obj.location = (
                obj.location.x,
                obj.location.y,
                obj.location.z + DEFAULT_CAMERA_HEIGHT
            )
            cam_obj.rotation_euler = (0.0, 0.0, 0.0)

            # Setup orthographic view
            cam_obj.data.type = DEFAULT_CAMERA_TYPE
            max_dim = max(obj.dimensions.x, obj.dimensions.y)
            # Fix R: guard against a zero-dimension object (e.g. fresh mesh
            # with zeroed scale). ortho_scale=0 makes the entire scene
            # invisible in the camera viewport without any error.
            if max_dim <= 0.0:
                raise RuntimeError(
                    "Canvas has zero dimensions — apply scale (Ctrl+A) before framing the camera."
                )
            cam_obj.data.ortho_scale = max_dim

            # Set render resolution based on aspect ratio
            if obj.dimensions.y > 0 and obj.dimensions.x > 0:
                ratio = obj.dimensions.x / obj.dimensions.y
                if ratio >= 1:
                    context.scene.render.resolution_x = DEFAULT_RENDER_RESOLUTION
                    context.scene.render.resolution_y = int(DEFAULT_RENDER_RESOLUTION / ratio)
                else:
                    context.scene.render.resolution_y = DEFAULT_RENDER_RESOLUTION
                    context.scene.render.resolution_x = int(DEFAULT_RENDER_RESOLUTION * ratio)

            # Switch viewport to camera
            for area in context.screen.areas:
                if area.type == 'VIEW_3D':
                    area.spaces[0].region_3d.view_perspective = 'CAMERA'
                    break

            self._report_info(INFO_CAMERA_FRAMED)
            return {'FINISHED'}

        except RuntimeError as e:
            self._report_error(str(e))
            return {'CANCELLED'}


# Register all operator classes
_OPERATOR_CLASSES = (
    RASTER_OT_create_canvas,
    RASTER_OT_add_layer,
    RASTER_OT_remove_layer,
    RASTER_OT_move_layer,
    RASTER_OT_duplicate_layer,
    RASTER_OT_set_active_layer,
    RASTER_OT_create_mask,
    RASTER_OT_remove_mask,
    RASTER_OT_sync_layers,
    RASTER_OT_resize_canvas,
    RASTER_OT_merge_visible,
    RASTER_OT_setup_camera,
)


def register() -> None:
    """Register all operators."""
    for cls in _OPERATOR_CLASSES:
        try:
            bpy.utils.register_class(cls)
            logger.debug(f"Registered {cls.__name__}")
        except Exception as e:
            logger.error(f"Failed to register {cls.__name__}: {e}")
            raise


def unregister() -> None:
    """Unregister all operators."""
    for cls in reversed(_OPERATOR_CLASSES):
        try:
            bpy.utils.unregister_class(cls)
            logger.debug(f"Unregistered {cls.__name__}")
        except Exception as e:
            logger.error(f"Failed to unregister {cls.__name__}: {e}")
