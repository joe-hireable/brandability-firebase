# Brandability Design System

This document outlines the comprehensive design system for Brandability, an application designed to help trademark lawyers assess, strategize, and prepare for trademark cases more efficiently. The design system creates a professional, trustworthy, and intuitive user experience tailored to legal professionals.

## Core Principles

* **Clarity:** Clean interfaces that allow users to focus on their work without distraction
* **Efficiency:** Enabling users to complete tasks quickly with minimal effort
* **Trustworthiness:** Professional visual design that reinforces reliability and credibility
* **Consistency:** Predictable, learnable experiences through unified components and patterns
* **Legal Precision:** Attention to detail that reflects the precision required in trademark law

## Implementation

The design system is implemented using:

* **Tailwind CSS** for styling
* **shadcn/ui** for component architecture
* **React** for UI rendering
* **Open Sans & Merriweather** fonts for typography

A live component showcase is available at `/DesignSystem` to view all components and styles in action.

## Color System

### Brand Colors

| Name | Hex Value | Usage |
|------|-----------|-------|
| Primary (Deep Blue) | `#0A2A4D` | Primary actions, headers, main branding |
| Secondary (Light Blue) | `#F0F4F8` | Secondary elements, backgrounds, hover states |
| Accent (Gold) | `#D4AF37` | Highlights, emphasis, decorative elements |
| Neutral Gray | `#F9FAFB` | Subtle backgrounds, cards, separators |

### Text Colors

| Name | Hex Value | Usage |
|------|-----------|-------|
| Text Primary | `#111827` | Main content, headers, labels |
| Text Secondary | `#6B7280` | Supporting text, descriptions, placeholders |

### Status Colors

| Name | Hex Value | Usage |
|------|-----------|-------|
| Success | `#10B981` | Confirmation, approval, completion |
| Warning | `#F59E0B` | Alerts, pending states, caution notices |
| Error | `#EF4444` | Errors, destructive actions, critical alerts |

### Dark Mode

The color system supports a dark mode variant with appropriate contrast adjustments while maintaining the brand identity.

## Typography

### Font Families

* **Headings:** "Merriweather" (serif)
  * Conveys authority, tradition, and professionalism
  * Used for all headings (h1-h6)
  * Weights: 400 (regular), 700 (bold)

* **Body:** "Open Sans" (sans-serif)
  * Clean, modern, and highly readable
  * Used for all body text, buttons, and interface elements
  * Weights: 300 (light), 400 (regular), 500 (medium), 600 (semibold), 700 (bold)

### Type Scale

| Element | Size (px) | Weight | Line Height | Use Case |
|---------|-----------|--------|-------------|----------|
| h1 | 36/48px | 700 | 1.2 | Page titles |
| h2 | 30/36px | 700 | 1.2 | Section headings |
| h3 | 24/30px | 700 | 1.3 | Subsection headings |
| h4 | 20/24px | 700 | 1.3 | Card headings |
| h5 | 18/20px | 700 | 1.4 | Minor headings |
| h6 | 16/18px | 700 | 1.4 | Smallest headings |
| Large text | 18px | 400 | 1.6 | Introductory paragraphs |
| Body | 16px | 400 | 1.6 | Main content |
| Small | 14px | 400 | 1.5 | Secondary information |
| Code | 14px | 400 | 1.5 | Technical information |

## Components

### Buttons

Buttons use consistent styling with variants for different contexts:

* **Default:** Primary blue background for main actions
* **Secondary:** Light blue background for secondary actions
* **Accent:** Gold background for highlighted actions
* **Destructive:** Red background for destructive actions
* **Outline:** Bordered button for less prominent actions
* **Ghost:** Text-only button with hover state
* **Link:** Styled as a text link
* **Success:** Green background for confirmation actions
* **Warning:** Orange background for cautionary actions
* **Legal:** Special variant for legal document actions

Button sizes:
* **Small:** Compact actions
* **Default:** Standard size for most contexts
* **Large:** Prominent or primary page actions
* **Icon:** Square button for icon-only actions

### Cards

The `card-trademark` class provides a consistent container for trademark-related information with appropriate spacing, borders, and shadows.

### Status Badges

* **Pending:** Orange-tinted badge for in-process items
* **Approved:** Green-tinted badge for successful outcomes
* **Rejected:** Red-tinted badge for denied applications

### Legal-specific Elements

Special containers and styles for legal documents:
* `container-legal`: For legal document containers
* `legal-heading`: For document titles and sections
* `legal-section`: For document content blocks

## Responsive Design

All components are designed to be fully responsive, with appropriate adjustments for different screen sizes:

* Mobile-first approach
* Breakpoints at standard sizes (sm, md, lg, xl, 2xl)
* Appropriate spacing and typography adjustments
* Simplified layouts on smaller screens

## Accessibility

The design system prioritizes accessibility with:

* WCAG 2.1 AA compliance
* Sufficient color contrast
* Keyboard navigation support
* Screen reader friendly markup
* Focus states for all interactive elements

---

This design system ensures a consistent and high-quality user experience across the entire Brandability application, reflecting the professional needs of trademark lawyers and legal professionals.