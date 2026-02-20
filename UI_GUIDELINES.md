# ChitChat UI Guidelines

This document defines visual and interaction standards for ChitChat's interface. All modals, alerts, and form components should follow these guidelines for consistency, accessibility, and responsive behavior.

---

## 1. Design tokens

| Token | Dark | Light |
|-------|------|-------|
| Background (surface) | `#25262b` | `#fafafa` |
| Background (input) | `#0f0f12` | `#fff` |
| Border | `#3f3f46` | `#d4d4d8` |
| Text primary | `#e4e4e7` | `#18181b` |
| Text secondary | `#a1a1aa` | `#52525b` |
| Text muted | `#71717a` | `#71717a` |
| Accent (primary) | `#6366f1` | `#6366f1` |
| Accent hover | `#5558e3` | `#5558e3` |
| Destructive | `#7f1d1d` / `#ef4444` | `#dc2626` |
| Destructive hover | `#991b1b` | `#b91c1c` |
| Secondary button bg | `#3f3f46` | `#e4e4e7` |
| Secondary button hover | `#52525b` | `#d4d4d8` |

---

## 2. Modals and dialogs

### 2.1 General rules

- **Use custom modals** — Never use native `alert()`, `confirm()`, or `prompt()`. They cannot be styled and break the app's look and feel.
- **Semantic markup** — Use `role="dialog"`, `aria-modal="true"`, and `aria-label` (or `aria-labelledby`).
- **Focus management** — Move focus into the dialog on open; trap focus within; return focus on close.
- **Escape to close** — Dialogs must close on Escape unless the action is critical and irreversible.
- **Backdrop** — Use a semi-transparent overlay (`rgba(0,0,0,0.5)`) to dim the page.
- **z-index** — Backdrop: `2000`; dialog content: `2001`; pickers/overlays: `2002`.

### 2.2 Dimensions

| Breakpoint | Min width | Max width | Max height |
|------------|-----------|-----------|------------|
| Desktop | 280px | 90vw or 480px | 85vh |
| Mobile (≤768px) | 280px | calc(100vw - 2rem) | 80vh |

- **Padding**: 1rem–1.5rem.
- **Border radius**: 12px.
- **Box shadow**: `0 8px 24px rgba(0,0,0,0.5)` (dark) / lighter for light theme.

### 2.3 Confirm dialogs

- **Message**: Clear, concise text. For destructive actions, state consequences.
- **Primary button**: Rightmost; accent color for normal, destructive color for dangerous actions.
- **Secondary button**: "Cancel" or "Go back"; left of primary.
- **Button order**: Cancel | OK (or Delete / Wipe, etc.).

### 2.4 Prompt dialogs

- **Label**: Describe what the user should enter.
- **Input**: Full width; consistent with form inputs (border, padding, focus ring).
- **Placeholder**: Optional hint text.
- **Buttons**: Cancel | Submit.

### 2.5 Edit modals (message, profile, channel)

- **Title**: Short, descriptive (e.g., "Edit message", "Edit channel").
- **Form fields**: Labels above inputs; consistent spacing.
- **Actions**: Right-aligned; Cancel | OK.
- **Textarea**: Min height 100px; max height 280px; resize vertical.

---

## 3. Edit modal specifics

| Modal | Min width | Max width | Notes |
|-------|-----------|-----------|-------|
| Edit message | 320px | 90vw, 480px | Textarea for content; on mobile: long-press message or tap own message to show Edit button |
| Edit profile | 320px | 90vw, 480px | Status, away, bio fields |
| Edit channel | 320px | 90vw, 480px | Name, topic, protected checkbox |
| Search results | 320px | 90vw | Scrollable list |
| Room switcher | 320px | 400px | Filter + list |

### Mobile adjustments (≤768px)

- Modals use `max-width: calc(100vw - 2rem)` to avoid edge overflow.
- Ensure touch targets ≥ 44px height.
- Consider bottom sheet for long lists on mobile (e.g., presence sheet).

---

## 4. Accessibility

- **Color contrast**: Meet WCAG 2.1 AA (4.5:1 for normal text).
- **Focus visible**: Use `:focus-visible` or visible focus ring (e.g., `outline: 2px solid #6366f1`).
- **Reduced motion**: Respect `prefers-reduced-motion: reduce` for animations.
- **Keyboard**: Tab order logical; Enter submits; Escape closes.

---

## 5. References

- [WAI-ARIA Dialog Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/)
- [Stanford Modal Dialogs](https://uit.stanford.edu/accessibility/guides/web-applications/modal-dialogs)
- ChitChat design tokens and existing modals in `app/templates/chat.html`
