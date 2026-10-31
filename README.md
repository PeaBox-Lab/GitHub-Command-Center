# GitHub Command Center v3.51.0

Version 3.51 is the accessibility improvement release.

## Accessibility & Display Center

Open `Ctrl+K → Accessibility & Display` to configure:

- high contrast
- larger text and larger list/table targets
- reduced-motion preference
- enhanced keyboard focus indicators

Preferences persist through the existing local preference service.

## Keyboard-first operation

The release documents and reinforces keyboard navigation around `Ctrl+K`, Tab / Shift+Tab, Enter / Space, F5, and standard dialog behavior. The Command Palette remains the fastest route to the complete Git/GitHub toolset.

## Shared accessibility layer

`ui/accessibility.py` provides reusable preferences, palette selection, accessible ttk styling, keyboard activation helpers, and text scaling. Future centers can consume one common accessibility contract instead of implementing accessibility independently.

## Design baseline

`ACCESSIBILITY.md` establishes rules for not relying on color alone, meaningful text labels, logical focus order, scalable text, and retaining keyboard access for destructive confirmations.
