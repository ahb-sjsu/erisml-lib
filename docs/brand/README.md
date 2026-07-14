# Atlas AI — Brand kit

The canonical logo files. The SVGs in this directory are the source of
truth; any PNG / ICO / WebP exports should be regenerated from these,
not maintained by hand.

## Files

| File | What it is | Use it for |
|---|---|---|
| `atlas_mark.svg` | Sphere + apple combined mark (dark background) | The app header, ecosystem materials, anywhere Atlas and ErisML are presented together |
| `atlas_mark_light.svg` | Same, for white / light backgrounds | Printed whitepapers, light-theme docs |
| `atlas_sphere.svg` | Sphere alone (dark) | Atlas standing on its own — dashboard favicon, Atlas-only surfaces |
| `atlas_sphere_light.svg` | Sphere alone (light) | Atlas on white backgrounds |
| `erisml_apple.svg` | Apple alone (dark) | ErisML lib, Geometric Ethics book cover, ethics-specific repos |
| `erisml_apple_light.svg` | Apple alone (light) | ErisML on white backgrounds |

All files are 200×200 viewBox with no embedded raster, so they scale
cleanly at any size.

## Composition — the combined mark

Layout is:
- **Sphere** on the left, 50 px radius, centered at (75, 100).
- **Apple** on the right, 16 px radius, centered at (150, 90). Smaller
  than the sphere on purpose — Atlas is the primary product.
- **Tether** is a short dashed line from the sphere's right edge
  (125, 100) to the apple's lower-left edge (134, 90). Dash pattern
  `3 2` at 1.5 px stroke, 55% opacity.

This proportion and spacing is the spec. Don't scale them independently.

## Colors

| Role | Token | Dark bg | Light bg |
|---|---|---|---|
| Sphere ring | primary | `#4a9eff` | `#2b6cb0` |
| Sphere longitude/latitude | primary-tint | `#63b3ed` | `#2b6cb0` |
| Apple body | gold | `#f5c147` | `#c38a00` |
| Apple stem | stem | `#f5c147` dk / `#6b3a00` | `#6b3a00` |
| Leaf | leaf | `#4ade80` | `#15803d` |
| Tether | neutral | `#e0e6f0` | `#1a2340` |

Stay on these values. If a surface requires a different bg, add a
surface variant file rather than recoloring inline.

## Clear space

Minimum clear space around the combined mark: **1/4 of the sphere
radius** (≈13 px at native 200-unit viewBox) on all sides. Don't
crowd the mark with text or other graphics inside that margin.

## Minimum sizes

| Mark | Min display size |
|---|---|
| `atlas_mark` (combined) | 48 px wide. Below that, prefer the sphere-only mark. |
| `atlas_sphere` | 16 px (favicon). The longitude/latitude lines disappear but the circle + blue accent remains recognizable. |
| `erisml_apple` | 24 px. Below that, the leaf vanishes and it reads as a gold circle. |

## Exports (you'll need to regenerate as the SVG changes)

A small script generates PNG / ICO from the SVG masters:

```bash
# Requires: pip install cairosvg pillow
python docs/brand/export.py
```

Produces under `docs/brand/exports/`:

- `atlas_mark_<1024|512|256|128|64>.png` (dark + light variants)
- `atlas_sphere_<1024|512|256|128|64|32|16>.png`
- `erisml_apple_<512|256|128|64|32>.png`
- `favicon.ico` (16/32/48 multi-size, based on sphere mark)

Do **not** commit the exports by default — regenerate when needed so
the repo doesn't balloon with binaries. If a particular export is
needed in a specific location (e.g., a deployed site favicon), commit
only that file and regenerate the rest as build artifacts.

## Usage rules

**Do**

- Use `atlas_mark` in ecosystem / pitch contexts.
- Use `atlas_sphere` standalone for Atlas as a product.
- Use `erisml_apple` standalone for ErisML as a product.
- Keep the tether short and dashed — it's a deliberate narrative
  element, not a connector you can scale arbitrarily.

**Don't**

- Don't change the sphere-to-apple size ratio.
- Don't replace the dashed tether with a solid line, an arrow, or
  remove it from the combined mark.
- Don't recolor the apple. The gold is the Eris reference and is
  load-bearing.
- Don't set either mark on a patterned background.
- Don't use drop shadows or 3D effects.
