# Camera Slider Project - System Architecture & Patterns

## System Architecture

### Core Components
1. **Motor Control System**
   - DynamixelManager (dxl_manager.py)
     * Low-level motor communication
     * Hardware interaction layer
     * Bulk read/write operations

   - MotorController (motor_controller.py)
     * Unit conversion system
     * Motor state management
     * Position/velocity control

2. **Profile Management**
   - ProfileController (profile_controller.py)
     * Profile storage and retrieval
     * Movement sequence execution
     * Motor synchronization

3. **Focus System**
   - FocusController (focus.py)
     * Pan/tilt calculations
     * Position tracking
     * Auto-focus management

4. **Web Interface**
   - Flask Application (web_app.py)
     * REST API endpoints
     * Real-time updates
     * User interface

### Motor Control Patterns

#### 1. Unit Conversion System
```python
class MotorController:
    CONVERSION_FACTORS = {
        "slider": 64 / 4096,     # mm per step
        "pan": 360 / 4096,       # degrees per step
        "tilt": 360 / 4096,      # degrees per step
        "turntable": 360 / 4096, # degrees per step
        "zoom": 360 / 4096,      # degrees per step
        "focus": 360 / 4096      # degrees per step
    }

    def steps_to_units(self, steps, motor):
        value = steps * CONVERSION_FACTORS[motor]
        if motor in MOTOR_OFFSETS:
            return value - MOTOR_OFFSETS[motor]
        return value
```

#### 2. Motor Movement Patterns

1. **Primary Motors (Slider, Turntable, Zoom, Focus)**
   ```python
   # Velocity/Acceleration Control
   primary_velocity_dict = {
       MOTOR_IDS['turntable']: velocity,
       MOTOR_IDS['slider']: velocity,
       MOTOR_IDS['zoom']: velocity,
       MOTOR_IDS['focus']: velocity
   }
   motor_controller.safe_dxl_operation(
       motor_controller.dxl.bulk_write_profile_velocity, 
       primary_velocity_dict
   )
   
   # Position Control
   positions = {int(motor_id): int(pos) for motor_id, pos in point['positions'].items()}
   motor_controller.safe_dxl_operation(
       motor_controller.dxl.bulk_write_goal_positions, 
       positions
   )
   ```

2. **Pan/Tilt Control**
   ```python
   # Optimized Parameters
   pan_tilt_velocity = {
       MOTOR_IDS['pan']: int(velocity * 1.2),  # Higher velocity for tracking
       MOTOR_IDS['tilt']: int(velocity * 1.2)
   }
   pan_tilt_accel = int(acceleration * 0.8)  # Lower acceleration for smoothness
   
   # Separate Movement Control
   pan_tilt_positions = {
       MOTOR_IDS['pan']: motor_controller.units_to_steps(motor_positions['pan'], 'pan'),
       MOTOR_IDS['tilt']: motor_controller.units_to_steps(motor_positions['tilt'], 'tilt')
   }
   motor_controller.safe_dxl_operation(
       motor_controller.dxl.bulk_write_goal_positions, 
       pan_tilt_positions
   )
   ```

3. **Position Monitoring**
   ```python
   # Primary Motors (±5 steps tolerance)
   for motor_id, target_pos in positions.items():
       current_pos = current_positions.get(motor_id, 0)
       if abs(current_pos - target_pos) >= 5:
           primary_reached = False
           break
   
   # Pan/Tilt Motors (±10 steps tolerance)
   for motor_id, target_pos in pan_tilt_positions.items():
       current_pos = current_positions.get(motor_id, 0)
       if abs(current_pos - target_pos) >= 10:
           pan_tilt_reached = False
           break
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

#### 2. Movement Coordination
1. Primary Motor Movement
   - Position setting
   - Speed/acceleration control
   - Position monitoring

2. Pan/Tilt Updates
   - Focus point calculation
   - Position adjustment
   - Real-time tracking

### Design Patterns

#### 1. Motor Control Abstraction
```python
class MotorController:
    def safe_dxl_operation(self, operation, params):
        """Thread-safe motor operations with error handling"""
        try:
            with self.dxl.lock:
                return operation(params)
        except Exception as e:
            print(f"Motor operation error: {e}")
            return None
```

#### 2. Movement Coordination
```python
def execute_movement(positions, velocity):
    # 1. Set parameters for primary motors
    set_primary_motor_params(velocity)
    
    # 2. Move primary motors
    move_primary_motors(positions)
    
    # 3. Calculate pan/tilt positions
    pan_tilt = calculate_pan_tilt_positions(positions)
    
    # 4. Set parameters for pan/tilt
    set_pan_tilt_params(velocity)
    
    # 5. Move pan/tilt motors
    move_pan_tilt_motors(pan_tilt)
    
    # 6. Monitor all positions
    wait_for_movement_completion()
```

#### 3. Profile Management
- JSON profile storage
- Real-time state updates
- Position tracking

## Implementation Guidelines

### 1. Motor Operations
- Use separate bulk_write for pan/tilt
- Maintain independent control paths
- Monitor positions separately

### 2. Profile Execution
- Sequence primary motor movements
- Calculate pan/tilt positions
- Implement smooth transitions

### 3. Error Handling
- Hardware communication errors
- Position validation
- Movement timeout checks

## Future Considerations
1. Enhanced synchronization
2. Advanced motion profiles
3. Expanded error recovery
4. Performance optimization
