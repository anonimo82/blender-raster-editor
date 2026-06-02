"""
Blender Raster Editor - Non-destructive layer system for Blender.
Provides Photoshop-like layers with blend modes, masks, and video support.
"""

import logging
from typing import Callable

import bpy

from . import engine, operators, properties, ui

# Configure module-level logger
logger = logging.getLogger(__name__)

bl_info = {
    "name": "Blender Raster Editor",
    "author": "Gemini & User",
    "version": (1, 1, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Paint Layers",
    "description": "Non-destructive layer system for hand-painting and rotoscoping",
    "category": "Paint",
    "support": "COMMUNITY",
    "doc_url": "https://github.com/your-repo",
    "tracker_url": "https://github.com/your-repo/issues",
}


def _register_module(module) -> None:
    """Safely register a module if it has a register function."""
    try:
        if hasattr(module, "register"):
            module.register()
            logger.debug(f"Registered {module.__name__}")
    except Exception as e:
        logger.error(f"Failed to register {module.__name__}: {e}", exc_info=True)
        raise


def _unregister_module(module) -> None:
    """Safely unregister a module if it has an unregister function."""
    try:
        if hasattr(module, "unregister"):
            module.unregister()
            logger.debug(f"Unregistered {module.__name__}")
    except Exception as e:
        logger.error(f"Failed to unregister {module.__name__}: {e}", exc_info=True)


def register() -> None:
    """Register all addon components in correct order."""
    logger.info("Registering Blender Raster Editor")
    
    # Order matters: properties first, then operators, then UI
    for module in [properties, operators, ui]:
        _register_module(module)
    
    logger.info("Blender Raster Editor registered successfully")


def unregister() -> None:
    """Unregister all addon components in reverse order."""
    logger.info("Unregistering Blender Raster Editor")
    
    # Unregister in reverse order
    for module in [ui, operators, properties]:
        _unregister_module(module)
    
    logger.info("Blender Raster Editor unregistered successfully")


if __name__ == "__main__":
    register()
