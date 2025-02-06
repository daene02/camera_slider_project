"""
Web interface settings and styling configuration.
All web-related constants and parameters are defined here.
"""

from typing import Dict

########################################
# Color Settings
########################################
COLORS: Dict[str, str] = {
    "primary": "#4a9eff",
    "background": "#000000",
    "overlay": "rgba(0, 0, 0, 0.85)",
    "border": "rgba(255, 255, 255, 0.3)",
    "text": {
        "primary": "#ffffff",
        "secondary": "rgba(255, 255, 255, 0.7)"
    }
}

########################################
# Typography Settings
########################################
FONTS = {
    "primary": "Arial, sans-serif",
    "monospace": "monospace",
    "sizes": {
        "small": "12px",
        "normal": "14px",
        "large": "16px",
        "xlarge": "24px"
    },
    "weights": {
        "normal": "400",
        "bold": "700"
    }
}

########################################
# Component Dimensions
########################################
COMPONENTS = {
    "icon_button": {
        "size": "60px",
        "border_radius": "5px"
    },
    "panel": {
        "width": "300px",
        "header_height": "61px"
    },
    "spacing": {
        "small": "10px",
        "medium": "15px",
        "large": "20px"
    }
}

########################################
# Animation Settings
########################################
ANIMATIONS = {
    "duration": {
        "fast": "0.6s",
        "normal": "2s"
    },
    "timing": "ease"
}

# Export settings for use in other modules
__all__ = [
    "COLORS",
    "FONTS",
    "COMPONENTS",
    "ANIMATIONS"
]
