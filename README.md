# Blender Raster Editor

**Blender Raster Editor** is a powerful add-on that introduces a non-destructive, layer-based workflow directly into Blender's 3D Viewport. 

Designed specifically for hand-painting textures, annotating scenes, and rotoscoping video files, this tool generates a smart, managed material node tree behind the scenes. This gives you Photoshop-like layer control while maintaining all of Blender's native 3D and painting capabilities.

## 🚀 Key Features

* **Non-Destructive Layer System:** Create, duplicate, reorder, and remove layers seamlessly. The add-on dynamically builds the underlying shader graph for you.
* **Industry-Standard Blending Modes:** Full support for 19 blend modes including Multiply, Overlay, Color Burn, Dodge, Screen, and more, alongside per-layer Opacity sliders.
* **Layer Masks:** Easily add black-and-white mask images to any layer to hide or reveal painted areas non-destructively.
* **Video & Sequence Rotoscoping:** Load `.mp4` files or image sequences directly into a layer. The add-on automatically handles frame refresh rates, allowing you to paint over or annotate playing videos.
* **Smart Baking (Merge Visible):** Flatten your entire layer stack into a single, clean texture image with a single click using an automated Cycles-based baking process.
* **Targeted Painting:** Instantly switch your active painting target between the base layer image and its associated mask using intuitive UI toggles.
* **Canvas Utilities:** Automatically frame a perfect 2D Orthographic Camera around your canvas, and intelligently resize all layers (using Python's `numpy`) by adding empty space without stretching your artwork.

## 📋 Requirements

* **Blender Version:** 4.0.0 or higher.
* **Dependencies:** Python `numpy` module (included in standard Blender installations).

## 🛠️ Installation

1. Click on `Code` > `Download ZIP` to download the repository.
2. Open Blender and navigate to **Edit** > **Preferences** > **Add-ons**.
3. Click **Install...**, locate your downloaded `.zip` file, and click **Install Add-on**.
4. Enable the add-on by checking the box next to **Paint: Blender Raster Editor**.
5. In the 3D Viewport, press **N** to open the Sidebar and select the **Paint Layers** tab.

## 📖 How to Use

### Setup & Organization
1.  **Initialize Canvas:** Click **Create Canvas** to generate a pre-configured 3D plane and the underlying managed material.
2.  **Add Layers:** Click **Add Layer** to start stacking textures. Use the folder icon to load existing images or videos, or click the "New" icon to create a blank texture for hand-painting.
3.  **Adjust Layers:** Use the arrows to move layers up or down, the duplicate button to copy them, and adjust the **Blend Mode** and **Opacity** from the dropdowns below each layer name.

### Painting & Masking
1.  **Select Target:** Click the **Brush icon** next to a layer's name to set it as the active paint target.
2.  **Using Masks:** Click **Add Mask** on a layer. To paint on the mask (black hides, white reveals), click the Brush icon on the *mask row*.
3.  **Paint Settings:** At the bottom of the panel, when in *Texture Paint* mode, you'll find quick access to your brush Radius, Strength, and Color.

### Finalizing
* **Apply Opacity:** If opacity changes don't immediately update in the viewport due to Blender cache, click **Apply Opacity** to force a refresh.
* **Merge Visible:** Once you are happy with your artwork, click **Merge** to bake all visible layers into a new, flattened image. *(Note: This process uses the Cycles render engine).*

## ⚠️ Known Limitations

Due to Blender's underlying engine and architecture, keep the following constraints in mind:

* **Baking Performance:** The *Merge Visible* operation uses the Cycles rendering engine to bake the texture. Merging many high-resolution layers may take several seconds and temporarily freeze the interface.
* **Opacity Update Lag:** Slider adjustments for layer Opacity may sometimes require triggering the *Apply Opacity* button or moving the viewport camera to force a visual update in the EEVEE shader graph.
* **Node Tree Management:** The material's Shader Editor node tree is fully managed inside a warning frame (`LAYER_MANAGER_FRAME`). Manual edits to these nodes will be overwritten or cause the system to break.
* **Viewport Only:** The layer system operates purely through shader nodes. You cannot apply these layered edits to standard images outside the 3D viewport without performing a "Merge Visible" bake first.

## 📄 License

This program is free software: you can redistribute it and/or modify it under the terms of the **GNU General Public License v3.0 (GPL-3.0)**.
See the [LICENSE](LICENSE) file for more details.