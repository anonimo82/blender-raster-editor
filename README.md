# Blender Raster Editor — Complete Tutorial

> **Add-on version:** 1.1.0 | **Blender:** 4.0.0+ | **License:** GNU GPL v3.0

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Requirements & Installation](#2-requirements--installation)
3. [UI Overview](#3-ui-overview)
4. [Getting Started — Core Workflow](#4-getting-started--core-workflow)
   - [4.1 Creating a Canvas](#41-creating-a-canvas)
   - [4.2 Adding and Configuring Layers](#42-adding-and-configuring-layers)
   - [4.3 The Layer Interface — Anatomy of a Layer Row](#43-the-layer-interface--anatomy-of-a-layer-row)
   - [4.4 Painting on a Layer](#44-painting-on-a-layer)
   - [4.5 Using Layer Masks](#45-using-layer-masks)
   - [4.6 Blend Modes and Opacity](#46-blend-modes-and-opacity)
   - [4.7 Reordering and Duplicating Layers](#47-reordering-and-duplicating-layers)
   - [4.8 Video Rotoscoping](#48-video-rotoscoping)
5. [Utilities](#5-utilities)
   - [5.1 Apply Opacity](#51-apply-opacity)
   - [5.2 Merge Visible (Bake)](#52-merge-visible-bake)
   - [5.3 Resize Canvas](#53-resize-canvas)
   - [5.4 Frame Camera](#54-frame-camera)
6. [Known Limitations](#6-known-limitations)
7. [Blend Mode Reference](#7-blend-mode-reference)
8. [Developer Reference](#8-developer-reference)
9. [Quick-Start Cheat Sheet](#9-quick-start-cheat-sheet)

---

## 1. Introduction

**Blender Raster Editor** is an open-source Blender add-on that introduces a non-destructive, Photoshop-like layer workflow directly inside the 3D Viewport. Instead of relying on external image editors, you can stack textures, apply blend modes and masks, and composite them in real time — all managed by a smart shader node tree that the add-on builds and maintains automatically behind the scenes.

**Key capabilities:**

- Non-destructive layer stack with per-layer blend modes and opacity
- 19 blend modes (Multiply, Overlay, Screen, Color Burn, Dodge, and more)
- Per-layer black-and-white masks for non-destructive hiding/revealing of pixel areas
- Video and image-sequence rotoscoping with automatic frame refresh
- One-click **Merge Visible** bake using Blender's Cycles engine
- Canvas resize utility — adds empty space around existing artwork without any stretching
- Auto-framing orthographic camera setup for clean render output

---

## 2. Requirements & Installation

### 2.1 Requirements

| Item | Requirement |
|---|---|
| Blender version | 4.0.0 or higher |
| Python module | `numpy` (bundled with Blender — no action needed) |
| OS | Windows, macOS, Linux |
| Render engine (for Merge Visible) | Cycles (built-in) |

### 2.2 Installation

1. Download the repository as a ZIP file (**Code → Download ZIP** on GitHub).
2. Open Blender and go to **Edit → Preferences → Add-ons**.
3. Click **Install…**, locate the downloaded `.zip`, and confirm.
4. Enable the add-on by ticking the checkbox next to **Paint: Blender Raster Editor**.
5. Press **N** in the 3D Viewport to open the Sidebar, then select the **Paint Layers** tab.

> **Note:** The add-on registers three modules in order: Properties → Operators → UI. Unregistration happens in reverse order. If Blender reports an error during enable, open the **System Console** (Window → Toggle System Console on Windows, or launch Blender from a terminal on macOS/Linux) to read the detailed log output.

---

## 3. UI Overview

All controls live in the **Paint Layers** sidebar tab (N-panel → Paint Layers). The panel is organised into four sections:

| Section | Purpose |
|---|---|
| **Canvas** | Create a new canvas plane with a managed material |
| **Layer Management** | Add layers; each layer row shows its image, controls, blend mode, and opacity |
| **Utilities** | Apply Opacity, Merge Visible, Resize Canvas, Frame Camera |
| **Paint Settings** | Quick brush controls — visible only when in Texture Paint mode |

---

## 4. Getting Started — Core Workflow

This section walks you through every step of a typical painting session, from creating a blank canvas to outputting a final merged image.

---

### 4.1 Creating a Canvas

**Where:** Sidebar → **Create Canvas** button (top of the Paint Layers panel).

Clicking **Create Canvas** performs the following automatically:

- Adds a 2 × 2 world-unit plane to the scene, named `Canvas`
- Creates a new node-based material called `CanvasMaterial` and attaches it to the plane
- Adds a default `Background` layer to the layer stack
- Builds the initial shader node tree, wiring a Principled BSDF to the layer composition group

> **Working with an existing object:** You do not have to use the Create Canvas button. You can select any mesh that already has a node-based material — the add-on attaches its layer data to whichever object is currently active. Just make sure **Use Nodes** is enabled on the material (Properties → Material → Surface → Use Nodes).

> **Duplicate name warning:** If an object called `Canvas` already exists, Blender will silently rename the new one (e.g. `Canvas.001`). The add-on will warn you in the viewport header and in the System Console.

---

### 4.2 Adding and Configuring Layers

**Where:** Sidebar → **Add Layer** button.

Each click adds a new layer entry at the top of the visible stack (highest compositing priority). Layers are displayed **top-to-bottom** in the panel, corresponding to **highest-to-lowest** in the actual blend order — the same convention used in Photoshop and other raster editors.

After adding a layer you typically want to:

1. Give it a meaningful name (click the name field in the layer row and type).
2. Assign an image — either click **New** to generate a blank texture, or **Open** (folder icon) to load an existing file from disk.
3. Set a blend mode and opacity if this is not the base layer.

> **Tip:** The very first layer (index 0, labelled `Background` by default) does not display blend mode or opacity controls — it is always fully opaque and acts as the base of the composition. All layers above it blend on top of it.

---

### 4.3 The Layer Interface — Anatomy of a Layer Row

Each layer is displayed as a box containing several controls. Here is what every element does, reading left to right:

```
[ ● ] [ 👁 ] [ Layer Name _______ ] [ ▲ ] [ ▼ ] [ ⎘ ] [ ✕ ]
[ Image selector / template_ID                              ]
[ Mask row (see Section 4.5)                                ]
[ Blend Mode dropdown                                       ]
[ Opacity ────────────────────────────────────── 1.00       ]
```

| Control | Icon | Description |
|---|---|---|
| **Paint Target** | Brush / radio button | Marks this layer (or its mask) as the active paint destination. A filled brush icon means this layer is currently selected for painting. Click it before switching to Texture Paint mode. |
| **Visibility** | Eye open / Eye closed | Toggles the layer on or off in the composition. Hidden layers are completely excluded from the shader output and from Merge Visible baking. |
| **Name field** | — | Editable text box. Double-click or click once and type to rename the layer. |
| **Move Up ▲** | Triangle up | Moves the layer one position higher in the stack (increases compositing priority). |
| **Move Down ▼** | Triangle down | Moves the layer one position lower in the stack (decreases compositing priority). |
| **Duplicate ⎘** | Copy icon | Creates an independent copy of the layer directly below the original, sharing the same image and mask references but with its own node group. |
| **Delete ✕** | X button | Permanently removes the layer from the stack. This action is undoable (Ctrl+Z). |
| **Image selector** | — | Blender's built-in `template_ID` widget. Use **New** to create a blank texture at a chosen resolution, or the **folder icon** to open an existing file (`.png`, `.jpg`, `.exr`, `.mp4`, image sequences, etc.). |
| **Blend Mode** | — | Dropdown with 19 blending algorithms. Only visible on layers above index 0. See [Section 7](#7-blend-mode-reference) for full descriptions. |
| **Opacity slider** | — | Sets per-layer transparency from 0.0 (fully transparent) to 1.0 (fully opaque). Only visible on layers above index 0. If the viewport does not update immediately, click **Apply Opacity** in the Utilities section. |

---

### 4.4 Painting on a Layer

Follow these steps every time you want to paint on a specific layer:

1. **Select the paint target.** Click the **Brush icon** (paint target button) on the desired layer row. The icon fills in to confirm the selection.
2. **Switch to Texture Paint mode.** Press **Tab** or use the mode dropdown in the viewport header and select **Texture Paint**.
3. **Assign an image if needed.** If the layer has no image yet, the viewport will be grey. Click **New** in the image selector on that layer row, choose a resolution (e.g. 2048 × 2048), and confirm. The canvas will become paintable.
4. **Paint.** Use Blender's standard brush tools. The **Paint Settings** section at the bottom of the panel provides quick access to brush **Color**, **Radius**, **Strength**, and **Blend Mode** without having to open the Tool shelf.
5. **Save your work.** Blender does not auto-save painted images. Go to **Image Editor → Image → Save As** (or pack images into the `.blend` file via **Image → Pack**) to avoid losing paint data.

> ⚠️ **Important:** Always confirm the correct layer is selected before painting. The add-on keeps Blender's active image node in sync with the paint target whenever you click the Brush icon, but switching objects, undoing, or manually selecting nodes in the Shader Editor can desync this. If your strokes appear to paint on the wrong layer, click the Brush icon again on the intended layer.

---

### 4.5 Using Layer Masks

Masks let you non-destructively hide or reveal parts of a layer using a greyscale image:

- **White pixels** → fully reveal the layer content beneath the mask
- **Black pixels** → fully hide the layer content
- **Grey pixels** → partial transparency proportional to the grey value

#### Adding a Mask

Click **Add Mask** on any layer row. The add-on will:

- Create a new 1024 × 1024 white image (fully revealing by default)
- Assign it as the mask for that layer
- Automatically enable the mask and set it as the active paint target

#### The Mask Row

Once a mask exists, the layer row expands to show a **mask sub-row** below the image selector:

```
[ ● ] [ 🛡 ] [ Mask image selector ______________ ] [ ✕ ]
```

| Control | Description |
|---|---|
| **Mask Paint Target** (brush icon) | Sets the mask as the active paint destination. Click this before painting in greyscale to edit the mask. |
| **Mask Enable Toggle** (shield icon) | Toggles the mask on/off without deleting it. Useful for quickly comparing masked vs unmasked states. |
| **Mask Image Selector** | Lets you swap the mask for any other image. You can load an external file as a mask (e.g. an alpha channel exported from another tool). |
| **Remove Mask ✕** | Deletes the mask association from the layer. The underlying mask image data-block is not deleted from the `.blend` file, only unlinked. |

#### Painting a Mask

1. Click the **Brush icon on the mask row** (not the main layer row) to target the mask.
2. Switch to **Texture Paint** mode.
3. Set your brush colour to **black** to hide areas, **white** to restore them, or any grey for partial transparency.
4. Paint as normal. The mask effect is visible in real time in the viewport.

> **Tip:** You can use the **Erase** brush blend mode to paint back to white (fully revealed) quickly.

---

### 4.6 Blend Modes and Opacity

**Blend Mode** controls how a layer's pixels are mathematically combined with the layers beneath it. **Opacity** scales the layer's overall contribution before blending.

Both controls appear on every layer except the background (index 0). The blend mode dropdown is located below the image selector; the opacity slider is directly below it.

Changes to blend mode take effect immediately. Changes to opacity may occasionally lag in EEVEE's viewport due to shader cache behaviour — if you see no change after moving the slider, click **Apply Opacity** in the Utilities section (see [Section 5.1](#51-apply-opacity)).

For a full description of every available blend mode, see [Section 7](#7-blend-mode-reference).

---

### 4.7 Reordering and Duplicating Layers

**Reordering** is done with the **▲** and **▼** buttons on each layer row. Moving a layer up increases its priority in the blend stack (it composites on top of more layers). Moving it down decreases priority.

**Duplicating** a layer via the **⎘** (copy) icon creates an independent copy inserted directly below the original. The duplicate shares the same image and mask data-blocks as the source but has its own internal node group — modifying one does not affect the other.

> **Note:** If you need a fully independent copy with its own pixel data (so you can paint on the duplicate without affecting the original), duplicate the layer and then create a new image from within the image selector on the duplicate.

---

### 4.8 Video Rotoscoping

The add-on handles `.mp4` video files and image sequences natively, making it well-suited for frame-by-frame rotoscoping work:

- In the image selector on any layer, click the **folder icon** and load an `.mp4` file or the first frame of an image sequence (e.g. `frame_0001.png`).
- The add-on automatically enables `Auto Refresh` on the image user and syncs `frame_duration` so the texture updates as you scrub or play the timeline.
- To paint or annotate on top of a video layer, add a new **blank** layer above it and paint on that layer. The video layer below it remains unmodified.

> **Limitation:** Video and image-sequence layers cannot be resized via the Resize Canvas utility. Resize the source footage externally if needed before loading it.

---

## 5. Utilities

The **Utilities** section sits at the bottom of the Paint Layers panel and provides four tools for layer management, baking, and viewport setup.

---

### 5.1 Apply Opacity

**Button:** Utilities → **Apply Opacity** (file refresh icon)

**When to use it:** Due to the way EEVEE caches shader node data, moving the Opacity slider on a layer may not visually update the viewport immediately. Clicking **Apply Opacity** forces the add-on to re-synchronise the entire node tree, flushing any cached values and making all opacity changes visible.

This button is also useful after any operation that modifies layer data programmatically (e.g. via a script) and you want to guarantee the viewport reflects the current state.

---

### 5.2 Merge Visible (Bake)

**Button:** Utilities → **Merge** (or **Merge Visible**)

**What it does:** Bakes the entire visible layer stack into a single flat image using Blender's Cycles render engine. The result is placed into a new layer at the top of the stack, and the original visible layers are hidden (not deleted).

**Step-by-step:**

1. Make sure at least **2 layers are visible** in the stack. (Merge Visible requires a minimum of 2 visible layers to be meaningful.)
2. Click **Merge Visible**.
3. A resolution dialog appears. Enter the desired output resolution (default is 1024 × 1024; maximum is 4096 × 4096).
4. Click **OK**. The add-on will:
   - Temporarily switch the render engine to Cycles
   - Create a new blank image at the chosen resolution
   - Insert a temporary bake target node into the material
   - Run a Diffuse bake pass (`bpy.ops.object.bake`)
   - Remove the temporary node
   - Hide all previously visible layers
   - Add a **Merged Layer** at the top of the stack containing the baked result
   - Restore the original render engine

> ⚠️ **Warning:** Baking freezes the Blender interface for several seconds — longer at high resolutions or on complex scenes. **Save your `.blend` file before using Merge Visible.** The undo history (Ctrl+Z) can recover the hidden layers, but the baked image data will be lost if Blender crashes before you save.

> **Tip:** For iteration work, bake at 512 × 512 or 1024 × 1024 to keep bake times short. Only bake at full resolution (2048 × 2048 or 4096 × 4096) for final output.

---

### 5.3 Resize Canvas

**Button:** Utilities → **Resize Canvas** (fullscreen icon)

**What it does:** Changes the pixel dimensions of all raster layers on the canvas, adding empty (transparent/black) space around the existing artwork to fill the new size. No stretching occurs — existing pixel data is centred in the new canvas and copied without resampling.

**Step-by-step:**

1. Click **Resize Canvas**.
2. The dialog pre-fills with the current dimensions of the first raster layer it finds. Adjust **Width** and **Height** to your target resolution.
3. Click **OK**. The add-on will:
   - Read each layer's pixel data into a NumPy array
   - Create a new blank canvas at the target size
   - Centre the old content and copy it across (with bounds-checking to handle both upscaling and downscaling)
   - Replace each layer's image reference with the new resized image
   - Adjust the Canvas object's world-space dimensions to maintain the correct aspect ratio

**What gets skipped:** Video (`.mp4`) and image-sequence layers cannot be resized this way — they are automatically skipped. The add-on will warn you if any layer could not be resized.

> **Note on downscaling:** If the new canvas is smaller than the original artwork, the content is cropped from the centre outward — not scaled down. Use Blender's Image Editor (**Image → Scale Image**) before loading your files if you need a proper downscale with resampling.

---

### 5.4 Frame Camera

**Button:** Utilities → **Frame Camera** (camera icon)

**What it does:** Sets up a perfectly aligned orthographic camera that frames the canvas exactly, ready for rendering.

Clicking **Frame Camera** will:

- Find an existing camera in the scene, or create a new orthographic camera named `Canvas_Camera` if none exists
- Position the camera directly above the canvas centre, pointing straight down
- Set `ortho_scale` to match the canvas world-space dimensions (so the render fills the frame with no border)
- Set the render resolution to **1920 px** on the longest axis, with the shorter axis scaled proportionally to maintain the correct aspect ratio
- Switch the active 3D Viewport to **Camera** perspective so you immediately see the framed result

**Common use cases:**

- Setting up the final render after all layers are painted
- Checking what the render will look like at any point during painting
- Re-framing after using **Resize Canvas** (which changes the canvas aspect ratio)

> ⚠️ **Warning:** If the canvas object has a zeroed scale (e.g. you just created it and pressed S then 0), Frame Camera will report an error: *"Canvas has zero dimensions — apply scale (Ctrl+A) before framing the camera."* Press **Ctrl+A → Apply → Scale** in the viewport first, then try again.

---

## 6. Known Limitations

| Limitation | Details & Workaround |
|---|---|
| **Baking performance** | Merge Visible uses Cycles and freezes the UI. Use lower resolutions during iteration; merge at full resolution for final output only. |
| **Opacity update lag** | EEVEE's shader cache may delay opacity changes. Click **Apply Opacity** to force a refresh. |
| **Node tree protection** | The managed node frame (`LAYER_MANAGER_FRAME`) must not be edited manually in the Shader Editor — the add-on will overwrite any manual changes on the next rebuild. Always use the panel UI. |
| **Viewport only** | Layered edits live in the shader node tree and are visible in the 3D Viewport. To export a standalone image file, always run **Merge Visible** first, then save the resulting image from the Image Editor. |
| **Resize & video layers** | Video (`.mp4`) and image-sequence layers are skipped by Resize Canvas. Resize source files externally if needed. |
| **Resize crops, doesn't scale** | Downscaling with Resize Canvas crops from the centre rather than scaling down. Use Blender's Image Editor to scale images before loading them. |
| **Minimum 2 layers for Merge** | Merge Visible requires at least 2 visible layers. If you only have one, duplicate it or add a blank layer before merging. |
| **Camera zero-scale guard** | Frame Camera will fail if the canvas object's scale is zeroed. Apply scale with Ctrl+A first. |

---

## 7. Blend Mode Reference

| Mode | Description |
|---|---|
| **Mix** | Standard alpha-compositing blend (default). Blends linearly between the base and blend layers using the layer opacity as the factor. |
| **Darken** | Compares pixels and keeps the darker value at each channel. Bright areas of the blend layer have no effect. |
| **Multiply** | Multiplies pixel values together. Always darkens or keeps the same; never lightens. Great for shadows and colour filters. |
| **Color Burn** | Darkens the base by increasing contrast to reflect the blend colour. Produces strong, saturated darkening. |
| **Lighten** | Compares pixels and keeps the lighter value at each channel. Dark areas of the blend layer have no effect. |
| **Screen** | Inverts both layers, multiplies, then inverts the result. Always lightens or keeps the same; never darkens. |
| **Color Dodge** | Brightens the base layer by decreasing contrast to reflect the blend layer's colour. Produces bright, washed-out highlights. |
| **Add** | Adds colour values directly. Quickly clips to white (1.0). Useful for glow and light-emission effects. |
| **Overlay** | Combines Multiply and Screen depending on the base layer brightness: darkens darks and lightens lights, increasing contrast overall. |
| **Soft Light** | A gentler variant of Overlay. Subtle contrast boost without clipping. Good for dodge/burn-style shading. |
| **Linear Light** | Combines Linear Burn and Linear Dodge. Very strong contrast effect — use with low opacity. |
| **Difference** | Subtracts one layer from the other and takes the absolute value. Black where layers are identical; inverted colour where they differ. Useful for alignment checks. |
| **Exclusion** | Similar to Difference but produces lower contrast. Overlapping areas tend towards grey rather than black. |
| **Subtract** | Subtracts the blend layer from the base, clamping at black. Useful for darkening specific colour channels. |
| **Divide** | Divides the base by the blend layer. Brightens the result. White in the blend layer leaves the base unchanged. |
| **Hue** | Takes the **hue** from the blend layer and the **saturation + value** from the base. Changes colour tone without altering brightness. |
| **Saturation** | Takes the **saturation** from the blend layer and the **hue + value** from the base. Useful for desaturating specific areas. |
| **Color** | Takes **hue + saturation** from the blend layer and the **value** from the base. Classic "colorize" effect — applies colour without changing luminosity. |
| **Value** | Takes the **brightness (value)** from the blend layer and the **hue + saturation** from the base. Useful for swapping lightness maps. |

---

## 8. Developer Reference

### 8.1 Module Architecture

| Module | Responsibility |
|---|---|
| `__init__.py` | Add-on entry point. Registers modules in correct dependency order; configures the package-level logger. |
| `constants.py` | Single source of truth for all magic strings, numeric defaults, and node identifiers. Edit this file to change defaults globally. |
| `properties.py` | Custom Blender properties (`RasterLayerItem`, object-level collections). Defines the `_auto_update_tree` callback fired on every property change. |
| `engine.py` | `NodeTreeManager` class and `rebuild_node_tree()` function. All shader node construction, linking, and synchronisation lives here. |
| `operators.py` | `bpy.types.Operator` subclasses for every user action. `BaseOperator` provides shared validation helpers. |
| `ui.py` | `VIEW3D_PT_raster_layers` panel and all static drawing helpers. |

### 8.2 Data Flow

```
User action in the UI panel
  → Operator.execute()
  → modifies obj.raster_layers
  → calls rebuild_node_tree(obj)
  → NodeTreeManager rebuilds the shader graph
  → Blender's viewport updates
```

Property changes (`image`, `opacity`, `blend_type`, `is_visible`, `use_mask`) also trigger the `_auto_update_tree` callback automatically, so the node tree stays in sync without requiring an explicit operator call.

### 8.3 Extending the Add-on

#### Adding a New Operator

1. Subclass `BaseOperator` in `operators.py`.
2. Implement `execute(self, context)`. Call `_validate_active_object()` and `_validate_active_material()` at the start to benefit from shared error handling.
3. Add the class to `_OPERATOR_CLASSES` at the bottom of `operators.py`.
4. Add a UI button in `ui.py` calling your operator's `bl_idname`.

#### Adding a New Blend Mode

1. Add an entry to the `blend_type` `EnumProperty` in `properties.py`.
2. Blender's `ShaderNodeMix` supports all standard blend modes natively — no changes to `engine.py` are required.

#### Adding a New Layer Property

1. Define the `bpy.props.*` field in `RasterLayerItem` in `properties.py`.
2. Add `update=_auto_update_tree` to the property definition so the node tree rebuilds automatically on change.
3. Handle the new property in `NodeTreeManager.update_layer_group()` in `engine.py`.
4. Expose the property in `ui.py` inside `_draw_layer_item()`.

---

## 9. Quick-Start Cheat Sheet

| Goal | Action |
|---|---|
| **Create a new canvas** | Sidebar → **Create Canvas** |
| **Add a layer** | Sidebar → **Add Layer**, then assign or create an image |
| **Paint on a layer** | Click **Brush icon** on the layer → switch to **Texture Paint** mode → paint |
| **Add a mask to a layer** | Click **Add Mask** on the layer row |
| **Paint a mask** | Click **Brush icon on the mask row** → switch to Texture Paint → paint in greyscale |
| **Toggle mask on/off** | Click the **Shield icon** on the mask row |
| **Remove a mask** | Click **✕** on the mask row |
| **Change blend mode** | **Blend Mode** dropdown below the layer image selector |
| **Change opacity** | **Opacity** slider; click **Apply Opacity** if the viewport lags |
| **Force node tree sync** | Utilities → **Apply Opacity** |
| **Reorder layers** | **▲ / ▼** buttons on the layer row |
| **Duplicate a layer** | **⎘** (copy icon) on the layer row |
| **Delete a layer** | **✕** button on the layer row |
| **Hide a layer** | **Eye icon** on the layer row |
| **Flatten all layers** | Utilities → **Merge Visible** (requires ≥ 2 visible layers) |
| **Change canvas size** | Utilities → **Resize Canvas** → enter new dimensions |
| **Set up render camera** | Utilities → **Frame Camera** |
| **Load a video layer** | Image selector → folder icon → select `.mp4` or first frame of sequence |
| **Export the final image** | Merge Visible → open Image Editor → **Image → Save As** |

---

*Blender Raster Editor — Licensed under GNU GPL v3.0 — See [LICENSE](LICENSE) for details.*
