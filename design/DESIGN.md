# Design System: High-End Asset Explorer & 3D Viewer

## 1. Overview & Creative North Star
**Creative North Star: "The Synthetic Lens"**
This design system is engineered to feel less like a software interface and more like a high-precision optical instrument. It rejects the cluttered, "button-heavy" aesthetic of legacy 3D tools in favor of **The Synthetic Lens**—a philosophy where the UI recedes to prioritize the asset, using light, depth, and atmospheric blur to guide the user’s eye. 

The system breaks the "template" look through **intentional asymmetry** (e.g., a heavy-weighted sidebar juxtaposed against an expansive, edge-to-edge viewport) and **tonal depth**. We move away from rigid 1px dividers, instead defining the workspace through "atmospheric" shifts in dark values, creating a UI that feels carved out of a single piece of obsidian.

---

## 2. Colors & Surface Philosophy
The palette is rooted in a deep "Midnight Charcoal" base, punctuated by high-frequency neon accents that mimic the glow of a phosphor screen.

### Tonal Hierarchy
- **Base Surface (`surface` / `#0f1419`):** The absolute floor of the application. Used for the main background.
- **The "No-Line" Rule:** Explicitly prohibit 1px solid borders for sectioning. Boundaries must be defined solely through background color shifts. For example, a navigation tree sitting on `surface-container-low` against a `surface` background provides all the definition needed without the "jail-cell" feel of grid lines.
- **Nesting Logic:** Use the `surface-container` tiers to create organic depth. 
    - *Viewport:* `surface-container-lowest` (#0a0f14) to create a "void" for the 3D model.
    - *Panels:* `surface-container` (#1b2025).
    - *Pop-overs/Modals:* `surface-bright` (#353a3f).

### The "Glass & Gradient" Rule
To achieve a premium, futuristic feel, floating panels (like transform gizmo settings) must use **Glassmorphism**.
- **Token:** `surface-container-high` at 60% opacity.
- **Effect:** `backdrop-filter: blur(20px)`.
- **Signature Texture:** Primary actions (`primary` / `#c3f5ff`) should never be flat. Use a subtle linear gradient transitioning from `primary` to `primary_container` (#00e5ff) at a 135-degree angle to give the UI "soul" and a sense of internal illumination.

---

## 3. Typography
We utilize a dual-typeface system to balance technical precision with editorial authority.

*   **Display & Headlines (Manrope):** Chosen for its geometric purity. Use `display-md` or `headline-sm` for workspace titles or major asset categories. The wide tracking and high-contrast scale convey a premium, "gallery" feel.
*   **Interface & Data (Inter):** Used for everything else. Inter’s tall x-height ensures readability in dense tree views and property inspectors. 
*   **The Hierarchy Rule:** Use `label-sm` (#0.6875rem) in `on-surface-variant` for non-interactive metadata to keep the UI quiet. Reserve `title-sm` (1rem) for active selection states to create a clear focal point.

---

## 4. Elevation & Depth
In this system, depth is a function of light, not structure.

*   **The Layering Principle:** Stack surfaces to create a "frosted" hierarchy. A `surface-container-highest` card placed on a `surface-container` panel creates a natural lift.
*   **Ambient Shadows:** For floating elements, use a "Neon Glow" shadow. Instead of black, use a shadow color derived from the `surface_tint` (#00daf3) at 4% opacity with a 32px blur. This mimics the light bleed from a high-end monitor.
*   **The "Ghost Border" Fallback:** If a separation is required for accessibility, use the `outline-variant` (#3b494c) at **15% opacity**. This creates a "suggestion" of an edge that disappears into the dark base, maintaining the sleek aesthetic.

---

## 5. Components

### The 3D Viewport (The Hero)
- **Edge-to-Edge:** The viewport should occupy the maximum available space, often bleeding behind semi-transparent sidebars (`surface-container` with 80% opacity and blur).
- **Corner Radius:** Apply `xl` (1.5rem) or `lg` (1rem) to the internal viewport container to soften the technical "edge" of the 3D engine.

### Sidebar Tree Views & Lists
- **Interaction:** No dividers. Use the `Spacing Scale (2)` (0.4rem) between items.
- **Hover State:** Apply a subtle background shift to `surface-container-highest` with a 2px `secondary` (Emerald) left-accent bar.
- **Selection:** Use `primary-container` background with `on-primary-container` text.

### Buttons & Inputs
- **Primary Action:** `primary` gradient fill, `md` (0.75rem) corner radius. Use `on-primary` for text.
- **Input Fields:** Use `surface-container-lowest` for the field base. The label should use `label-md` and sit 0.3rem above the field, never inside it, to maintain an editorial look.
- **Checkboxes/Radios:** Use `secondary` (#44f6a8) for "on" states to provide a sophisticated "emerald" contrast against the cyan primary actions.

### Asset Grid (Thumbnail Gallery)
- **The Frame:** Bitmaps should be housed in `surface-container-low` containers. 
- **The "No-Line" Rule Applied:** Separate thumbnails using `Spacing Scale (4)` (0.9rem) rather than borders. On hover, the thumbnail should scale slightly (1.05x) and increase its `backdrop-blur`.

---

## 6. Do’s and Don’ts

### Do
- **DO** use asymmetry. Place a heavy property panel on the right and a slim, icon-only toolbar on the left.
- **DO** use "breathable" white space. A high-end tool needs room for the user to think; use `Spacing Scale (8)` (1.75rem) to separate major functional groups.
- **DO** use `tertiary` (Violet) for destructive or advanced "power-user" actions to differentiate from standard navigation.

### Don't
- **DON'T** use pure black (#000000). It kills the "Synthetic Lens" effect and prevents the use of subtle depth layering.
- **DON'T** use 100% opaque borders. They create visual "noise" that competes with the 3D assets.
- **DON'T** use standard "drop shadows." If a panel is floating, it should feel like it is hovering due to magnetic levitation, not sitting on a table. Use wide, tinted ambient glows.