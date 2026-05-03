import bpy

def rebuild_node_tree(obj):
    if not obj.active_material or not obj.active_material.use_nodes:
        return

    mat = obj.active_material
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    principled = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if not principled: 
        return

    manager_frame = nodes.get("LAYER_MANAGER_FRAME")
    if manager_frame:
        for node in list(nodes):
            if node.parent == manager_frame:
                nodes.remove(node)
    else:
        manager_frame = nodes.new('NodeFrame')
        manager_frame.name = "LAYER_MANAGER_FRAME"
        manager_frame.label = "⚠ MANAGED BY LAYER MANAGER - DO NOT MODIFY MANUALLY ⚠"
        manager_frame.label_size = 20

    visible_layers = [l for l in obj.raster_layers if l.is_visible]
    
    if not visible_layers:
        for link in principled.inputs['Base Color'].links: 
            links.remove(link)
        return

    previous_output = None
    start_x, start_y = -1000, 400

    for index, layer in enumerate(visible_layers):
        
        if not layer.group_name or layer.group_name not in bpy.data.node_groups or "Factor" not in bpy.data.node_groups[layer.group_name].interface.items_tree:
            ng = bpy.data.node_groups.new(name=f"Group_{layer.name}", type='ShaderNodeTree')
            ng.interface.new_socket(name="Color", in_out='OUTPUT', socket_type='NodeSocketColor')
            ng.interface.new_socket(name="Factor", in_out='OUTPUT', socket_type='NodeSocketFloat')
            layer.group_name = ng.name
            
            t_main = ng.nodes.new('ShaderNodeTexImage')
            t_main.name = "MainTexture"
            t_main.location = (-300, 100)
            
            t_mask = ng.nodes.new('ShaderNodeTexImage')
            t_mask.name = "MaskTexture"
            t_mask.location = (-300, -150)
            
            math = ng.nodes.new('ShaderNodeMath')
            math.name = "OpacityMath"
            math.operation = 'MULTIPLY'
            math.location = (-100, -100)
            
            out = ng.nodes.new('NodeGroupOutput')
            out.location = (100, 0)
            
            ng.links.new(t_main.outputs['Color'], out.inputs['Color'])
            ng.links.new(math.outputs['Value'], out.inputs['Factor'])

        ng = bpy.data.node_groups.get(layer.group_name)
        if ng:
            t_main = ng.nodes.get("MainTexture")
            t_mask = ng.nodes.get("MaskTexture")
            math = ng.nodes.get("OpacityMath")
            
            if t_main: 
                t_main.image = layer.image
                if layer.image and layer.image.source in {'MOVIE', 'SEQUENCE'}:
                    t_main.image_user.use_auto_refresh = True
                    t_main.image_user.frame_duration = layer.image.frame_duration

            if t_mask: 
                t_mask.image = layer.mask_image
                if layer.mask_image and layer.mask_image.source in {'MOVIE', 'SEQUENCE'}:
                    t_mask.image_user.use_auto_refresh = True
                    t_mask.image_user.frame_duration = layer.mask_image.frame_duration
            
            if math:
                math.inputs[1].default_value = layer.opacity
                if layer.mask_image and layer.use_mask:
                    ng.links.new(t_mask.outputs['Color'], math.inputs[0])
                else:
                    for link in math.inputs[0].links: 
                        ng.links.remove(link)
                    math.inputs[0].default_value = 1.0

        group_node = nodes.new('ShaderNodeGroup')
        group_node.node_tree = ng
        group_node.parent = manager_frame
        group_node.location = (start_x, start_y - (index * 250))
        
        if index == 0:
            previous_output = group_node.outputs['Color']
        else:
            mix_node = nodes.new('ShaderNodeMix')
            mix_node.data_type = 'RGBA'
            mix_node.blend_type = layer.blend_type
            mix_node.parent = manager_frame
            mix_node.location = (start_x + (index * 250), start_y - (index * 250))
            
            links.new(previous_output, mix_node.inputs[6])
            links.new(group_node.outputs['Color'], mix_node.inputs[7])
            links.new(group_node.outputs['Factor'], mix_node.inputs['Factor'])
            
            previous_output = mix_node.outputs[2]

    links.new(previous_output, principled.inputs['Base Color'])

    active_idx = getattr(obj, "raster_active_index", 0)
    is_mask = getattr(obj, "raster_active_is_mask", False)
    
    if 0 <= active_idx < len(obj.raster_layers):
        active_layer = obj.raster_layers[active_idx]
        for n in nodes: n.select = False
            
        group_node = next((n for n in nodes if n.type == 'GROUP' and getattr(n, "node_tree", None) and n.node_tree.name == active_layer.group_name), None)
        
        if group_node:
            group_node.select = True
            nodes.active = group_node
            
            if active_layer.group_name in bpy.data.node_groups:
                ng = bpy.data.node_groups[active_layer.group_name]
                for n in ng.nodes: n.select = False
                
                target_node = ng.nodes.get("MaskTexture") if (is_mask and active_layer.mask_image) else ng.nodes.get("MainTexture")
                if not target_node:
                    target_node = next((n for n in ng.nodes if n.type == 'TEX_IMAGE'), None)
                    
                if target_node:
                    target_node.select = True
                    ng.nodes.active = target_node