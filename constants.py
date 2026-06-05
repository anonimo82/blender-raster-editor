"""
Constants and configuration for Blender Raster Editor.
Centralizes all magic numbers and strings for easier maintenance.
"""

# Node names and identifiers
NODE_FRAME_NAME = "LAYER_MANAGER_FRAME"
NODE_FRAME_LABEL = "⚠ MANAGED BY LAYER MANAGER - DO NOT MODIFY MANUALLY ⚠"
NODE_FRAME_LABEL_SIZE = 20

# Internal node group names
TEXTURE_NODE_NAME = "MainTexture"
MASK_NODE_NAME = "MaskTexture"
OPACITY_MATH_NODE_NAME = "OpacityMath"

# Node group socket names
SOCKET_COLOR_OUTPUT = "Color"
SOCKET_FACTOR_OUTPUT = "Factor"

# Shader node types
SHADER_TYPE_PRINCIPLED = "BSDF_PRINCIPLED"

# Fix Blender 5.1 compatibility: nodes.new() and n.type use different strings
# for group nodes. nodes.new() requires "ShaderNodeGroup" (changed in 5.1),
# while n.type still returns the legacy "GROUP" string for read-only checks.
# Keeping them as separate constants makes the distinction explicit and allows
# each to be updated independently if Blender changes either value again.
SHADER_TYPE_GROUP = "ShaderNodeGroup"   # passed to nodes.new()
SHADER_NODE_GROUP_TYPE = "GROUP"        # compared against n.type

# nodes.new() identifiers
NODE_TYPE_MIX = "ShaderNodeMix"
NODE_TYPE_TEX_IMAGE = "ShaderNodeTexImage"
NODE_TYPE_MATH = "ShaderNodeMath"
NODE_TYPE_FRAME = "NodeFrame"
NODE_TYPE_GROUP_OUTPUT = "NodeGroupOutput"
NODE_TYPE_GROUP_TREE = "ShaderNodeTree"
# n.type check value (different from nodes.new() key)
SHADER_NODE_TEX_IMAGE_TYPE = "TEX_IMAGE"
SHADER_MATH_OPERATION_MULTIPLY = "MULTIPLY"
SHADER_MIX_DATA_TYPE_RGBA = "RGBA"

# Image source types
IMAGE_SOURCE_MOVIE = "MOVIE"
IMAGE_SOURCE_SEQUENCE = "SEQUENCE"

# Default values
DEFAULT_LAYER_NAME = "Layer"
DEFAULT_OPACITY = 1.0
DEFAULT_BLEND_MODE = "MIX"
DEFAULT_CANVAS_SIZE = 2.0
DEFAULT_CANVAS_NAME = "Canvas"
DEFAULT_MATERIAL_NAME = "CanvasMaterial"

# Camera settings
DEFAULT_CAMERA_NAME = "Canvas_Camera"
DEFAULT_CAMERA_HEIGHT = 5.0
DEFAULT_CAMERA_TYPE = "ORTHO"  # replaces inline 'ORTHO' literal
OBJECT_TYPE_CAMERA = "CAMERA"  # Fix W: replaces inline 'CAMERA' literal in operator
DEFAULT_RENDER_RESOLUTION = 1920

# Image generation settings
DEFAULT_MASK_RESOLUTION = 1024
DEFAULT_MASK_COLOR = (1.0, 1.0, 1.0, 1.0)
DEFAULT_IMAGE_ALPHA = True

# FIX #6: dedicated constant for mask images (greyscale, no alpha channel).
# Replaces the confusing `not DEFAULT_IMAGE_ALPHA` expression used in operators.py.
MASK_IMAGE_ALPHA = False

# Merge/bake settings
BAKE_ENGINE = "CYCLES"
BAKE_TYPE = "DIFFUSE"
MIN_VISIBLE_LAYERS_FOR_MERGE = 2
DEFAULT_MERGE_RESOLUTION = 1024

# Node positioning
NODE_START_X = -1000
NODE_START_Y = 400
NODE_VERTICAL_SPACING = 250
NODE_HORIZONTAL_SPACING = 250

# Internal node positions (in node groups)
INTERNAL_MAIN_TEXTURE_Y = 100
INTERNAL_MAIN_TEXTURE_X = -300
INTERNAL_MASK_TEXTURE_Y = -150
INTERNAL_MASK_TEXTURE_X = -300
INTERNAL_MATH_NODE_Y = -100
INTERNAL_MATH_NODE_X = -100
INTERNAL_OUTPUT_NODE_X = 100
INTERNAL_OUTPUT_NODE_Y = 0

# UI settings
UI_PANEL_SPACE = "VIEW_3D"
UI_PANEL_REGION = "UI"
UI_PANEL_CATEGORY = "Paint Layers"

# Error messages
ERROR_NO_ACTIVE_OBJECT = "No active object selected."
ERROR_NO_MATERIAL = "Object does not have an active material."
ERROR_NO_NODES = "Material does not have nodes enabled."
ERROR_BAKE_FAILED = "Baking operation failed."
ERROR_INSUFFICIENT_LAYERS = "At least 2 visible layers are required to merge."

# Warning messages
WARNING_NO_PRINCIPLED = "Could not find Principled BSDF node."

# Info messages
INFO_CANVAS_CREATED = "Canvas created successfully."
INFO_LAYER_ADDED = "Layer added successfully."
INFO_LAYERS_MERGED = "Layers successfully merged!"
INFO_CANVAS_RESIZED = "Canvas resized successfully!"
INFO_CAMERA_FRAMED = "Camera framed perfectly!"
