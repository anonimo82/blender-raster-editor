import bpy

def rebuild_node_tree(obj):
    if not obj.active_material or not obj.active_material.use_nodes:
        return

    mat = obj.active_material
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Find the Principled BSDF node (the final target)
    principled = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if not principled:
        return

    # 1. Clean the old system (everything inside the manager frame)
    manager_frame = nodes.get("LAYER_MANAGER_FRAME")
    if manager_frame:
        for node in list(nodes):
            if node.parent == manager_frame:
                nodes.remove(node)
    else:
        # Create the protection Frame if it doesn't exist
        manager_frame = nodes.new('NodeFrame')
        manager_frame.name = "LAYER_MANAGER_FRAME"
        manager_frame.label = "⚠ MANAGED BY LAYER MANAGER - DO NOT MODIFY MANUALLY ⚠"
        manager_frame.label_size = 20

    layers = obj.raster_layers
    if len(layers) == 0:
        return

    previous_output = None
    start_x = -1000
    start_y = 400

    # 2. Rebuild the linear cascade
    for index, layer in enumerate(layers):
        # Ensure a Node Group exists for this layer
        if not layer.group_name or layer.group_name not in bpy.data.node_groups:
            ng = bpy.data.node_groups.new(name=f"Group_{layer.name}", type='ShaderNodeTree')
            ng.interface.new_socket(name="Color", in_out='OUTPUT', socket_type='NodeSocketColor')
            layer.group_name = ng.name
        
        # Create the node that calls the Node Group
        group_node = nodes.new('ShaderNodeGroup')
        group_node.node_tree = bpy.data.node_groups[layer.group_name]
        group_node.parent = manager_frame
        group_node.location = (start_x, start_y - (index * 250)) # Vertical Pretty Printing
        
        if index == 0:
            # The first layer is the base
            previous_output = group_node.outputs[0]
        else:
            # Create the Mix node for subsequent layers
            mix_node = nodes.new('ShaderNodeMix')
            mix_node.data_type = 'RGBA'
            mix_node.blend_type = layer.blend_type
            mix_node.inputs['Factor'].default_value = layer.opacity
            mix_node.parent = manager_frame
            
            # Cascade Pretty Printing (shifted right and down)
            mix_node.location = (start_x + (index * 250), start_y - (index * 250))
            
            # Connect the cascade: (Base -> A), (Current Layer -> B)
            links.new(previous_output, mix_node.inputs[6]) # Input A
            links.new(group_node.outputs[0], mix_node.inputs[7]) # Input B
            
            previous_output = mix_node.outputs[2] # Mix Result

    # 3. Connect the final result to the Principled BSDF
    links.new(previous_output, principled.inputs['Base Color'])