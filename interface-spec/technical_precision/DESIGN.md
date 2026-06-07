---
name: Technical Precision
colors:
  surface: '#10131a'
  surface-dim: '#10131a'
  surface-bright: '#363941'
  surface-container-lowest: '#0b0e15'
  surface-container-low: '#191b23'
  surface-container: '#1d2027'
  surface-container-high: '#272a31'
  surface-container-highest: '#32353c'
  on-surface: '#e1e2ec'
  on-surface-variant: '#c2c6d6'
  inverse-surface: '#e1e2ec'
  inverse-on-surface: '#2e3038'
  outline: '#8c909f'
  outline-variant: '#424754'
  surface-tint: '#adc6ff'
  primary: '#adc6ff'
  on-primary: '#002e6a'
  primary-container: '#4d8eff'
  on-primary-container: '#00285d'
  inverse-primary: '#005ac2'
  secondary: '#c6c6c7'
  on-secondary: '#2f3131'
  secondary-container: '#454747'
  on-secondary-container: '#b4b5b5'
  tertiary: '#c7c6c6'
  on-tertiary: '#2f3131'
  tertiary-container: '#909191'
  on-tertiary-container: '#292a2a'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#d8e2ff'
  primary-fixed-dim: '#adc6ff'
  on-primary-fixed: '#001a42'
  on-primary-fixed-variant: '#004395'
  secondary-fixed: '#e2e2e2'
  secondary-fixed-dim: '#c6c6c7'
  on-secondary-fixed: '#1a1c1c'
  on-secondary-fixed-variant: '#454747'
  tertiary-fixed: '#e3e2e2'
  tertiary-fixed-dim: '#c7c6c6'
  on-tertiary-fixed: '#1a1c1c'
  on-tertiary-fixed-variant: '#464747'
  background: '#10131a'
  on-background: '#e1e2ec'
  surface-variant: '#32353c'
typography:
  headline-lg:
    fontFamily: Geist
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Geist
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: -0.01em
  body-md:
    fontFamily: Geist
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
    letterSpacing: '0'
  body-sm:
    fontFamily: Geist
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
    letterSpacing: '0'
  code-md:
    fontFamily: Geist Mono
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 20px
    letterSpacing: '0'
  code-sm:
    fontFamily: Geist Mono
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
    letterSpacing: '0'
  label-caps:
    fontFamily: Geist
    fontSize: 11px
    fontWeight: '700'
    lineHeight: 16px
    letterSpacing: 0.05em
spacing:
  unit: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  gutter: 16px
  sidebar-width: 280px
---

## Brand & Style
This design system is built for high-velocity engineering environments where clarity and information density are paramount. The brand personality is clinical, efficient, and uncompromisingly technical. It avoids the "softness" of consumer apps in favor of a workspace that feels like a high-performance terminal.

The aesthetic follows a **Technical Minimalism** approach:
- **Atmosphere:** Dark, focused, and immersive.
- **Visual Language:** Sharp geometry, high-contrast logic, and zero-depth surfaces.
- **Emotional Response:** Empowers the user with a sense of control, precision, and speed.
- **Target Audience:** Developers, architects, and technical leads interacting with complex codebases.

## Colors
The palette is strictly functional, optimized for prolonged focus and reduced eye strain in dark environments. 

- **Foundation:** The interface uses `#0a0a0a` as the primary canvas, with `#111111` for secondary containers like sidebars or code blocks to create subtle structural hierarchy.
- **Accent:** Electric Blue (`#3b82f6`) is reserved strictly for interactive states, primary actions, and AI-driven insights. It acts as a beacon within the dark workspace.
- **Content:** Typography utilizes pure white for maximum legibility in headings and UI labels, while subtext and metadata use muted greys to reduce visual noise.
- **Borders:** Instead of shadows, 1px solid strokes in `#222` and `#333` define the spatial boundaries.

## Typography
The typography system prioritizes scanning efficiency and technical readability. It uses **Geist** for the interface to maintain a clean, modernist sans-serif feel, and **Geist Mono** for all code-related content and metadata.

- **Scale:** Sizes are intentionally compact (starting at 13px/14px for body text) to support high information density.
- **Hierarchy:** Use `label-caps` for section headers in sidebars to differentiate navigation from content.
- **Code Rendering:** All code snippets, file paths, and terminal outputs must use the monospaced scale to ensure character alignment and technical accuracy.

## Layout & Spacing
The layout follows a **Rigid Grid** model with a 4px base unit. This allows for a dense, "utility-first" interface where every pixel is utilized for workflow.

- **Structure:** A standard 12-column grid is used for the main content area, but the interface is primarily defined by its fixed sidebars (File Explorer/History) and a fluid central editor/chat zone.
- **Density:** Gaps between components should remain tight (8px to 16px) to keep related information grouped effectively.
- **Responsive Behavior:** 
  - **Desktop:** Multi-pane view with persistent sidebars.
  - **Tablet:** Sidebars collapse into icons or drawers.
  - **Mobile:** Single-column focus, with the chat interface taking priority and the codebase accessible via a full-screen overlay.

## Elevation & Depth
This design system rejects the use of shadows and blurs. Depth is conveyed entirely through **Tonal Layering** and **Line Work**.

- **Surface Tiers:**
  - **Level 0 (#0a0a0a):** The primary application background.
  - **Level 1 (#111111):** Floating panels, sidebars, and input containers.
- **Separation:** Boundaries are strictly enforced by 1px solid borders.
- **Interaction Depth:** Instead of lifting an element on hover, the design system uses border-color shifts (from `#222` to `#333` or the primary accent) and background color changes. This maintains the "flat" technical aesthetic while providing clear feedback.

## Shapes
The shape language is defined by **Absolute Geometry**. 

- **Corners:** All elements (buttons, cards, inputs, modals) have a border-radius of 0px. This reinforces the "constructed" and precise nature of a codebase.
- **Consistency:** There are no exceptions for "pill" shapes or soft corners. Even checkboxes and radio buttons should maintain sharp 90-degree angles.

## Components
- **Buttons:** Sharp corners. Primary buttons use a solid `#3b82f6` background with white text. Secondary buttons use a transparent background with a 1px `#333` border, shifting to a white border on hover.
- **Inputs:** Darker than the background (`#000000` or `#0a0a0a`) with a 1px `#222` border. On focus, the border changes to `#3b82f6` with a subtle 1px inner glow (no blur).
- **Code Blocks:** Displayed on a `#111111` background. Syntax highlighting should follow a high-contrast theme that avoids pastel colors, favoring vivid primaries and secondaries.
- **Chips/Labels:** Small, monospaced text inside a `#222` bordered box. Used for tags like `refactor`, `bug`, or `file-type`.
- **Lists:** High-density rows with 1px bottom borders. Hovering over a row should trigger a background shift to `#161616`.
- **AI Pulse:** For "thinking" or "loading" states, use a subtle 1px border animation that "crawls" around the container or a rhythmic opacity shift of the accent color.