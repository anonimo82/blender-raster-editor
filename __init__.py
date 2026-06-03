"""
Blender Raster Editor - Non-destructive layer system for Blender.
Provides Photoshop-like layers with blend modes, masks, and video support.
"""

import sys
import logging

import bpy

from . import engine, operators, properties, ui

# ---- Package-level logger ----
# Each module uses logging.getLogger(__name__), which produces child loggers
# under this root name. Configuring a handler here ensures all log output is
# visible in Blender's System Console without requiring the user to set up
# Python logging manually.
#
# FIX #7: attach a StreamHandler to the package root logger inside register()
# so that messages from every sub-module are actually emitted. The guard
# (`if not root.handlers`) prevents duplicate handlers if the add-on is
# reloaded without a full Blender restart.
_PKG_LOGGER_NAME = __name__.split(".")[0]  # top-level package name

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


def _configure_logging() -> None:
    """Attach a stdout StreamHandler to the package root logger if not already present.

    This is called once inside register() so that all child loggers
    (engine, operators, ui, …) have a working handler from the moment
    the add-on is enabled, without any manual setup by the user.
    """
    root = logging.getLogger(_PKG_LOGGER_NAME)
    if not root.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter("[%(name)s] %(levelname)s: %(message)s")
        )
        root.addHandler(handler)
        root.setLevel(logging.DEBUG)


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
    # FIX #7: configure logging before anything else so that errors during
    # module registration are also captured.
    _configure_logging()

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
