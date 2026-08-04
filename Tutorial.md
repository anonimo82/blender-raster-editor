# Blender Raster Editor — Typical Workflow

This tutorial walks through a common painting and compositing session from an empty Blender scene to a finished merged image.

## 1. Enable the Add-on

Install and enable Blender Raster Editor, open the 3D Viewport sidebar with `N`, and select the **Paint Layers** tab.

## 2. Create a Canvas

Click **Create Canvas**. The add-on creates a plane named `Canvas`, adds a node-based material, and initializes a background layer.

You may also use an existing mesh with an active material and **Use Nodes** enabled, but a generated canvas is the simplest starting point.

## 3. Create the Background Image

In the Background layer's image selector:

1. Click **New**.
2. Choose the desired pixel dimensions.
3. Give the image a meaningful name.
4. Confirm the creation.

Click the paint-target button at the left side of the layer row. This tells Blender Raster Editor which image Blender should treat as the active painting target.

## 4. Start Painting

Switch the object to **Texture Paint** mode. When a brush is active, the panel displays quick controls for color, radius, strength, and brush blend mode.

Paint on the canvas as usual. Save the image periodically from the Image Editor or pack it into the `.blend` file.

## 5. Build a Layer Stack

Click **Add Layer** and create or open an image for the new layer. The visible list is displayed like a conventional image editor: higher rows are composited above lower rows.

For each non-background layer you can:

- rename it;
- toggle visibility;
- move it up or down;
- duplicate or delete it;
- select it as the paint target;
- choose a blend mode;
- adjust opacity.

A duplicated layer starts with the same image and mask references but receives an independent internal node group. Create a separate image when the duplicate also needs independent pixels.

## 6. Add and Paint a Mask

Click **Add Mask** on a layer. A white grayscale image is created and selected as the active paint target.

Paint the mask in grayscale:

- white reveals the layer;
- black hides the layer;
- gray produces partial visibility.

Use the mask toggle to enable or disable its effect without deleting it. Click the mask paint-target button whenever you need to continue painting the mask.

## 7. Refine the Composition

Experiment with blend modes and opacity. The add-on updates its managed shader graph automatically. When the viewport appears not to reflect an opacity change immediately, click **Apply Opacity** to force synchronization.

Do not manually modify nodes inside the frame labelled as managed by the Layer Manager.

## 8. Resize the Canvas

Choose **Resize Canvas**, enter the new width and height, and confirm. Compatible still-image layers and masks are copied into newly sized images without stretching; the old pixels remain centered.

Movie and image-sequence sources are skipped. Downsizing can crop pixels outside the new boundaries.

## 9. Frame the Camera

Click **Frame Camera** to create or reuse an orthographic camera, align it with the canvas, and set a matching render aspect ratio. Apply object scale first when the canvas has zero dimensions.

## 10. Merge a Preview or Final Composite

Save the `.blend` file, then click **Merge**. Choose an output resolution and confirm.

The add-on temporarily uses Cycles to bake all visible layers into a new image. The original visible layers are hidden rather than deleted, and a new visible **Merged Layer** is added. This preserves an editable fallback while providing a flattened result.

At least two visible layers are required.

## 11. Save the Result

Open the merged image in Blender's Image Editor and use **Image > Save As**. Alternatively, pack it into the Blender file.

Before ending the session, check that every painted source image and mask has been saved or packed. Saving only the `.blend` file does not necessarily preserve unsaved external image pixels.
