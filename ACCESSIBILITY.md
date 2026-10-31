# Accessibility

GitHub Command Center v3.51 introduces an accessibility preference layer for the Tk desktop UI.

## Available options

- High-contrast palette
- Large text and larger Treeview row targets
- Reduced-motion preference for animated/indeterminate UI
- Enhanced focus indicators
- Persistent local preferences

## Keyboard

- `Ctrl+K`: Command Palette
- `Tab` / `Shift+Tab`: move focus
- `Enter` / `Space`: activate standard focused controls
- `F5`: refresh where supported

## Design rules for future UI

- Do not use color alone to communicate PASS/FAIL, additions/deletions, or risk.
- Buttons must have text labels unless the accessible name is otherwise explicit.
- Destructive actions retain written confirmation and keyboard access.
- Text must remain readable at larger Tk scaling.
- New task centers should preserve logical tab order.
