"""
Node tree management engine for the Raster Layer system.
Handles shader graph construction, layer composition, and node synchronization.
"""

import logging
from typing import Optional, List

import bpy
from bpy.types import Object, ShaderNodeTree, Node, ShaderNode

from .constants import *

logger = logging.getLogger(__name__)


class NodeTreeManager:
    """Manages shader node tree construction and updates for layer rendering."""

    @staticmethod
    def get_principled_bsdf(nodes: bpy.types.Nodes) -> Optional[ShaderNode]:
        """
        Find the Principled BSDF node in a node tree.

        Args:
            nodes: Collection of nodes to search

        Returns:
            Principled BSDF node if found, None otherwise
        """
        # next() with a default never raises StopIteration, so no try/except needed.
        result = next((n for n in nodes if n.type == SHADER_TYPE_PRINCIPLED), None)
        if result is None:
            logger.warning(WARNING_NO_PRINCIPLED)
        return result

    @staticmethod
    def clear_manager_frame(nodes: bpy.types.Nodes) -> bpy.types.Node:
        """
        Clear or create the layer manager frame node.

        Args:
            nodes: Collection of nodes to modify

        Returns:
            The manager frame node
        """
        manager_frame = nodes.get(NODE_FRAME_NAME)

        if manager_frame:
            # IMPORTANT — order dependency: orphan_groups must be snapshotted
            # BEFORE nodes.remove() is called. While the group nodes still exist
            # their node_tree has users >= 1, so we can safely collect references.
            # After removal users drops to 0, making the ng.users == 0 check
            # below correct. Reversing these two steps would break the purge.
            orphan_groups = [
                n.node_tree for n in nodes
                if n.parent == manager_frame
                and n.type == SHADER_TYPE_GROUP
                and getattr(n, "node_tree", None) is not None
            ]
            child_nodes = [n for n in nodes if n.parent == manager_frame]
            for node in child_nodes:
                nodes.remove(node)
            # Fix B: purge node groups that are now unreferenced (users == 0)
            # to avoid accumulating orphan data-blocks during a session.
            for ng in orphan_groups:
                if ng.users == 0:
                    bpy.data.node_groups.remove(ng)
                    logger.debug(f"Purged orphan node group: {ng.name}")
        else:
            # Create new frame
            manager_frame = nodes.new('NodeFrame')
            manager_frame.name = NODE_FRAME_NAME
            manager_frame.label = NODE_FRAME_LABEL
            manager_frame.label_size = NODE_FRAME_LABEL_SIZE

        return manager_frame

    @staticmethod
    def create_or_update_layer_group(layer: 'RasterLayerItem') -> Optional[bpy.types.NodeTree]:
        """
        Create or update a node group for a layer.

        Args:
            layer: The layer to create a group for

        Returns:
            The node group, or None if creation failed
        """
        # FIX #3: use the already-resolved `ng` variable in the inner check
        # instead of re-fetching from bpy.data.node_groups a second time.
        if layer.group_name and layer.group_name in bpy.data.node_groups:
            ng = bpy.data.node_groups[layer.group_name]
            if "Factor" in ng.interface.items_tree:
                return ng

        # Create new node group
        try:
            ng = bpy.data.node_groups.new(
                name=f"Group_{layer.name}",
                type='ShaderNodeTree'
            )
            ng.interface.new_socket(
                name=SOCKET_COLOR_OUTPUT,
                in_out='OUTPUT',
                socket_type='NodeSocketColor'
            )
            ng.interface.new_socket(
                name=SOCKET_FACTOR_OUTPUT,
                in_out='OUTPUT',
                socket_type='NodeSocketFloat'
            )
            layer.group_name = ng.name

            NodeTreeManager._setup_layer_group_nodes(ng)
            logger.debug(f"Created node group: {ng.name}")
            return ng
        except Exception as e:
            logger.error(f"Failed to create node group for layer '{layer.name}': {e}")
            return None

    @staticmethod
    def _setup_layer_group_nodes(ng: ShaderNodeTree) -> None:
        """
        Setup the internal nodes for a layer group.

        Args:
            ng: The node group to populate
        """
        nodes = ng.nodes
        links = ng.links

        # Create main texture node
        t_main = nodes.new('ShaderNodeTexImage')
        t_main.name = TEXTURE_NODE_NAME
        t_main.location = (INTERNAL_MAIN_TEXTURE_X, INTERNAL_MAIN_TEXTURE_Y)

        # Create mask texture node
        t_mask = nodes.new('ShaderNodeTexImage')
        t_mask.name = MASK_NODE_NAME
        t_mask.location = (INTERNAL_MASK_TEXTURE_X, INTERNAL_MASK_TEXTURE_Y)

        # Create opacity math node
        math = nodes.new('ShaderNodeMath')
        math.name = OPACITY_MATH_NODE_NAME
        math.operation = 'MULTIPLY'
        math.location = (INTERNAL_MATH_NODE_X, INTERNAL_MATH_NODE_Y)

        # FIX #4: initialise both inputs so new layers are fully opaque by
        # default, instead of leaving inputs[0] at 0.0 (fully transparent).
        math.inputs[0].default_value = 1.0  # mask factor — no mask → fully opaque
        math.inputs[1].default_value = 1.0  # opacity default

        # Create output node
        out = nodes.new('NodeGroupOutput')
        out.location = (INTERNAL_OUTPUT_NODE_X, INTERNAL_OUTPUT_NODE_Y)

        # Wire outputs
        links.new(t_main.outputs['Color'], out.inputs[SOCKET_COLOR_OUTPUT])
        links.new(math.outputs['Value'], out.inputs[SOCKET_FACTOR_OUTPUT])

    @staticmethod
    def update_layer_group(ng: ShaderNodeTree, layer: 'RasterLayerItem') -> None:
        """
        Update layer group node properties and image references.

        Args:
            ng: The node group to update
            layer: The layer providing updated data
        """
        if not ng:
            return

        try:
            nodes = ng.nodes
            t_main = nodes.get(TEXTURE_NODE_NAME)
            t_mask = nodes.get(MASK_NODE_NAME)
            math = nodes.get(OPACITY_MATH_NODE_NAME)

            # Update main texture
            if t_main:
                t_main.image = layer.image
                if layer.image and layer.image.source in {IMAGE_SOURCE_MOVIE, IMAGE_SOURCE_SEQUENCE}:
                    t_main.image_user.use_auto_refresh = True
                    t_main.image_user.frame_duration = layer.image.frame_duration

            # Update mask texture
            if t_mask:
                t_mask.image = layer.mask_image
                if layer.mask_image and layer.mask_image.source in {IMAGE_SOURCE_MOVIE, IMAGE_SOURCE_SEQUENCE}:
                    t_mask.image_user.use_auto_refresh = True
                    t_mask.image_user.frame_duration = layer.mask_image.frame_duration

            # FIX #1: split into two independent steps:
            #   1. always clear existing links on inputs[0]
            #   2. conditionally re-wire the mask or reset the default
            # This prevents the mask factor from getting stuck after toggling
            # use_mask off and back on.
            if math:
                math.inputs[1].default_value = layer.opacity
                links = ng.links

                # Step 1 — always clear existing connections on the mask input
                for link in list(math.inputs[0].links):
                    links.remove(link)

                # Step 2 — wire mask or restore default
                if layer.mask_image and layer.use_mask:
                    links.new(t_mask.outputs['Color'], math.inputs[0])
                else:
                    # Reset so a future mask reconnects cleanly
                    math.inputs[0].default_value = 1.0

        except Exception as e:
            logger.error(f"Failed to update layer group '{ng.name}': {e}")

    @staticmethod
    def build_composition_chain(
        obj: Object,
        visible_layers: List['RasterLayerItem'],
        nodes: bpy.types.Nodes,
        links: bpy.types.NodeLinks,
        manager_frame: Node
    ) -> Optional[ShaderNode]:
        """
        Build the composition chain (mix nodes) for all visible layers.

        Args:
            obj: The object being rendered
            visible_layers: List of visible layers to compose
            nodes: Node collection
            links: Link collection
            manager_frame: The manager frame node

        Returns:
            The final output color node, or None if no layers
        """
        if not visible_layers:
            logger.warning("No visible layers to compose")
            return None

        previous_output = None
        start_x, start_y = NODE_START_X, NODE_START_Y
        # Fix G: use a dedicated placement counter instead of the enumerate index.
        # If a layer is skipped (ng is None), the counter is NOT incremented, so
        # placed nodes stay evenly spaced with no visual gaps in the Shader Editor.
        placed = 0

        for layer in visible_layers:
            # Create or update layer group
            ng = NodeTreeManager.create_or_update_layer_group(layer)
            if not ng:
                logger.warning(f"Skipping layer '{layer.name}': node group could not be created or retrieved")
                continue

            NodeTreeManager.update_layer_group(ng, layer)

            # Create group node
            group_node = nodes.new(SHADER_TYPE_GROUP)
            group_node.node_tree = ng
            group_node.parent = manager_frame
            group_node.location = (start_x, start_y - (placed * NODE_VERTICAL_SPACING))

            if placed == 0:
                previous_output = group_node.outputs[SOCKET_COLOR_OUTPUT]
            else:
                # Create mix node
                mix_node = nodes.new('ShaderNodeMix')
                mix_node.data_type = 'RGBA'
                mix_node.blend_type = layer.blend_type
                mix_node.parent = manager_frame
                mix_node.location = (start_x + (placed * NODE_HORIZONTAL_SPACING),
                                     start_y - (placed * NODE_VERTICAL_SPACING))

                # Wire mix node
                try:
                    links.new(previous_output, mix_node.inputs[6])
                    links.new(group_node.outputs[SOCKET_COLOR_OUTPUT], mix_node.inputs[7])
                    links.new(group_node.outputs[SOCKET_FACTOR_OUTPUT], mix_node.inputs['Factor'])
                    previous_output = mix_node.outputs[2]
                except Exception as e:
                    logger.error(f"Failed to wire mix node at position {placed}: {e}")

            placed += 1

        if previous_output is None:
            logger.warning("build_composition_chain: all layer node groups failed; no output produced")
        return previous_output

    @staticmethod
    def set_active_layer_selection(obj: Object, nodes: bpy.types.Nodes) -> None:
        """
        Update node selection to highlight the active layer.

        Args:
            obj: The object with active layer info
            nodes: Node collection to update
        """
        try:
            active_idx = getattr(obj, "raster_active_index", 0)
            is_mask = getattr(obj, "raster_active_is_mask", False)

            if not (0 <= active_idx < len(obj.raster_layers)):
                return

            active_layer = obj.raster_layers[active_idx]

            # Deselect all nodes
            for n in nodes:
                n.select = False

            # Find and select the active layer's group node
            group_node = next(
                (n for n in nodes
                 if n.type == SHADER_TYPE_GROUP
                 and getattr(n, "node_tree", None)
                 and n.node_tree.name == active_layer.group_name),
                None
            )

            if group_node:
                group_node.select = True
                nodes.active = group_node

                # Handle node group internal selection
                if active_layer.group_name in bpy.data.node_groups:
                    ng = bpy.data.node_groups[active_layer.group_name]
                    for n in ng.nodes:
                        n.select = False

                    target_node = None
                    if is_mask and active_layer.mask_image:
                        target_node = ng.nodes.get(MASK_NODE_NAME)
                    else:
                        target_node = ng.nodes.get(TEXTURE_NODE_NAME)

                    if not target_node:
                        target_node = next(
                            (n for n in ng.nodes if n.type == 'TEX_IMAGE'),
                            None
                        )

                    if target_node:
                        target_node.select = True
                        ng.nodes.active = target_node
        except Exception as e:
            logger.error(f"Failed to set active layer selection: {e}")


def rebuild_node_tree(obj: Object) -> bool:
    """
    Rebuild the entire shader node tree for an object's layers.

    This is the main entry point for updating layer composition.

    Args:
        obj: The object to rebuild the node tree for

    Returns:
        True if successful, False otherwise
    """
    try:
        # Validate object and material
        if not obj or not obj.active_material:
            logger.warning(f"Invalid object or material: {obj}")
            return False

        if not obj.active_material.use_nodes:
            logger.warning("Material does not have nodes enabled")
            return False

        mat = obj.active_material
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links

        # Get Principled BSDF
        principled = NodeTreeManager.get_principled_bsdf(nodes)
        if not principled:
            return False

        # Prepare manager frame
        manager_frame = NodeTreeManager.clear_manager_frame(nodes)

        # Get visible layers
        visible_layers = [l for l in obj.raster_layers if l.is_visible]

        # Clear base color input if no layers
        if not visible_layers:
            for link in list(principled.inputs['Base Color'].links):
                links.remove(link)
            logger.info("No visible layers; cleared base color")
            return True

        # Build composition chain
        final_output = NodeTreeManager.build_composition_chain(
            obj, visible_layers, nodes, links, manager_frame
        )

        if final_output:
            # Clear existing connections
            for link in list(principled.inputs['Base Color'].links):
                links.remove(link)
            # Wire final output
            links.new(final_output, principled.inputs['Base Color'])

        # Update active layer selection
        NodeTreeManager.set_active_layer_selection(obj, nodes)

        logger.debug(f"Successfully rebuilt node tree for {obj.name}")
        return True

    except Exception as e:
        logger.error(f"Fatal error rebuilding node tree: {e}", exc_info=True)
        return False
