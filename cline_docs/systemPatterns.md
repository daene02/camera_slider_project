# Camera Slider Project - System Patterns

## Architecture Overview
The system follows a modular architecture with clear separation of concerns:

### Core Components
1. **Camera Slider Control** (camera_slider.py)
   - Handles physical motor control
   - Manages movement sequences
   - Coordinates multi-axis motion

2. **Focus System** (focus.py)
   - Calculates pan/tilt angles
   - Manages focus adjustments
   - Implements position-based tracking

3. **Motor Management** (dxl_manager.py)
   - Low-level motor control
   - Communication with hardware
   - Motor state management

4. **Settings Management** (settings.py)
   - System configuration
   - Motor limits
   - Conversion factors

### Key Technical Patterns
1. **Motion Control**
   - Coordinated multi-motor movement
   - Position-based calculations
   - Smooth acceleration/deceleration

2. **Focus Tracking**
   - Trigonometric calculations for angles
   - Distance-based focus adjustment
   - Real-time position updates

3. **Hardware Abstraction**
   - Modular motor control
   - Hardware-independent calculations
   - Configurable parameters

## Design Decisions
1. Python-based implementation for:
   - Hardware control flexibility
   - Math library support
   - Easy integration with web interfaces

2. Modular architecture allowing:
   - Independent component testing
   - Easy maintenance
   - Feature expansion

3. Web interface integration for:
   - Remote control capability
   - Real-time monitoring
   - User-friendly operation
