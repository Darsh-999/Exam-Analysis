---
name: Functional Academic
colors:
  surface: '#fff8f3'
  surface-dim: '#dfd9d4'
  surface-bright: '#fff8f3'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f9f2ed'
  surface-container: '#f3ede7'
  surface-container-high: '#ede7e2'
  surface-container-highest: '#e8e1dc'
  on-surface: '#1d1b18'
  on-surface-variant: '#59413a'
  inverse-surface: '#33302c'
  inverse-on-surface: '#f6f0ea'
  outline: '#8d7169'
  outline-variant: '#e1bfb6'
  surface-tint: '#ae3102'
  primary: '#ab2f00'
  on-primary: '#ffffff'
  primary-container: '#cd471b'
  on-primary-container: '#fffbff'
  inverse-primary: '#ffb59f'
  secondary: '#835500'
  on-secondary: '#ffffff'
  secondary-container: '#feae2c'
  on-secondary-container: '#6b4500'
  tertiary: '#006386'
  on-tertiary: '#ffffff'
  tertiary-container: '#007da8'
  on-tertiary-container: '#fbfcff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#ffdbd1'
  primary-fixed-dim: '#ffb59f'
  on-primary-fixed: '#3a0a00'
  on-primary-fixed-variant: '#862300'
  secondary-fixed: '#ffddb4'
  secondary-fixed-dim: '#ffb955'
  on-secondary-fixed: '#291800'
  on-secondary-fixed-variant: '#633f00'
  tertiary-fixed: '#c3e8ff'
  tertiary-fixed-dim: '#79d1ff'
  on-tertiary-fixed: '#001e2c'
  on-tertiary-fixed-variant: '#004c68'
  background: '#fff8f3'
  on-background: '#1d1b18'
  surface-variant: '#e8e1dc'
typography:
  display-title:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.02em
  section-heading:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.01em
  body-main:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  table-header:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
  label-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
  display-title-mobile:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  nav-height: 64px
  container-max-width: 1280px
  gutter: 24px
  margin-mobile: 16px
  stack-gap: 16px
---

## Brand & Style
The design system is built for "ExamInsight," focusing on high-utility project management and deep exam analysis. The personality is academic yet modern—prioritizing legibility and structural clarity over decorative flair. 

The aesthetic follows a **Corporate / Modern** approach with a "Functionalist" twist. It utilizes a warm, parchment-like background to reduce eye strain during long analysis sessions, contrasted against sharp, high-contrast navigation elements. The interface communicates reliability and precision, using vibrant gradients only to highlight progress, status, and primary actions.

## Colors
The palette is grounded in a warm-neutral spectrum to differentiate from cold, standard SaaS blues. 

- **Foundation:** The page background uses a warm cream to evoke a paper-like feel. Surfaces and cards are pure white to provide maximum contrast for data.
- **Navigation:** The header uses a deep charcoal to anchor the application and provide a clear hierarchy between global navigation and workspace content.
- **Accents:** A signature orange-to-amber gradient is reserved for high-value actions and "active" states (e.g., data extraction in progress).
- **Status:** Standard semantic colors apply: Amber for processing, Green (#2D8A39) for completion, and Red (#D93025) for failures.

## Typography
This design system employs a systematic sans-serif stack (Inter) to ensure maximum readability and a "built-in" feel. 

- **Hierarchy:** Use `display-title` for page headers. On mobile devices, scale this down to 24px to prevent excessive wrapping.
- **Data Density:** The 14px body size is chosen to balance readability with the need to display dense exam metadata.
- **Tables:** Headers must use the `table-header` style, featuring increased letter spacing and uppercase casing to distinguish them from row data.

## Layout & Spacing
The layout follows a **Fixed Grid** philosophy on desktop (centered 1280px container) and a fluid model on mobile.

- **Grid:** A 12-column grid is used for dashboard layouts. Stat cards typically span 3 columns (4 per row) on desktop and 12 columns on mobile.
- **Rhythm:** A base-8 spacing system is preferred, though 12px and 20px increments are used for specific typographic alignment.
- **Top Nav:** Fixed at 64px. Content should have a top padding of at least 32px below the nav to allow the page title to breathe.

## Elevation & Depth
The system uses **Tonal Layers** and subtle shadows to imply depth without breaking the clean, functional aesthetic.

- **Level 0 (Background):** #F9F7F2 (Page background).
- **Level 1 (Surface):** #FFFFFF (Cards, Modals, Inputs).
- **Shadows:** Use a single, soft shadow style for cards: `0 1px 3px rgba(0,0,0,0.06)`. This creates a "lifted paper" effect rather than a floating one.
- **Scrim:** Modals use a 40% opacity charcoal (#141414) backdrop to pull focus.

## Shapes
The shape language is "Soft-Square." It avoids overly playful rounds but softens sharp corners to appear modern and approachable.

- **Small Components:** Checkboxes and small icons use 4px (Soft) radius.
- **Standard UI:** Buttons and input fields use 8px radius.
- **Containers:** Stat cards use a 10px radius, while larger Modals use 12px to emphasize their role as distinct temporary surfaces.

## Components

### Top Navigation
- **Height:** 64px.
- **Style:** Background #141414, Text #FFFFFF.
- **Items:** Links should have a 60% opacity in default state, moving to 100% on hover or active state.

### Stat Cards
- **Structure:** White background, 10px radius, soft shadow.
- **Visual Marker:** A 4px wide vertical bar on the extreme left edge, utilizing the Primary Accent Gradient.
- **Content:** Title in `label-sm` (Secondary Text), Value in `section-heading` (Primary Text).

### Buttons
- **Primary:** 8px radius, #EA5B2E to #F5A623 gradient, white text, semi-bold.
- **Secondary:** 8px radius, white background, 1px #E7E3DA border, #171512 text.
- **Height:** Standard buttons are 40px tall; small utility buttons are 32px.

### Status Badges
- **Shape:** Pill-style (fully rounded).
- **States:** 
    - *Amber:* Extracting/Classifying.
    - *Green:* Completed.
    - *Red:* Failed.
- **Style:** Light tinted background with high-contrast text of the same hue.

### Data Tables
- **Header:** Background #F9F7F2, uppercase text, 1px bottom divider #E7E3DA.
- **Rows:** White background, 1px bottom divider, 14px text. No vertical borders.

### Input Fields
- **Style:** 8px radius, 1px #E7E3DA border, 14px text. 
- **Focus:** 1px solid #EA5B2E with a subtle 2px orange outer glow.