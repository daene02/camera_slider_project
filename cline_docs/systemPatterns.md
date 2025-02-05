# Camera Slider Project - System Architecture & Patterns

## Web Interface Design System

### Web Settings Architecture

1. **Core Configuration Structure**
```python
# web_settings.py

class WebUISettings:
    # Colors
    COLORS = {
        "primary": "#4a9eff",
        "background": "#000000",
        "overlay": "rgba(0, 0, 0, 0.85)",
        "border": "rgba(255, 255, 255, 0.3)",
        "text": {
            "primary": "#ffffff",
            "secondary": "rgba(255, 255, 255, 0.7)"
        }
    }

    # Typography
    TYPOGRAPHY = {
        "fonts": {
            "primary": "Arial, sans-serif",
            "monospace": "monospace"
        },
        "sizes": {
            "small": "12px",
            "normal": "14px",
            "large": "16px",
            "xlarge": "24px"
        },
        "weights": {
            "normal": 400,
            "bold": 700
        }
    }

    # Component Dimensions
    COMPONENTS = {
        "icon_button": {
            "size": "60px",
            "radius": "8px"
        },
        "panel": {
            "width": "300px",
            "header_height": "61px"
        }
    }

    # Spacing
    SPACING = {
        "small": "10px",
        "medium": "15px",
        "large": "20px"
    }

    # Animations
    ANIMATIONS = {
        "fast": "0.2s",
        "normal": "0.3s",
        "timing": "ease"
    }
```

2. **CSS Implementation Pattern**
```css
/* base.css */

:root {
    /* Colors */
    --color-primary: var(--COLORS-primary);
    --color-background: var(--COLORS-background);
    --color-overlay: var(--COLORS-overlay);
    --color-border: var(--COLORS-border);
    
    /* Typography */
    --font-primary: var(--TYPOGRAPHY-fonts-primary);
    --font-monospace: var(--TYPOGRAPHY-fonts-monospace);
    
    /* Component Dimensions */
    --icon-button-size: var(--COMPONENTS-icon_button-size);
    --icon-button-radius: var(--COMPONENTS-icon_button-radius);
    
    /* Spacing */
    --spacing-small: var(--SPACING-small);
    --spacing-medium: var(--SPACING-medium);
    --spacing-large: var(--SPACING-large);
}
```

### Component Architecture

1. **Base Components**
```css
/* Common Button Pattern */
.btn {
    background: var(--color-overlay);
    color: var(--color-text-primary);
    border: 1px solid var(--color-border);
    padding: var(--spacing-small) var(--spacing-medium);
    border-radius: var(--icon-button-radius);
    transition: all var(--animation-fast) var(--animation-timing);
}

/* Panel Pattern */
.panel {
    width: var(--panel-width);
    background: var(--color-overlay);
    border: 1px solid var(--color-border);
}

/* Form Control Pattern */
.form-control {
    background: var(--color-overlay);
    border: 1px solid var(--color-border);
    color: var(--color-text-primary);
    padding: var(--spacing-small);
    border-radius: var(--icon-button-radius);
}
```

2. **Feature-Specific Patterns**
```css
/* Focus Control Pattern */
.focus-controls {
    display: grid;
    gap: var(--spacing-medium);
}

/* Motor Control Pattern */
.motor-box {
    padding: var(--spacing-medium);
    border-radius: var(--icon-button-radius);
    background: var(--color-overlay);
    transition: border-color var(--animation-fast);
}

/* Profile Management Pattern */
.profile-controls {
    margin-bottom: var(--spacing-medium);
    padding: var(--spacing-medium);
    background: var(--color-overlay);
    border-radius: var(--icon-button-radius);
}

/* Video Controls Pattern */
.video-controls {
    margin-bottom: calc(var(--spacing-large) * 1.5);
}

/* Photo Mode Pattern */
.photo-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
    gap: var(--spacing-small);
}
```

### Implementation Guidelines

1. **CSS Organization**
   - Base reset styles
   - Common components
   - Typography classes
   - Utility classes
   - Feature-specific styles
   - Media queries

2. **Class Naming Convention**
   - Use BEM methodology
   - Component-based organization
   - Utility-first approach for common patterns
   - Feature-specific namespacing

3. **Responsive Design**
   - Mobile-first approach
   - Breakpoint system
   - Fluid typography
   - Flexible layouts

4. **Performance Optimization**
   - CSS specificity management
   - Minimal nesting
   - Reusable utility classes
   - Efficient selectors

[Previous content remains unchanged...]
