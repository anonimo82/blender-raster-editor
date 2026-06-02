"""
Property definitions for Blender Raster Editor layers and settings.
Defines all custom properties attached to Blender objects.
"""

import logging
from typing import Optional

import bpy
from bpy.types import PropertyGroup, Object

from .constants import *

logger = logging.getLogger(__name__)


def _auto_update_tree(self: 'RasterLayerItem', context: bpy.types.Context) -> None:
    """
    Callback function triggered when layer properties change.
    Updates the shader node tree and handles canvas aspect ratio.
    
    Args:
        self: The layer being modified
        context: The Blender context
    """
    if not context.active_object:
        return

    obj: Object = context.active_object

    # Auto-adjust canvas aspect ratio when loading image on background layer
    try:
        if (len(obj.raster_layers) > 0 
            and self == obj.raster_layers[0]
            and self.image 
            and self.image.size[0] > 0 
            and self.image.size[1] > 0):
            
            w, h = self.image.size
            if w >= h:
                obj.scale.x = w / h
                obj.scale.y = 1.0
            else:
                obj.scale.x = 1.0
                obj.scale.y = h / w
                
            logger.debug(f"Auto-adjusted canvas aspect ratio to {w}x{h}")
    except Exception as e:
        logger.warning(f"Failed to auto-adjust canvas aspect: {e}")

    # Rebuild node tree
    try:
        from .engine import rebuild_node_tree
        rebuild_node_tree(obj)
    except Exception as e:
        logger.error(f"Failed to rebuild node tree on property update: {e}")


class RasterLayerItem(PropertyGroup):
    """
    Represents a single layer in the raster layer system.
    
    Properties:
        name: User-readable layer name
        image: The main texture image for this layer
        mask_image: Optional black-and-white mask image
        use_mask: Whether the mask is active
        is_visible: Layer visibility toggle
        blend_type: Blending mode (Mix, Multiply, etc.)
        opacity: Layer opacity (0.0 - 1.0)
        group_name: Internal node group identifier
    """
    
    name: bpy.props.StringProperty(
        name="Name",
        description="Layer name",
        default=DEFAULT_LAYER_NAME
    )

    image: bpy.props.PointerProperty(
        name="Image",
        description="Main texture image for this layer",
        type=bpy.types.Image,
        update=_auto_update_tree
    )

    mask_image: bpy.props.PointerProperty(
        name="Mask",
        description="Black-and-white mask image (white reveals, black hides)",
        type=bpy.types.Image,
        update=_auto_update_tree
    )

    use_mask: bpy.props.BoolProperty(
        name="Enable Mask",
        description="Toggle mask visibility",
        default=True,
        update=_auto_update_tree
    )

    is_visible: bpy.props.BoolProperty(
        name="Visible",
        description="Toggle layer visibility in final composition",
        default=True,
        update=_auto_update_tree
    )

    blend_type: bpy.props.EnumProperty(
        name="Blend Mode",
        description="Layer blending mode",
        items=[
            ('MIX', "Mix", "Normal blend"),
            ('DARKEN', "Darken", "Darkens the image"),
            ('MULTIPLY', "Multiply", "Multiplies colors"),
            ('BURN', "Color Burn", "Darkens with intense effect"),
            ('LIGHTEN', "Lighten", "Lightens the image"),
            ('SCREEN', "Screen", "Inverts and multiplies"),
            ('DODGE', "Color Dodge", "Lightens with intense effect"),
            ('ADD', "Add", "Adds color values"),
            ('OVERLAY', "Overlay", "Combination of Multiply and Screen"),
            ('SOFT_LIGHT', "Soft Light", "Subtle overlay effect"),
            ('LINEAR_LIGHT', "Linear Light", "Intense dodge/burn"),
            ('DIFFERENCE', "Difference", "Subtracts colors"),
            ('EXCLUSION', "Exclusion", "Similar to Difference, lower contrast"),
            ('SUBTRACT', "Subtract", "Subtracts color values"),
            ('DIVIDE', "Divide", "Divides colors"),
            ('HUE', "Hue", "Uses hue of blend layer"),
            ('SATURATION', "Saturation", "Uses saturation of blend layer"),
            ('COLOR', "Color", "Uses color of blend layer"),
            ('VALUE', "Value", "Uses value of blend layer"),
        ],
        default=DEFAULT_BLEND_MODE,
        update=_auto_update_tree
    )

    opacity: bpy.props.FloatProperty(
        name="Opacity",
        description="Layer opacity (0 = transparent, 1 = opaque)",
        default=DEFAULT_OPACITY,
        min=0.0,
        max=1.0,
        subtype='FACTOR'
    )

    group_name: bpy.props.StringProperty(
        name="Group Name",
        description="Internal node group identifier (do not modify)",
        default=""
    )

    def validate(self) -> bool:
        """
        Validate layer properties for consistency.
        
        Returns:
            True if layer is valid, False otherwise
        """
        try:
            # Check if group exists
            if self.group_name and self.group_name not in bpy.data.node_groups:
                logger.warning(f"Layer '{self.name}' references missing node group '{self.group_name}'")
                return False
            
            # Check image validity
            if self.image and self.image.users == 0:
                logger.warning(f"Layer '{self.name}' has orphaned image reference")
                return False
            
            # Check mask validity
            if self.mask_image and self.mask_image.users == 0:
                logger.warning(f"Layer '{self.name}' has orphaned mask image reference")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Error validating layer '{self.name}': {e}")
            return False


def register() -> None:
    """Register all property groups."""
    try:
        bpy.utils.register_class(RasterLayerItem)
        logger.debug("Registered RasterLayerItem")

        # Register object properties
        bpy.types.Object.raster_layers = bpy.props.CollectionProperty(
            type=RasterLayerItem,
            name="Raster Layers",
            description="Collection of raster layers for this object"
        )

        bpy.types.Object.raster_active_index = bpy.props.IntProperty(
            name="Active Layer Index",
            description="Index of the currently active layer",
            default=0,
            min=0
        )

        bpy.types.Object.raster_active_is_mask = bpy.props.BoolProperty(
            name="Active Is Mask",
            description="Whether the active target is a mask or main image",
            default=False
        )

        logger.info("Properties registered successfully")
    except Exception as e:
        logger.error(f"Failed to register properties: {e}")
        raise


def unregister() -> None:
    """Unregister all property groups."""
    try:
        # Unregister object properties
        if hasattr(bpy.types.Object, "raster_active_is_mask"):
            del bpy.types.Object.raster_active_is_mask
        if hasattr(bpy.types.Object, "raster_active_index"):
            del bpy.types.Object.raster_active_index
        if hasattr(bpy.types.Object, "raster_layers"):
            del bpy.types.Object.raster_layers

        bpy.utils.unregister_class(RasterLayerItem)
        logger.debug("Unregistered RasterLayerItem")
        logger.info("Properties unregistered successfully")
    except Exception as e:
        logger.error(f"Failed to unregister properties: {e}")
