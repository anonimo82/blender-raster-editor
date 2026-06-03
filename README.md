# Blender Raster Editor — Complete Tutorial

> **Add-on version:** 1.1.0 | **Blender:** 4.0.0+ | **License:** GNU GPL v3.0

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Requirements & Installation](#2-requirements--installation)
3. [UI Overview](#3-ui-overview)
4. [Core Workflow](#4-core-workflow)
   - [4.1 Creating a Canvas](#41-creating-a-canvas)
   - [4.2 Adding and Configuring Layers](#42-adding-and-configuring-layers)
   - [4.3 Painting on a Layer](#43-painting-on-a-layer)
   - [4.4 Using Layer Masks](#44-using-layer-masks)
   - [4.5 Video Rotoscoping](#45-video-rotoscoping)
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

**Blender Raster Editor** is an open-source Blender add-on that introduces a non-destructive, Photoshop-like layer workflow directly inside the 3D Viewport. Instead of relying on external image editors, you can stack textures, apply blend modes and masks, and composite them in real time — all managed by a smart shader node tree that the add-on builds automatically behind the scenes.

**Key capabilities:**

- Non-destructive layer stack with per-layer blend modes and opacity
- 19 blend modes (Multiply, Overlay, Screen, Color Burn, Dodge, and more)
- Per-layer black-and-white masks for non-destructive hiding/revealing of areas
- Video and image-sequence rotoscoping with automatic frame refresh
- One-click **Merge Visible** bake using Blender's Cycles engine
- Canvas resize utility (adds empty space without stretching artwork)
- Auto-framing orthographic camera setup

---

## 2. Requirements & Installation

### 2.1 Requirements

| Item | Requirement |
|---|---|
| Blender version | 4.0.0 or higher |
| Python module | `numpy` (bundled with Blender) |
| OS | Windows, macOS, Linux |
| Render engine (for Merge) | Cycles (built-in) |

### 2.2 Installation

1. Download the repository as a ZIP file (**Code → Download ZIP** on GitHub).
2. Open Blender and go to **Edit → Preferences → Add-ons**.
3. Click **Install…**, locate the downloaded `.zip`, and confirm.
4. Enable the add-on by ticking the checkbox next to **Paint: Blender Raster Editor**.
5. Press **N** in the 3D Viewport to open the Sidebar, then select the **Paint Layers** tab.

> **Note:** The add-on registers three modules in order: Properties → Operators → UI. Unregistration happens in reverse order. If Blender reports an error during enable, check the **System Console** for detailed logging output.

---

## 3. UI Overview

All controls live in the **Paint Layers** sidebar tab (N-panel → Paint Layers). The panel is organised into four sections:

| Section | Purpose |
|---|---|
| Canvas | Create a new canvas plane with a managed material |
| Layer Management | Add layers; each layer shows its image, blend mode, and opacity |
| Utilities | Apply Opacity, Merge Visible, Resize Canvas, Frame Camera |
| Paint Settings | Quick brush controls (visible in Texture Paint mode only) |

---

## 4. Core Workflow

### 4.1 Creating a Canvas

Click **Create Canvas** in the sidebar. The add-on will:

- Add a 2×2 world-unit plane named `Canvas`
- Attach a new material named `CanvasMaterial` with nodes enabled
- Add a default `Background` layer
- Build the initial shader node tree (a Principled BSDF wired to an empty texture node group)

> **Note:** You can also select any existing mesh object that has a node-based material and use the layer controls. The add-on attaches its properties (`raster_layers`, `raster_active_index`, `raster_active_is_mask`) to whichever object is currently active.

---

### 4.2 Adding and Configuring Layers

Click **Add Layer**. A new entry appears at the top of the layer list (layers are displayed top-to-bottom, highest-to-lowest in the stack).

#### Layer Controls

| Control | Description |
|---|---|
| **Brush icon** (active target) | Sets this layer (or its mask) as the active painting target. A filled icon indicates the current target. |
| **Eye icon** | Toggle layer visibility. Hidden layers are excluded from composition. |
| **Name field** | Editable text field for the layer name. |
| **▲ / ▼ arrows** | Move the layer up or down in the stack. |
| **Copy icon** | Duplicate the layer (copies image, mask, blend mode, and opacity). |
| **X button** | Delete the layer permanently. |
| **Image selector** | Assign an existing image or load a file (including `.mp4` or image sequences). |
| **Blend Mode dropdown** | Choose from 19 blending algorithms (see [Section 7](#7-blend-mode-reference)). |
| **Opacity slider** | Set per-layer transparency (0.0 – 1.0). |

---

### 4.3 Painting on a Layer

1. Click the **Brush icon** next to the desired layer to make it the active paint target.
2. Switch Blender to **Texture Paint** mode (Tab or the mode dropdown in the header).
3. If the layer has no image yet, click **New** in the image selector to generate a blank texture and choose your resolution.
4. Paint normally using Blender's built-in brush tools. The **Paint Settings** section at the bottom of the panel gives quick access to brush Color, Radius, Strength, and Blend Mode.

> ⚠️ **Warning:** Always make sure the correct layer is the active paint target before painting. Blender's native brush writes to whichever image node is selected in the Shader Editor — the add-on keeps this in sync automatically when you click the Brush icon.

---

### 4.4 Using Layer Masks

Masks let you hide parts of a layer non-destructively using a greyscale image (**white = reveal, black = hide**).

1. Click **Add Mask** on any layer. A 1024×1024 white image is created and assigned as the mask.
2. Click the **Brush icon** on the mask row (below the layer image selector) to set the mask as the active paint target.
3. Paint in black to hide areas, white to restore them.
4. Toggle the mask on/off with the **shield icon** (`use_mask`) without deleting it.
5. Click **X** on the mask row to remove the mask entirely.

---

### 4.5 Video Rotoscoping

The add-on handles `.mp4` files and image sequences natively:

- In a layer's image selector, click the folder icon and load an `.mp4` or the first frame of an image sequence.
- The add-on automatically sets `image_user.use_auto_refresh = True` and syncs the `frame_duration` property so the texture updates as you scrub the timeline.
- You can paint or annotate on top of a video layer by placing a blank texture layer above it.

---

## 5. Utilities

### 5.1 Apply Opacity

Due to Blender's EEVEE shader cache, slider changes to **Opacity** may occasionally not refresh the viewport immediately. Click **Apply Opacity** (File Refresh icon) to force the node tree to re-synchronise.

---

### 5.2 Merge Visible (Bake)

**Merge Visible** bakes the entire visible layer stack into a single flat image using Cycles:

1. At least **2 visible layers** are required.
2. A resolution dialog appears (default 1024×1024, up to 4096×4096).
3. The add-on temporarily switches the render engine to Cycles, bakes a Diffuse pass, then restores the previous engine.
4. Original visible layers are hidden. A new **Merged Layer** containing the baked image is added at the top of the stack.

> ⚠️ **Warning:** Baking freezes the interface for several seconds at high resolutions. Save your `.blend` file before using Merge Visible, especially on complex scenes.

---

### 5.3 Resize Canvas

**Resize Canvas** opens a dialog where you set a new Width and Height. The add-on:

- Reads each layer's current pixel data with NumPy
- Creates a new canvas of the target size, centring the old content
- Copies pixels with proper bounds-checking (no stretching)
- Adjusts the Canvas object's dimensions to maintain the correct aspect ratio

> Video and image-sequence layers are skipped — they cannot be resized this way.

---

### 5.4 Frame Camera

**Frame Camera** automatically:

- Finds or creates an orthographic camera named `Canvas_Camera`
- Positions it 5 Blender units above the canvas centre, looking straight down
- Sets `ortho_scale` to match the canvas dimensions
- Updates the render resolution to 1920 px on the longest axis (maintaining aspect ratio)
- Switches the active viewport to Camera perspective

---

## 6. Known Limitations

| Limitation | Details & Workaround |
|---|---|
| **Baking performance** | Merge Visible uses Cycles and freezes the UI. Use lower resolutions during iteration and merge at full resolution only for final output. |
| **Opacity update lag** | EEVEE's shader cache may delay opacity changes. Click **Apply Opacity** to force a refresh. |
| **Node tree protection** | The managed frame (`LAYER_MANAGER_FRAME`) must not be edited manually — the add-on will overwrite changes. Always use the panel UI. |
| **Viewport only** | Layered edits live in the shader node tree. To get a standalone image file, always run **Merge Visible** first. |
| **Resize & video layers** | Video (`.mp4`) and image-sequence layers are skipped by Resize Canvas. Resize source files externally if needed. |

---

## 7. Blend Mode Reference

| Mode | Description |
|---|---|
| **Mix** | Standard alpha-compositing blend (default). |
| **Darken** | Keeps the darker of the two layers' pixels. |
| **Multiply** | Multiplies pixel values; always darkens. Great for shadows. |
| **Color Burn** | Darkens with increased contrast. Strong darkening effect. |
| **Lighten** | Keeps the lighter pixel at each position. |
| **Screen** | Inverts, multiplies, inverts again. Always lightens. |
| **Color Dodge** | Brightens the base layer using the blend layer. |
| **Add** | Adds colour values together; quickly clips to white. |
| **Overlay** | Combines Multiply and Screen: darkens darks, lightens lights. |
| **Soft Light** | Subtle Overlay variant; gentler contrast boost. |
| **Linear Light** | Linear burn/dodge combination; very strong contrast. |
| **Difference** | Subtracts colours; black where identical, inverted elsewhere. |
| **Exclusion** | Similar to Difference but lower contrast. |
| **Subtract** | Subtracts blend from base; clamps at black. |
| **Divide** | Divides base by blend; brightens the result. |
| **Hue** | Takes hue from blend layer, saturation/value from base. |
| **Saturation** | Takes saturation from blend, hue/value from base. |
| **Color** | Takes hue and saturation from blend, value from base. |
| **Value** | Takes brightness from blend, colour from base. |

---

## 8. Developer Reference

### 8.1 Module Architecture

| Module | Responsibility |
|---|---|
| `__init__.py` | Add-on entry point. Registers modules in correct order; configures logging. |
| `constants.py` | Single source of truth for all magic strings, numbers, and default values. |
| `properties.py` | Custom Blender properties (`RasterLayerItem`, object-level collections). Defines the `_auto_update_tree` callback. |
| `engine.py` | `NodeTreeManager` class and `rebuild_node_tree()` function. All shader node construction lives here. |
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

Property changes (`image`, `opacity`, `blend_type`) also trigger the `_auto_update_tree` callback automatically, so the node tree stays in sync without requiring an explicit operator call.

### 8.3 Extending the Add-on

#### Adding a New Operator

1. Subclass `BaseOperator` in `operators.py`.
2. Implement `execute(self, context)`. Call `_validate_active_object()` and `_validate_active_material()` at the start.
3. Add the class to `_OPERATOR_CLASSES` at the bottom of `operators.py`.
4. Add a UI button in `ui.py` calling your operator's `bl_idname`.

#### Adding a New Blend Mode

1. Add an entry to the `blend_type` `EnumProperty` in `properties.py`.
2. Blender's `ShaderNodeMix` supports all modes natively — no engine changes required.

#### Adding a New Layer Property

1. Define the `bpy.props.*` field in `RasterLayerItem` in `properties.py`.
2. Add `update=_auto_update_tree` to the property so the node tree refreshes on change.
3. Handle the new property in `NodeTreeManager.update_layer_group()` in `engine.py`.
4. Expose the property in `ui.py` inside `_draw_layer_item()`.

---

## 9. Quick-Start Cheat Sheet

| Goal | Action |
|---|---|
| Create a new canvas | Sidebar → **Create Canvas** |
| Add a layer | Sidebar → **Add Layer**, then assign an image |
| Paint on a layer | Click Brush icon → switch to Texture Paint mode → paint |
| Add a mask | Click **Add Mask** on the desired layer row |
| Paint the mask | Click Brush icon on the mask row → paint in greyscale |
| Change blend mode | Blend Mode dropdown below the layer name |
| Change opacity | Opacity slider; click **Apply Opacity** if the viewport lags |
| Reorder layers | ▲ / ▼ buttons on the layer row |
| Duplicate a layer | Copy icon on the layer row |
| Delete a layer | X button on the layer row |
| Flatten all layers | Utilities → **Merge Visible** (requires ≥2 visible layers) |
| Change canvas size | Utilities → **Resize Canvas** → enter new dimensions |
| Set up camera | Utilities → **Frame Camera** |
| Load a video | Image selector → folder icon → select `.mp4` |
| Force node sync | Utilities → **Apply Opacity** |

---

*Blender Raster Editor — Licensed under GNU GPL v3.0 — See [LICENSE](LICENSE) for details.*
