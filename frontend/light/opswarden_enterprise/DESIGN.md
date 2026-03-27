# Design System Strategy: The Intelligent Sentinel

## 1. Overview & Creative North Star
This design system is built for **The Intelligent Sentinel**. In the complex world of IT operations, the UI should not feel like a cluttered dashboard of widgets; it should feel like a curated, high-end command center. We move away from the "boxy" Enterprise SaaS tropes by embracing **Architectural Depth** and **Editorial Clarity**.

The system breaks the "template" look through:
*   **Intentional Asymmetry:** Using unbalanced white space to guide the eye toward critical alerts.
*   **Tonal Logic:** Replacing rigid 1px borders with "Lithic Layering"—defining structure through subtle shifts in surface luminance.
*   **Data as Art:** Monospaced data points are treated with high-contrast precision, turning technical logs into a sophisticated visual texture.

---

## 2. Colors & Surface Logic
Our palette is rooted in a "cool-to-warm" transition that separates the logic of the machine from the intuition of the operator.

### Palette Roles
*   **Primary (`#0058be`):** The "Action Nerve." Used sparingly for high-intent CTAs and active states.
*   **Secondary (`#006c49`):** The "Success Signal." Reserved for healthy system states and positive AI confirmations.
*   **Tertiary (`#4d5d73`):** The "Contextual Layer." Used for metadata and non-critical navigation elements.
*   **Neutral Surfaces:** A range from `surface_container_lowest` (#ffffff) to `surface_dim` (#cfdaf2) to define hierarchy without lines.

### The "No-Line" Rule
**Explicit Instruction:** Do not use 1px solid borders to separate sections. Structure must be achieved through background shifts. 
*   *Example:* Place a `surface_container_low` (#f0f3ff) sidebar against a `surface` (#f9f9ff) workspace. The 1% shift in value is enough for the human eye to perceive a boundary without creating visual "noise."

### Surface Hierarchy & Nesting
Treat the UI as a physical stack of paper:
1.  **Base Layer:** `background` (#f9f9ff)
2.  **Sectional Containers:** `surface_container_low` (#f0f3ff)
3.  **Active Workspace/Cards:** `surface_container_lowest` (#ffffff)
4.  **Floating Modals:** `surface_bright` with Glassmorphism.

### The Glass & Gradient Rule
For main CTAs or AI-powered insights, use a **Signature Texture**: A linear gradient from `primary` (#0058be) to `primary_container` (#2170e4) at a 135-degree angle. For floating AI "Warden" widgets, apply a `backdrop-blur(12px)` with a semi-transparent `surface_variant` to create a "frosted glass" effect that feels premium and integrated.

---

## 3. Typography
We utilize **Inter** as our UI workhorse, but we treat it with editorial intent.

*   **Display & Headline (Inter):** High tracking (-0.02em) and Semi-Bold weights. Use `display-sm` (2.25rem) for main dashboard summaries to command authority.
*   **Body (Inter):** Standardized at `body-md` (0.875rem) for density. We prioritize legibility by using `on_surface_variant` (#424754) for long-form logs to reduce eye strain.
*   **Labels & Monospace:** Technical data (IP addresses, cron jobs) must use a monospace font-family at `label-sm` (0.6875rem) to differentiate "system data" from "user interface."

---

## 4. Elevation & Depth
In this system, depth is a functional tool, not a stylistic flourish.

### The Layering Principle
Avoid shadows for static cards. Instead, achieve lift by placing a `surface_container_lowest` (#ffffff) element on top of a `surface_container` (#e7eeff) background. This "Tonal Lift" creates a cleaner, more modern enterprise feel.

### Ambient Shadows
When an element must float (Modals, Dropdowns), use **Ambient Shadows**:
*   `box-shadow: 0 12px 40px rgba(17, 28, 45, 0.08);`
*   The shadow is never black; it is a diluted version of `on_surface` (#111c2d) to mimic natural light refraction.

### The "Ghost Border" Fallback
If accessibility requirements demand a border, use the **Ghost Border**:
*   `outline: 1px solid rgba(194, 198, 214, 0.2);` (20% opacity of `outline_variant`). 
*   **Never** use 100% opaque borders for interior layout.

---

## 5. Components

### Buttons
*   **Primary:** Gradient fill (`primary` to `primary_container`), `lg` (0.5rem) corner radius. No border.
*   **Secondary:** Ghost style. Transparent background with a `ghost-border` and `primary` text.
*   **Tertiary:** Text-only with an underline appearing only on hover.

### Cards & Lists
*   **Rule:** Forbid divider lines. 
*   **Implementation:** Separate list items using `spacing-4` (1rem) of vertical white space or by alternating background colors between `surface_container_low` and `surface_container`.

### Input Fields
*   **State Logic:** On focus, the input should not just change border color; it should transition its background from `surface_container_low` to `surface_container_lowest` to "pop" toward the user.

### AI Insight Chips
*   **Unique Component:** For AI-generated operations insights, use a semi-transparent `secondary_container` (#6cf8bb) with a subtle `secondary` pulse animation to indicate "active monitoring."

---

## 6. Do’s and Don'ts

### Do:
*   **Do** use `spacing-8` (2rem) and `spacing-12` (3rem) to create generous "breathing zones" between unrelated data clusters.
*   **Do** use monospaced fonts for all numerical data to ensure tabular alignment.
*   **Do** use `surface_container_highest` (#d8e3fb) for "hover" states on interactive rows.

### Don’t:
*   **Don't** use 1px solid `#E2E8F0` borders to draw boxes around everything. Let the background colors do the work.
*   **Don't** use standard "Drop Shadows." If it looks like a default CSS shadow, it is too heavy. Use Ambient Shadows.
*   **Don't** use bright Red (#EF4444) for anything other than critical system failure. Use `warning` or `tertiary` for non-breaking issues.
*   **Don't** crowd the screen. If a page feels full, increase the spacing scale values rather than shrinking the text.