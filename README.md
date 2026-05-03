# Blender Raster Editor (v1.0)

A non-destructive layer management system for hand-painting and rotoscoping directly inside Blender's 3D Viewport.

## Features
- **Non-Destructive Workflow**: Manage layers without permanently altering your images.
- **Opacity & 19 Blend Modes**: Full control over layer transparency and industry-standard blending (Multiply, Overlay, Color Burn, etc.).
- **Layer Masks**: Add white/black masks to non-destructively hide or reveal portions of your layers.
- **Video & Image Sequences**: Load videos as layers for rotoscoping and VFX annotations with automatic refresh.
- **Smart Baking**: Merge visible layers into a single new image with one click.
- **Brush Integration**: Access native brush settings (Radius, Strength, Color, Stroke) directly from the layer panel.
- **Targeted Painting**: Toggle between painting on the main image or the mask using the brush icon buttons.

## Installation
1. Download or copy the files into a folder named `blender-raster-editor`.
2. Zip the folder.
3. In Blender, go to **Edit > Preferences > Add-ons > Install**.
4. Select the `.zip` file and enable **Blender Raster Editor**.

## How to Use
1. **Setup**: In the 3D Viewport, press `N` to open the sidebar and select the **Paint Layers** tab.
2. **Create Canvas**: Click **Create Canvas** to generate a plane with a managed material.
3. **Add Layers**: Use the **Add Layer** button to stack new textures. 
4. **Painting**: 
   - Click the **Brush icon** next to a layer to set it as the target for painting.
   - Click **Add Mask** to create a mask for a layer. Click the brush icon on the mask row to paint transparency (black hides, white shows).
5. **Video Support**: Click the folder icon in the layer image selector to load a `.mp4` or movie file. Play the timeline to see it animate.
6. **Merging**: Use the **Merge** button to bake all currently visible layers into a new, flattened image.

## File Structure
- `__init__.py`: Add-on registration and metadata.
- `properties.py`: Data structures for layers and global properties.
- `engine.py`: The node-tree generator and logic core.
- `operators.py`: Functionality for adding, moving, and merging layers.
- `ui.py`: The user interface for the Sidebar panel.
