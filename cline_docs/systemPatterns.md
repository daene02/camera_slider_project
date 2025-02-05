# Camera Slider Project - System Architecture & Patterns

## Settings Architecture (Added March 2025)

### Centralized Configuration Pattern
```python
"""
Global settings and configuration for the camera slider project.
All constants and configuration parameters are defined here.
"""
from typing import Dict, List, Union

class SettingsArchitecture:
    # Communication Settings
    DEVICE_NAME: str
    BAUD_RATE: int
    PROTOCOL_VERSION: float
    
    # Motor Configuration
    MOTOR_IDS: Dict[str, int]
    MOTOR_LIMITS: Dict[str, Dict[str, int]]
    
    # Movement Parameters
    DEFAULT_VELOCITY: int
    DEFAULT_ACCELERATION: int
    PAN_TILT_VELOCITY: int
    
    # Focus Settings
    FOCUS_ENABLED: bool
    MIN_FOCUS_DISTANCE: int
```

### Settings Usage Pattern
```python
from src.settings import (
    MOTOR_IDS, CONVERSION_FACTORS,
    DEFAULT_VELOCITY, DEFAULT_ACCELERATION
)

class MotorController:
    def __init__(self):
        self.motor_ids = MOTOR_IDS
        self.conversion_factors = CONVERSION_FACTORS

    def move_motors(self, positions, velocity=DEFAULT_VELOCITY):
        # Implementation using settings
```

## System Architecture

### Core Components
1. **Settings Management**
   - settings.py
     * Central configuration hub
     * Type-annotated constants
     * Categorized settings
     * Documentation for all parameters

2. **Motor Control System**
   - DynamixelManager (dxl_manager.py)
     * Low-level motor communication
     * Hardware interaction layer
     * Bulk read/write operations

   - MotorController (motor_controller.py)
     * Unit conversion system
     * Motor state management
     * Position/velocity control

3. **Profile Management**
   - ProfileController (profile_controller.py)
     * Profile storage and retrieval
     * Movement sequence execution
     * Motor synchronization

4. **Focus System**
   - FocusController (focus.py)
     * Pan/tilt calculations
     * Position tracking
     * Auto-focus management

5. **Web Interface**
   - Flask Application (web_app.py)
     * REST API endpoints
     * Real-time updates
     * User interface

### Motor Control Patterns

#### 1. Unit Conversion System
```python
# settings.py
CONVERSION_FACTORS: Dict[str, float] = {
    "slider": 64 / 4096,     # mm per step
    "pan": 360 / 4096,       # degrees per step
    "tilt": 360 / 4096,      # degrees per step
    "turntable": 360 / 4096, # degrees per step
    "zoom": 360 / 4096,      # degrees per step
    "focus": 360 / 4096      # degrees per step
}

# motor_controller.py
from src.settings import CONVERSION_FACTORS, MOTOR_OFFSETS

def steps_to_units(self, steps, motor):
    value = steps * CONVERSION_FACTORS[motor]
    if motor in MOTOR_OFFSETS:
        return value - MOTOR_OFFSETS[motor]
    return value
```

#### 2. Motor Movement Patterns

1. **Primary Motors (Slider, Turntable, Zoom, Focus)**
   ```python
   # Using consolidated settings
   from src.settings import (
       MOTOR_IDS, DEFAULT_VELOCITY, DEFAULT_ACCELERATION
   )
   
   primary_velocity_dict = {
       MOTOR_IDS['turntable']: DEFAULT_VELOCITY,
       MOTOR_IDS['slider']: DEFAULT_VELOCITY,
       MOTOR_IDS['zoom']: DEFAULT_VELOCITY,
       MOTOR_IDS['focus']: DEFAULT_VELOCITY
   }
   ```

2. **Pan/Tilt Control**
   ```python
   from src.settings import (
       MOTOR_IDS, PAN_TILT_VELOCITY, PAN_TILT_ACCELERATION
   )
   
   pan_tilt_velocity = {
       MOTOR_IDS['pan']: PAN_TILT_VELOCITY,
       MOTOR_IDS['tilt']: PAN_TILT_VELOCITY
   }
   ```

### Movement Profile System

#### 1. Profile Structure
```json
{
    "name": "profile_name",
    "points": [
        {
            "positions": {
                "1": steps_turntable,
                "2": steps_slider,
                "5": steps_zoom,
                "6": steps_focus
            },
            "velocity": speed_value,
            "timestamp": time_value
        }
    ],
    "acceleration": global_accel
}
```

### Design Patterns

#### 1. Settings Access Pattern
```python
from src.settings import (
    MOTOR_IDS, CONVERSION_FACTORS,
    DEFAULT_VELOCITY, DEFAULT_ACCELERATION,
    PAN_TILT_VELOCITY, PAN_TILT_ACCELERATION
)

class Controller:
    def __init__(self):
        # Import all needed settings at initialization
        self.motor_ids = MOTOR_IDS
        self.conversion_factors = CONVERSION_FACTORS
        self.default_velocity = DEFAULT_VELOCITY
```

#### 2. Movement Coordination
```python
def execute_movement(positions, velocity=None):
    # Use default values from settings if not specified
    velocity = velocity or DEFAULT_VELOCITY
    
    # Set parameters using settings-based values
    set_primary_motor_params(velocity)
    set_pan_tilt_params(PAN_TILT_VELOCITY)
    
    # Execute movement with proper parameters
    move_motors(positions)
```

## Implementation Guidelines

### 1. Settings Usage
- Import only needed settings
- Use type hints for clarity
- Reference settings.py for documentation
- Use default values when appropriate

### 2. Configuration Management
- All constants in settings.py
- Clear categorization
- Comprehensive documentation
- Type annotations

### 3. Error Handling
- Hardware communication errors
- Position validation
- Movement timeout checks

## Web Interface Design System

### Web Settings Architecture
Similar to the main settings.py, the web interface has its own configuration system:

1. **Web Settings File Structure**
- `src/web/web_settings.py`: Central configuration for all web styling
- `src/web/static/css/base.css`: CSS implementation of web settings

2. **Key Configuration Areas**
```python
# Colors
- Primary colors (blue: #4a9eff)
- Background colors (black)
- Text colors (white, rgba variations)
- Border colors (rgba(255, 255, 255, 0.3))

# Typography
- Font families (Arial, monospace)
- Font sizes (12px to 24px)
- Line heights and spacing

# Component Dimensions
- Icon buttons (60x60px)
- Panels (300px width)
- Spacing units (10px, 15px, 20px)

# Animations
- Durations (0.2s, 0.3s)
- Timing functions (ease)
```

3. **Usage Pattern**
```python
from src.web.web_settings import COLORS, FONTS, COMPONENTS

class WebComponent:
    def __init__(self):
        self.primary_color = COLORS["primary"]
        self.font_family = FONTS["primary"]
        self.button_size = COMPONENTS["icon_button"]["size"]
```

### Implementation Guidelines
1. All web styling configurations in web_settings.py
2. Use base.css for shared styles
3. Follow consistent naming conventions
4. Document all parameters

## Future Considerations
1. Settings validation system
2. Hot-reload capability
3. Dynamic parameter adjustment
4. Configuration persistence
5. Settings backup/restore
6. Environment-specific settings
