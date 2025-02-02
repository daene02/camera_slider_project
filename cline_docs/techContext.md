# Camera Slider Project - Technical Specifications

## Current Implementation Details

### Motor Control System
1. **Hardware Interface**
   - Dynamixel Protocol 2.0
   - Servo Motors:
     * ID 1: Turntable (360° rotation)
     * ID 2: Slider (500mm linear travel)
     * ID 3: Pan (-180° to +180°)
     * ID 4: Tilt (-180° to +180°)
     * ID 5: Zoom (360° rotation)
     * ID 6: Focus (360° rotation)

2. **Communication Parameters**
   - Baudrate: 57600
   - Device: /dev/ttyUSB0
   - Protocol Version: 2.0

### Software Architecture
1. **Core Components**
   ```python
   # Motor Manager
   class DynamixelManager:
       - bulk_read_positions()
       - bulk_write_goal_positions()
       - bulk_read_profile_velocity()
       - bulk_write_profile_velocity()

   # Motor Controller
   class MotorController:
       - steps_to_units()
       - units_to_steps()
       - update_motor_position()
       - get_motor_status()

   # Profile Controller
   class ProfileController:
       - run_profile()
       - start_playback()
       - stop_playback()
   ```

2. **Unit Conversion System**
   - Steps to Physical Units:
     * Slider: 64mm per rotation (4096 steps)
     * Rotation Motors: 360° per rotation (4096 steps)
   - Conversion Precision: 2 decimal places
   - Position Ranges:
     * Slider: 0-500mm
     * Pan/Tilt: -180° to +180°
     * Others: 0-360°

### Current Implementation Details

1. **Motor Control Architecture**
   ```python
   # Primary Motor Control
   def control_primary_motors(positions, velocity, acceleration):
       # Set velocity/acceleration
       primary_params = {
           MOTOR_IDS['turntable']: velocity,
           MOTOR_IDS['slider']: velocity,
           MOTOR_IDS['zoom']: velocity,
           MOTOR_IDS['focus']: velocity
       }
       dxl.bulk_write_profile_velocity(primary_params)
       
       # Move to position
       dxl.bulk_write_goal_positions(positions)

   # Pan/Tilt Control
   def control_pan_tilt(positions, base_velocity, base_acceleration):
       # Optimized parameters
       velocity = base_velocity * 1.2  # 20% faster
       acceleration = base_acceleration * 0.8  # 20% slower
       
       params = {
           MOTOR_IDS['pan']: velocity,
           MOTOR_IDS['tilt']: velocity
       }
       dxl.bulk_write_profile_velocity(params)
       
       # Separate movement
       dxl.bulk_write_goal_positions(positions)
   ```

2. **Movement Coordination**
   ```python
   # Implemented Solution
   def execute_movement(profile_point):
       # 1. Primary motors first
       primary_positions = extract_primary_positions(profile_point)
       control_primary_motors(primary_positions, velocity, acceleration)
       
       # 2. Calculate and move pan/tilt
       pan_tilt = calculate_pan_tilt_positions(slider_position)
       control_pan_tilt(pan_tilt, velocity, acceleration)
       
       # 3. Monitor positions independently
       wait_for_completion(
           primary_tolerance=5,  # ±5 steps
           pan_tilt_tolerance=10 # ±10 steps
       )
   ```

### Development Environment
1. **System Requirements**
   - OS: Linux
   - Python: 3.x
   - Libraries:
     * dynamixel_sdk
     * numpy
     * flask

2. **Hardware Setup**
   - USB Connection
   - Motor Power Supply
   - Linear Rail System
   - Pan/Tilt Mount

### Performance Specifications

1. **Movement Parameters**
   ```python
   PARAMETERS = {
       'primary': {
           'velocity_scale': 1.0,    # Base velocity
           'acceleration_scale': 1.0, # Base acceleration
           'position_tolerance': 5    # ±5 steps
       },
       'pan_tilt': {
           'velocity_scale': 1.2,    # 20% faster for tracking
           'acceleration_scale': 0.8, # 20% slower for smoothness
           'position_tolerance': 10   # ±10 steps
       }
   }
   ```

2. **Timing Characteristics**
   - Position Update Interval: 50ms
   - Movement Completion Check: Every 50ms
   - Profile Point Transition: After both groups reach position
   - Pan/Tilt Response Time: < 100ms

3. **Position Control**
   - Slider Precision: ±0.1mm
   - Angular Precision: ±0.1°
   - Step Resolution: 4096 steps/rotation
   - Continuous Position Monitoring

4. **Communication**
   - Protocol: Dynamixel 2.0
   - Baudrate: 57600
   - Separate Bulk Operations:
     * Primary Motor Updates
     * Pan/Tilt Updates
     * Position Monitoring

## Technical Requirements

1. **Motor Control System**
   - ✓ Independent Control Paths
   - ✓ Optimized Movement Parameters
   - ✓ Separate Position Monitoring
   - ✓ Thread-safe Operations

2. **Profile System**
   - ✓ Sequential Movement Control
   - ✓ Parameter Optimization
   - ✓ Position Validation
   - ✓ Error Handling

3. **Performance Targets**
   - Movement Smoothness: No visible jerking
   - Position Accuracy: Within tolerance
   - Profile Playback: Continuous motion
   - Pan/Tilt Tracking: Real-time response

4. **System Integration**
   - Hardware Interface: Dynamixel SDK
   - Web Interface: Flask/JSON API
   - Profile Storage: JSON files
   - Real-time Monitoring: Websocket updates

## Development Guidelines

1. **Code Structure**
   - Maintain separation of concerns
   - Clear error handling
   - Comprehensive logging

2. **Testing Requirements**
   - Unit conversion accuracy
   - Movement synchronization
   - Profile playback stability

3. **Documentation Needs**
   - API documentation
   - Configuration guide
   - Troubleshooting procedures
