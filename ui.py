"""
UI panels and menus for the Blender Raster Editor.
Defines the viewport sidebar panel with layer management controls.
"""

import logging

import bpy
from bpy.types import Panel, UILayout, Object

from .constants import *

logger = logging.getLogger(__name__)


class VIEW3D_PT_raster_layers(Panel):
    """Main panel for the Raster Layer Manager in the 3D viewport."""

    bl_space_type = UI_PANEL_SPACE
    bl_region_type = UI_PANEL_REGION
    bl_category = UI_PANEL_CATEGORY
    bl_label = "Layer Manager"
    # Fix: removed 'DEFAULT_CLOSED' so the panel is visible immediately after
    # enabling the add-on. A first-time user seeing a blank, collapsed panel
    # has no obvious next step. The panel is lightweight enough that keeping
    # it open by default has no performance cost.

    def draw(self, context: bpy.types.Context) -> None:
        """Draw the main panel UI."""
        layout = self.layout
        obj = context.active_object

        # Canvas creation section
        self._draw_canvas_section(layout)
        layout.separator()

        # Validation
        if not obj or not obj.active_material:
            layout.label(text="Select object with Material", icon='ERROR')
            return

        # Layer management section
        self._draw_layer_management_section(layout, obj)
        layout.separator()

        # Layer list section
        self._draw_layer_list(layout, obj, context)
        layout.separator()

        # Utilities section
        self._draw_utilities_section(layout, context)

        # Paint settings section (if in paint mode)
        if context.mode == 'PAINT_TEXTURE':
            self._draw_paint_settings_section(layout, context)

    @staticmethod
    def _draw_canvas_section(layout: UILayout) -> None:
        """Draw canvas creation button."""
        layout.operator("raster.create_canvas", icon='MESH_PLANE', text="Create Canvas")

    @staticmethod
    def _draw_layer_management_section(layout: UILayout, obj: Object) -> None:
        """Draw layer creation button."""
        layout.operator("raster.add_layer", icon='ADD', text="Add Layer")

    @staticmethod
    def _draw_layer_list(layout: UILayout, obj: Object, context: bpy.types.Context) -> None:
        """Draw the list of layers."""
        # Fix: show a helpful hint when no layers exist yet, so the user knows
        # what to do rather than seeing an empty, unexplained space.
        if not obj.raster_layers:
            layout.label(text="No layers — click Add Layer to start", icon='INFO')
            return

        # Display layers in reverse order (top to bottom = highest to lowest in stack)
        for i in reversed(range(len(obj.raster_layers))):
            layer = obj.raster_layers[i]
            VIEW3D_PT_raster_layers._draw_layer_item(layout, obj, layer, i, context)

    @staticmethod
    def _draw_layer_item(
        layout: UILayout,
        obj: Object,
        layer: 'RasterLayerItem',
        index: int,
        context: bpy.types.Context
    ) -> None:
        """Draw a single layer item with controls."""
        box = layout.box()

        # Main layer row
        row = box.row(align=True)
        VIEW3D_PT_raster_layers._draw_paint_target_button(row, obj, index, False)
        VIEW3D_PT_raster_layers._draw_visibility_toggle(row, layer)
        row.prop(layer, "name", text="")
        VIEW3D_PT_raster_layers._draw_layer_reorder_buttons(row, index)
        VIEW3D_PT_raster_layers._draw_layer_action_buttons(row, index)

        # Image selection
        box.template_ID(layer, "image", new="image.new", open="image.open")

        # Mask section
        if layer.mask_image:
            VIEW3D_PT_raster_layers._draw_active_mask(box, obj, layer, index)
        else:
            VIEW3D_PT_raster_layers._draw_add_mask(box, index)

        # Blend mode and opacity (not for background layer)
        if index > 0:
            col = box.column(align=True)
            col.prop(layer, "blend_type", text="")
            col.prop(layer, "opacity", slider=True)

    @staticmethod
    def _draw_paint_target_button(row: UILayout, obj: Object, index: int, is_mask: bool) -> None:
        """Draw the paint target selection button."""
        is_active = (obj.raster_active_index == index and obj.raster_active_is_mask == is_mask)
        paint_icon = 'BRUSH_DATA' if is_active else 'RADIOBUT_OFF'
        btn = row.operator(
            "raster.set_active_layer",
            text="",
            icon=paint_icon,
            depress=is_active
        )
        btn.index = index
        btn.is_mask = is_mask

    @staticmethod
    def _draw_visibility_toggle(row: UILayout, layer: 'RasterLayerItem') -> None:
        """Draw layer visibility toggle button."""
        eye_icon = 'HIDE_OFF' if layer.is_visible else 'HIDE_ON'
        row.prop(layer, "is_visible", text="", icon=eye_icon)

    @staticmethod
    def _draw_layer_reorder_buttons(row: UILayout, index: int) -> None:
        """Draw layer reorder (up/down) buttons.

        FIX #5: buttons now use semantically correct direction values.
        Previously TRIA_UP fired direction='DOWN' and vice versa to compensate
        for the reversed draw order, making the code misleading and fragile.
        The operator itself uses logical UP/DOWN (lower/higher index), and the
        reversed display order is handled solely in _draw_layer_list — the two
        concerns are now cleanly separated.
        """
        btn_up = row.operator("raster.move_layer", text="", icon='TRIA_UP')
        btn_up.direction = 'UP'
        btn_up.index = index

        btn_down = row.operator("raster.move_layer", text="", icon='TRIA_DOWN')
        btn_down.direction = 'DOWN'
        btn_down.index = index

    @staticmethod
    def _draw_layer_action_buttons(row: UILayout, index: int) -> None:
        """Draw layer action buttons (duplicate, delete)."""
        btn_dup = row.operator("raster.duplicate_layer", text="", icon='COPYDOWN')
        btn_dup.index = index

        btn_del = row.operator("raster.remove_layer", text="", icon='X')
        btn_del.index = index

    @staticmethod
    def _draw_active_mask(box: UILayout, obj: Object, layer: 'RasterLayerItem', index: int) -> None:
        """Draw active mask controls."""
        mask_row = box.row(align=True)

        # Paint target button for mask
        VIEW3D_PT_raster_layers._draw_paint_target_button(mask_row, obj, index, True)

        # Mask enable toggle
        mask_row.prop(layer, "use_mask", text="", icon='MOD_MASK')

        # Mask image selector
        mask_row.template_ID(layer, "mask_image", new="image.new", open="image.open")

        # Remove mask button
        btn_rm = mask_row.operator("raster.remove_mask", text="", icon='X')
        btn_rm.index = index

    @staticmethod
    def _draw_add_mask(box: UILayout, index: int) -> None:
        """Draw add mask button."""
        mask_row = box.row(align=True)
        mask_row.label(text="", icon='BLANK1')
        btn_add = mask_row.operator("raster.create_mask", text="Add Mask", icon='MOD_MASK')
        btn_add.index = index

    @staticmethod
    def _draw_utilities_section(layout: UILayout, context: bpy.types.Context) -> None:
        """Draw utility buttons."""
        box_utils = layout.box()
        col = box_utils.column(align=True)
        col.scale_y = 1.2

        col.operator("raster.sync_layers", icon='FILE_REFRESH', text="Apply Opacity")

        row = col.row(align=True)
        row.operator("raster.merge_visible", icon='IMAGE_BACKGROUND', text="Merge")
        row.operator("raster.resize_canvas", icon='FULLSCREEN_ENTER', text="Resize Canvas")

        col.operator("raster.setup_camera", icon='OUTLINER_OB_CAMERA', text="Frame Camera")

    @staticmethod
    def _draw_paint_settings_section(layout: UILayout, context: bpy.types.Context) -> None:
        """Draw paint tool settings (shown when in texture paint mode)."""
        layout.separator()
        layout.label(text="Paint Settings", icon='TOOL_SETTINGS')

        settings = context.tool_settings.image_paint

        # Fix Blender 5.1: image_paint.brush is read-only and template_ID
        # renders a red box regardless of whether a brush is active, because
        # the brush selector is managed by Blender's tool system rather than
        # being directly assignable. Replacing template_ID with a label avoids
        # the misleading red display while still exposing the relevant brush
        # properties (color, size, strength, blend mode) for quick access.
        brush = settings.brush
        if brush:
            layout.label(text=f"Brush: {brush.name}", icon='BRUSH_DATA')
            box = layout.box()
            col = box.column(align=True)
            col.prop(brush, "color", text="Color")
            col.separator()
            col.prop(brush, "size", text="Radius")
            col.prop(brush, "strength", slider=True)
            col.separator()
            col.prop(brush, "blend", text="Mode")
        else:
            layout.label(text="No brush active", icon='ERROR')


def register() -> None:
    """Register UI classes."""
    try:
        bpy.utils.register_class(VIEW3D_PT_raster_layers)
        logger.debug("Registered VIEW3D_PT_raster_layers")
        logger.info("UI registered successfully")
    except Exception as e:
        logger.error(f"Failed to register UI: {e}")
        raise


def unregister() -> None:
    """Unregister UI classes."""
    try:
        bpy.utils.unregister_class(VIEW3D_PT_raster_layers)
        logger.debug("Unregistered VIEW3D_PT_raster_layers")
        logger.info("UI unregistered successfully")
    except Exception as e:
        logger.error(f"Failed to unregister UI: {e}")
