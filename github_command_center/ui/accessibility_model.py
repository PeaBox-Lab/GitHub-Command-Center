from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class AccessibilityPreferences:
    high_contrast: bool = False
    large_text: bool = False
    reduce_motion: bool = False
    focus_indicators: bool = True

def accessible_palette(high_contrast=False):
    if high_contrast:
        return {"bg":"#000000","fg":"#ffffff","panel":"#000000","accent":"#ffff00","selection":"#00ffff","muted":"#d1d5db"}
    return {"bg":"#ffffff","fg":"#111827","panel":"#f8fafc","accent":"#4f46e5","selection":"#e0e7ff","muted":"#64748b"}
