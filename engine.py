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

    # 1. Pulisce la vecchia cascata
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

    # 2. FILTRA SOLO I LAYER VISIBILI (Questo crea il bypass automatico!)
    visible_layers = [layer for layer in obj.raster_layers if layer.is_visible]
    
    if not visible_layers:
        # Se tutti i layer sono nascosti, scollega il Base Color per evitare errori
        for link in principled.inputs['Base Color'].links:
            links.remove(link)
        return

    previous_output = None
    start_x = -1000
    start_y = 400

    # 3. Ricostruisce la cascata usando solo i layer attivi
    for index, layer in enumerate(visible_layers):
        
        # Crea il Node Group e un nodo Image al suo interno se non esiste
        if not layer.group_name or layer.group_name not in bpy.data.node_groups:
            ng = bpy.data.node_groups.new(name=f"Group_{layer.name}", type='ShaderNodeTree')
            ng.interface.new_socket(name="Color", in_out='OUTPUT', socket_type='NodeSocketColor')
            layer.group_name = ng.name
            
            # Aggiunge il nodo texture base nel gruppo
            tex_node = ng.nodes.new('ShaderNodeTexImage')
            tex_node.location = (-300, 0)
            out_node = ng.nodes.new('NodeGroupOutput')
            out_node.location = (0, 0)
            ng.links.new(tex_node.outputs['Color'], out_node.inputs['Color'])

        # Aggiorna sempre l'immagine nel nodo con quella scelta nell'interfaccia UI
        ng = bpy.data.node_groups.get(layer.group_name)
        if ng:
            tex_node = next((n for n in ng.nodes if n.type == 'TEX_IMAGE'), None)
            if tex_node:
                tex_node.image = layer.image

        # Richiama il gruppo nell'albero principale
        group_node = nodes.new('ShaderNodeGroup')
        group_node.node_tree = bpy.data.node_groups[layer.group_name]
        group_node.parent = manager_frame
        group_node.location = (start_x, start_y - (index * 250))
        
        if index == 0:
            previous_output = group_node.outputs[0]
        else:
            mix_node = nodes.new('ShaderNodeMix')
            mix_node.data_type = 'RGBA'
            mix_node.blend_type = layer.blend_type
            mix_node.inputs['Factor'].default_value = layer.opacity
            mix_node.parent = manager_frame
            mix_node.location = (start_x + (index * 250), start_y - (index * 250))
            
            links.new(previous_output, mix_node.inputs[6]) # A
            links.new(group_node.outputs[0], mix_node.inputs[7]) # B
            
            previous_output = mix_node.outputs[2]

    # Collega l'uscita finale
    links.new(previous_output, principled.inputs['Base Color'])

    # ... [vecchio codice: links.new(previous_output, principled.inputs['Base Color'])] ...

    # =========================================================
    # NUOVO BLOCCO: IMPOSTA IL NODO ATTIVO PER LA PITTURA
    # =========================================================
    active_idx = obj.raster_active_index
    if 0 <= active_idx < len(obj.raster_layers):
        active_layer = obj.raster_layers[active_idx]
        
        # 1. Deseleziona tutti i nodi nell'albero principale
        for n in nodes: 
            n.select = False
            
        # 2. Trova il Node Group corrispondente al layer attivo
        group_node = next((n for n in nodes if n.type == 'GROUP' and getattr(n, "node_tree", None) and n.node_tree.name == active_layer.group_name), None)
        
        if group_node:
            group_node.select = True
            nodes.active = group_node
            
        # 3. Entra nel Group Node e seleziona l'Image Texture nativa
        if active_layer.group_name in bpy.data.node_groups:
            ng = bpy.data.node_groups[active_layer.group_name]
            
            # Deseleziona tutto dentro il gruppo
            for n in ng.nodes: 
                n.select = False
                
            # Trova l'immagine e rendila "Active"
            tex_node = next((n for n in ng.nodes if n.type == 'TEX_IMAGE'), None)
            if tex_node:
                tex_node.select = True
                ng.nodes.active = tex_node