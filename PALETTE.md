# Island Color Script (M4.3)

Bright, saturated, low-poly 90s/2000s platformer look (Spyro / Crash). Warm golden-hour sun and
cool sky fill. Every new asset (terrain, flora, water, props, cat, rides) picks its base colors from here.
Values are **sRGB 0..1, exactly as typed into Godot `Color()` or a shader `source_color` uniform** (Godot
linearizes them itself). Hex = the same values × 255, for image editors. In Blender color pickers, use the hex field.

Godot constants: `godot/scripts/palette.gd` (`Palette.SAND`, …). Keep that file and this table in sync.

## Rules

- **Saturation over realism.** Greens lean yellow, water leans turquoise, shadows lean blue-violet (never gray-black).
- **Value ladder** (light → dark): foam/sky horizon > sand > palm leaf > grass > rock > jungle floor > canopy dark > volcanic rock.
  The hero (orange fur) must pop against every zone: keep zone colors off pure orange.
- **Lava orange is reserved** for the volcano and danger/goal cues. Collectibles use banana yellow; shells (currency) use SHELL pink + SHELL_CREAM, never orange.
- **Textures**: flat colors + subtle vertex/noise variation (±8 % value). No photo textures. Low-res atlases (≤ 512 px).
- **Night / caves**: shift toward `CAVE_AMBIENT`, never plain black.

## Palette

| Token | Role | Color() | Hex |
|---|---|---|---|
| SKY_ZENITH | sky top | (0.23, 0.53, 0.93) | #3B87ED |
| SKY_HORIZON | sky at horizon, fog far | (0.70, 0.87, 0.98) | #B2DEFA |
| SUN_GLOW | sun disc / halo | (1.00, 0.86, 0.60) | #FFDB99 |
| SUN_LIGHT | directional light color | (1.00, 0.92, 0.76) | #FFEBC2 |
| AMBIENT_FILL | shadow fill tint | (0.55, 0.68, 0.95) | #8CADF2 |
| OCEAN_DEEP | open sea | (0.03, 0.30, 0.58) | #084C94 |
| OCEAN_SHALLOW | reef / lagoon / near shore | (0.10, 0.78, 0.80) | #1AC7CC |
| FOAM | surf, waterfall spray | (0.95, 0.98, 1.00) | #F2FAFF |
| RIVER | streams, ponds | (0.12, 0.62, 0.70) | #1F9EB2 |
| SAND | dry beach | (0.97, 0.87, 0.62) | #F7DE9E |
| SAND_WET | waterline, seabed near shore | (0.82, 0.68, 0.45) | #D1AD73 |
| GRASS | meadows, trail edges, jungle clearings | (0.45, 0.76, 0.22) | #73C238 |
| JUNGLE_FLOOR | dense jungle ground | (0.24, 0.55, 0.18) | #3D8C2E |
| CANOPY_DARK | deep foliage, undergrowth shade | (0.10, 0.37, 0.17) | #1A5E2B |
| PALM_LEAF | palm fronds, ferns | (0.40, 0.72, 0.18) | #66B82E |
| TRUNK | palm/tree bark | (0.55, 0.38, 0.22) | #8C6138 |
| TRAIL | packed dirt trail | (0.78, 0.60, 0.38) | #C79961 |
| ROCK | cliffs, boulders, escarpment | (0.58, 0.50, 0.43) | #94806E |
| ROCK_VOLCANIC | upper volcano, crater | (0.42, 0.34, 0.32) | #6B5752 |
| LAVA | lava, goal glow (reserved) | (1.00, 0.42, 0.08) | #FF6B14 |
| LAVA_GLOW | lava emission highlight | (1.00, 0.78, 0.25) | #FFC740 |
| CAVE_AMBIENT | cave interior fill | (0.20, 0.24, 0.38) | #333D61 |
| BANANA | collectibles | (1.00, 0.88, 0.15) | #FFE026 |
| SHELL | shell currency (P2.12), scallop body | (0.97, 0.42, 0.58) | #F76B94 |
| SHELL_CREAM | shell ridges / rim | (1.00, 0.93, 0.82) | #FFEDD1 |
| HERO_FUR | reference only (Tripo texture median) | (0.72, 0.31, 0.09) | #B84F17 |

## Terrain variation tints (P2.5, derived, shader only)

Not palette tokens: small offsets around GRASS / SAND used only by `godot/shaders/terrain.gdshader` (uniforms of the
same names). The patch mix is centered, so on average the ground stays exactly GRASS / SAND. Not in `palette.gd`.

| Uniform | Derived from | Color() |
|---|---|---|
| grass_lush_color | GRASS, deeper | (0.35, 0.67, 0.19) |
| grass_dry_color | GRASS, yellower | (0.56, 0.77, 0.22) |
| clover_color | GRASS, slightly blue-green | (0.33, 0.69, 0.26) |
| sand_dune_color | SAND, paler | (0.99, 0.92, 0.72) |
| sand_warm_color | SAND, warmer | (0.95, 0.81, 0.55) |
| flower_a/b/c_color | muted dots near the grass value (soft lilac, pale yellow-green, dusty lavender); never white, BANANA or SHELL | (0.66, 0.66, 0.84) · (0.68, 0.84, 0.40) · (0.74, 0.70, 0.86) |

## Zone mapping

- **Beach**: SAND, with SAND_WET for the last ~2 m above the waterline. OCEAN_SHALLOW → OCEAN_DEEP over the first ~60 m offshore, FOAM at the shoreline.
- **Jungle ring**: JUNGLE_FLOOR ground, GRASS in clearings and along the trail, CANOPY_DARK undergrowth, PALM_LEAF near the coast.
- **Escarpment / steep faces**: ROCK.
- **Volcano**: ROCK blending to ROCK_VOLCANIC above ~150 m, LAVA only in the crater.
- **Trail**: TRAIL dirt band (layout JSON trail polyline, half width 3.5 m).
