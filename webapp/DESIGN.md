# Design System Documentation
 
## 1. Overview & Creative North Star: "The Kinetic Editorial"
This design system moves away from the rigid, boxy constraints of traditional educational software. Our Creative North Star is **"The Kinetic Editorial"**—a philosophy that treats language learning as a living, breathing journey rather than a series of checklists. 
 
To achieve a premium, custom feel, we prioritize **intentional asymmetry** and **tonal depth**. We break the "template" look by overlapping typographic elements over containers and using high-contrast scales that prioritize data storytelling. This is not just a dashboard; it is a sophisticated, curated experience that celebrates progress through breathing room and vibrant, fluid transitions.

---
 
## 2. Colors & Surface Philosophy
The palette utilizes the vibrant energy of Pink and Teal, tempered by a sophisticated range of "warm-neutral" surfaces to ensure the app feels premium rather than "childish."
 
### The Palette
*   **Primary (#FF6B9D):** Our signature "Vibrant Pink." Used for critical brand moments, hero data points, and high-energy CTAs.
*   **Secondary (#40E0D0):** Our "Vibrant Teal." Used for growth indicators, success states, and linguistic milestones.
*   **Tertiary (#121111):** A deep, sophisticated dark tone used for high-contrast accents and grounded decorative elements.
*   **Neutral:** A range of warm-neutral surfaces derived from the seed to ensure the interface feels organic and premium.
 
### The "No-Line" Rule
**Explicit Instruction:** Designers are prohibited from using 1px solid borders to section content. Boundaries must be defined solely through background color shifts. Use `surface-container-low` for a section background and `surface-container-lowest` for cards sitting atop it. This creates a soft, modern interface that feels organic.
 
### The "Glass & Gradient" Rule
To add visual "soul," primary CTAs and progress bars should utilize subtle linear gradients (e.g., `primary` to `primary-container`). For floating modals or navigation overlays, apply **Glassmorphism**: use `surface` colors at 80% opacity with a `24px` backdrop blur.
 
---
 
## 3. Typography: Editorial Authority
We pair **Plus Jakarta Sans** (Display/Headlines) with **Inter** (Body/Labels) to balance character with extreme readability.
 
*   **Display (Plus Jakarta Sans):** Used for milestone numbers (e.g., "450 Words"). Use `display-lg` (3.5rem) with tight tracking (-2%) to create an authoritative, editorial impact.
*   **Headlines (Plus Jakarta Sans):** Use `headline-md` (1.75rem) for screen titles. These should often "bleed" outside of traditional container margins to break the grid.
*   **Body (Inter):** All instructional text uses `body-lg` (1rem) for maximum legibility during study sessions.
*   **Labels (Inter):** `label-md` (0.75rem) in all-caps with +5% letter spacing for data visualization legends.
 
---
 
## 4. Elevation & Depth: Tonal Layering
Traditional drop shadows are largely replaced by **Tonal Layering**, supported by moderate roundedness (`roundedness: 2`).
 
*   **The Layering Principle:** Depth is achieved by stacking tiers.
    *   *Base:* `surface`
    *   *Section:* `surface-container-low`
    *   *Card:* `surface-container-lowest`
*   **Ambient Shadows:** If an element must float (e.g., a FAB), use a `32px` blur at 6% opacity using a tinted shadow (`on-surface` color). 
*   **The "Ghost Border" Fallback:** If accessibility requires a stroke, use `outline-variant` at **15% opacity**. Never use 100% opaque borders.
 
---
 
## 5. Components & Data Visualization
 
### Cards & Progress Containers
*   **The Rule:** No dividers. Use moderate corner radii for main cards and subtle rounding for nested elements to maintain a balanced, modern feel. 
*   **Spacing:** Use a strict 8pt grid (level 2), but allow for "asymmetric breathing room"—increase padding on the left side of cards to 32px while keeping the right at 24px to create a directional flow.
 
### Progress Bars (Data-Driven)
*   **Track:** Use `surface-variant`.
*   **Indicator:** A gradient from `secondary` (#40E0D0) to its corresponding container shade.
*   **Animation:** Indicators should use a `cubic-bezier(0.34, 1.56, 0.64, 1)` transition to feel "springy" and alive.
 
### Interactive Elements
*   **Primary Buttons:** Rounded `full` (9999px). No border. Background: `primary` (#FF6B9D). Text: `on-primary`.
*   **Input Fields:** Use `surface-container-highest` as the background. On focus, transition the background to `surface-container-lowest` and add a 2px `secondary` (Teal) "Ghost Border" at 30% opacity.
*   **Chips:** Use `secondary-container` for active categories. Forbid "outline-only" chips; they clutter the visual field.
 
### Specialized Learning Components
*   **Vocabulary Heatmap:** Use a monochromatic scale of Teal (`secondary-fixed` to `secondary`) to represent mastery levels.
*   **Micro-Interactions:** When a user completes a lesson, use a "Pink Flash" (`primary`) transition that fades into the standard Teal success state.
 
---
 
## 6. Do's and Don'ts
 
### Do:
*   **Do** use overlapping elements (e.g., a progress percentage half-exiting the top of its card).
*   **Do** prioritize whitespace over lines. If a layout feels messy, add `16px` of padding rather than a divider.
*   **Do** use the "Vibrant Pink" (#FF6B9D) for momentum—it should represent energy and active learning.
 
### Don't:
*   **Don't** use pure black (#000000) for text. Always use `on-surface`.
*   **Don't** use standard Material Design elevation shadows. Stick to tonal shifts.
*   **Don't** use default Inter for headings. It lacks the "editorial" character required for this system; always use Plus Jakarta Sans for titles.
