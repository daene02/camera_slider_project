from flask import Flask, render_template, request, send_from_directory, jsonify
from src.dxl_manager import DynamixelManager
from src.focus import FocusController
import time
import os
import json
from threading import Thread, Event, Lock

app = Flask(__name__)

# Globale Variablen
playback_stop_event = Event()
tracking_stop_event = Event()
current_playback_thread = None
current_tracking_thread = None
dxl_lock = Lock()  # Lock für thread-sichere DXL Operationen

# Focus control
focus_points = []
focus_controller = None

# Background images for each page
PAGE_BACKGROUNDS = {
    'home': 'images/backgrounds/home-bg.jpg',
    'motor': 'images/backgrounds/motor-bg.jpg',
    'focus': 'images/backgrounds/focus-bg.jpg',
    'profiles': 'images/backgrounds/profiles-bg.jpg',
    'video': 'images/backgrounds/video-bg.jpg',
    'photo': 'images/backgrounds/photo-bg.jpg'
}

def get_background_image(endpoint):
    """Get the background image for the current page"""
    return PAGE_BACKGROUNDS.get(endpoint, PAGE_BACKGROUNDS['home'])

# Load focus points from JSON file
def load_focus_points():
    try:
        focus_points_path = os.path.join(os.path.dirname(__file__), 'profiles', 'focus_points.json')
        if os.path.exists(focus_points_path):
            with open(focus_points_path, 'r') as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f"Error loading focus points: {str(e)}")
        return []

# Save focus points to JSON file
def save_focus_points(points):
    try:
        focus_points_path = os.path.join(os.path.dirname(__file__), 'profiles', 'focus_points.json')
        os.makedirs(os.path.dirname(focus_points_path), exist_ok=True)
        with open(focus_points_path, 'w') as f:
            json.dump(points, f, indent=2)
    except Exception as e:
        print(f"Error saving focus points: {str(e)}")

# Routes
@app.route('/')
def home():
    return render_template('home.html', background_image=get_background_image('home'))

@app.route('/focus')
def focus():
    return render_template('focus.html', background_image=get_background_image('focus'))

@app.route('/motor')
def motor():
    motors = get_motor_status()
    if motors is None:
        return jsonify({"error": "Failed to get motor status"}), 500
    return render_template('motor.html', motors=motors, background_image=get_background_image('motor'))

@app.route('/profiles')
def profiles():
    try:
        # Get absolute path to the profiles directory
        current_dir = os.path.abspath(os.path.dirname(__file__))
        profile_dir = os.path.join(current_dir, 'profiles')
        print(f"Looking for profiles in: {profile_dir}")  # Debug print
        
        if not os.path.exists(profile_dir):
            os.makedirs(profile_dir)
            print(f"Created profiles directory at: {profile_dir}")
        
        # Get all JSON files except focus_points.json
        profiles = []
        profile_files = [f for f in os.listdir(profile_dir) 
                        if f.endswith('.json') and f != 'focus_points.json']
        
        for filename in profile_files:
            profile_name = filename[:-5]  # Remove .json extension
            print(f"Found profile: {profile_name}")  # Debug print
            try:
                # Verify the profile can be loaded
                profile_path = os.path.join(profile_dir, filename)
                with open(profile_path, 'r') as f:
                    json.load(f)  # Try to load the JSON to verify it's valid
                profiles.append(profile_name)
            except Exception as e:
                print(f"Error loading profile {filename}: {str(e)}")
                continue
        
        print(f"Total valid profiles found: {len(profiles)}")  # Debug print
        return render_template('profiles.html', profiles=profiles, background_image=get_background_image('profiles'))
    except Exception as e:
        print(f"Error in profiles route: {str(e)}")
        import traceback
        traceback.print_exc()  # Print full stack trace
        return render_template('profiles.html', profiles=[], background_image=get_background_image('profiles'))

@app.route('/video')
def video():
    return render_template('video.html', background_image=get_background_image('video'))

@app.route('/photo')
def photo():
    return render_template('photo.html', background_image=get_background_image('photo'))

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

# Conversion factors
CONVERSION_FACTORS = {
    "slider": 64 / 4096,     # 1 rotation = 64mm
    "pan": 360 / 4096,       # 1 rotation = 360 degrees
    "tilt": 360 / 4096,      # 1 rotation = 360 degrees
    "focus": 360 / 4096      # 1 rotation = 360 degrees
}

# Motor offsets
MOTOR_OFFSETS = {
    "pan": 180,
    "tilt": 180
}

# Motor IDs und Namen
MOTOR_IDS = {
    "turntable": 1,
    "slider": 2,
    "pan": 3,
    "tilt": 4,
    "zoom": 5,
    "focus": 6
}

MOTOR_NAMES = {
    1: "Turntable",
    2: "Slider",
    3: "Pan",
    4: "Tilt",
    5: "Zoom",
    6: "Focus"
}

dxl = DynamixelManager()

def safe_dxl_operation(func, *args, **kwargs):
    """Thread-sichere DXL Operationen ausführen"""
    with dxl_lock:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"DXL Operation error: {str(e)}")
            return None

@app.route('/torque/all', methods=['POST'])
def toggle_all_torque():
    enable = request.json.get('enable', False)
    if enable:
        safe_dxl_operation(dxl.enable_torque)
    else:
        safe_dxl_operation(dxl.disable_torque)
    return jsonify({"success": True})

@app.route('/torque/<int:motor_id>', methods=['POST'])
def toggle_motor_torque(motor_id):
    enable = request.json.get('enable', False)
    if enable:
        safe_dxl_operation(dxl.enable_torque, [motor_id])
    else:
        safe_dxl_operation(dxl.disable_torque, [motor_id])
    return jsonify({"success": True})


@app.route('/motor/<int:motor_id>/position', methods=['POST'])
def update_motor_position(motor_id):
    try:
        position = int(request.json.get('position', 512))
        safe_dxl_operation(dxl.bulk_write_goal_positions, {motor_id: position})
        return jsonify({"success": True})
    except ValueError:
        return jsonify({"error": "Invalid position value"}), 400

@app.route('/motor/<int:motor_id>/velocity', methods=['POST'])
def update_motor_velocity(motor_id):
    try:
        velocity = int(request.json.get('velocity', 100))
        safe_dxl_operation(dxl.bulk_write_profile_velocity, {motor_id: velocity})
        return jsonify({"success": True})
    except ValueError:
        return jsonify({"error": "Invalid velocity value"}), 400

@app.route('/motor/<int:motor_id>/acceleration', methods=['POST'])
def update_motor_acceleration(motor_id):
    try:
        acceleration = int(request.json.get('acceleration', 50))
        safe_dxl_operation(dxl.bulk_write_profile_acceleration, {motor_id: acceleration})
        return jsonify({"success": True})
    except ValueError:
        return jsonify({"error": "Invalid acceleration value"}), 400

@app.route('/motor/status')
def motor_status():
    motors = get_motor_status()
    if motors is None:
        return jsonify({"error": "Failed to get motor status"}), 500
    return jsonify(motors)

def get_motor_status():
    try:
        motors = []
        # Bulk-Read für alle Werte auf einmal
        positions = safe_dxl_operation(dxl.bulk_read_positions) or {}
        temperatures = safe_dxl_operation(dxl.bulk_read_temperature) or {}
        voltages = safe_dxl_operation(dxl.bulk_read_voltage) or {}
        currents = safe_dxl_operation(dxl.bulk_read_current) or {}
        velocities = safe_dxl_operation(dxl.bulk_read_profile_velocity) or {}
        accels = safe_dxl_operation(dxl.bulk_read_profile_acceleration) or {}
        torque_states = safe_dxl_operation(dxl.bulk_read_torque_enable) or {}
        
        for motor_id in dxl.dxl_ids:
            motors.append({
                "id": motor_id,
                "name": MOTOR_NAMES.get(motor_id, f"Motor {motor_id}"),
                "position": positions.get(motor_id, 0),
                "temperature": temperatures.get(motor_id, 0),
                "voltage": voltages.get(motor_id, 0) / 10.0,  # Konvertierung zu Volt
                "current": currents.get(motor_id, 0),
                "speed": velocities.get(motor_id, 0),
                "load": accels.get(motor_id, 0),
                "torque_enabled": torque_states.get(motor_id, False)
            })
        return motors
    except Exception as e:
        print(f"Error in get_motor_status: {str(e)}")
        return None


@app.route('/motors/positions')
def get_motor_positions():
    positions = safe_dxl_operation(dxl.bulk_read_positions)
    if positions is None:
        return jsonify({"error": "Failed to read positions"}), 500
    return jsonify(positions)

@app.route('/profile/list')
def list_profiles():
    try:
        current_dir = os.path.abspath(os.path.dirname(__file__))
        profile_dir = os.path.join(current_dir, 'profiles')
        
        if not os.path.exists(profile_dir):
            os.makedirs(profile_dir)
            
        # Get all JSON files except focus_points.json
        profiles = []
        for f in os.listdir(profile_dir):
            if f.endswith('.json') and f != 'focus_points.json':
                profile_name = f[:-5]  # Remove .json extension
                try:
                    # Verify profile can be loaded
                    with open(os.path.join(profile_dir, f), 'r') as file:
                        json.load(file)
                    profiles.append(profile_name)
                except Exception as e:
                    print(f"Error verifying profile {f}: {str(e)}")
                    continue
                    
        return jsonify(profiles)
    except Exception as e:
        print(f"Error listing profiles: {str(e)}")
        return jsonify([])

@app.route('/profile/<name>')
def get_profile(name):
    try:
        current_dir = os.path.abspath(os.path.dirname(__file__))
        profile_path = os.path.join(current_dir, 'profiles', f'{name}.json')
        print(f"Attempting to load profile from: {profile_path}")  # Debug print
        
        if not os.path.exists(profile_path):
            print(f"Profile file not found: {profile_path}")
            return jsonify({'error': 'Profile not found'}), 404
            
        with open(profile_path, 'r') as f:
            profile_data = json.load(f)
            print(f"Successfully loaded profile: {name}")  # Debug print
            return jsonify(profile_data)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON for profile {name}: {str(e)}")
        return jsonify({'error': 'Invalid profile format'}), 400
    except Exception as e:
        print(f"Error loading profile {name}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/profile/save', methods=['POST'])
def save_profile():
    try:
        profile = request.json
        profile_dir = os.path.join(os.path.dirname(__file__), 'profiles')
        if not os.path.exists(profile_dir):
            os.makedirs(profile_dir)
        
        profile_path = os.path.join(profile_dir, f'{profile["name"]}.json')
        with open(profile_path, 'w') as f:
            json.dump(profile, f, indent=2)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_focus_point(focus_config):
    """Get focus point from configuration, either from saved points or direct coordinates"""
    if focus_config['mode'] == 'point':
        point_index = focus_config['point'].get('index')
        if point_index is not None and 0 <= point_index < len(focus_points):
            return focus_points[point_index]
        return {
            'x': focus_config['point']['x'],
            'y': focus_config['point']['y'],
            'z': focus_config['point']['z']
        }
    return None

def apply_focus_tracking(focus_config, controller, current_slider_pos):
    """Apply focus tracking based on configuration"""
    try:
        if focus_config['mode'] == 'point':
            point = get_focus_point(focus_config)
            if point:
                motor_positions = controller.get_motor_positions(current_slider_pos)
                return {
                    MOTOR_IDS['pan']: units_to_steps(motor_positions['pan'], 'pan'),
                    MOTOR_IDS['tilt']: units_to_steps(motor_positions['tilt'], 'tilt'),
                    MOTOR_IDS['focus']: units_to_steps(motor_positions['focus'], 'focus')
                }
        elif focus_config['mode'] == 'direct':
            values = focus_config['values']
            return {
                MOTOR_IDS['pan']: units_to_steps(values['pan'], 'pan'),
                MOTOR_IDS['tilt']: units_to_steps(values['tilt'], 'tilt'),
                MOTOR_IDS['focus']: values['focus']
            }
    except Exception as e:
        print(f"Error in focus tracking: {str(e)}")
    return {}

def run_profile(profile, settings):
    global playback_stop_event, focus_controller
    
    try:
        # Set velocity and acceleration
        velocity_dict = {motor_id: int(settings['velocity']) for motor_id in dxl.dxl_ids}
        accel_dict = {motor_id: int(settings['acceleration']) for motor_id in dxl.dxl_ids}
        
        safe_dxl_operation(dxl.bulk_write_profile_velocity, velocity_dict)
        safe_dxl_operation(dxl.bulk_write_profile_acceleration, accel_dict)

        # Configure focus tracking
        continuous_focus = settings.get('continuous_focus', True)
        focus_update_rate = settings.get('focus_update_rate', 50) / 1000.0  # Convert to seconds

        # Process each point in the sequence
        for point in profile['points']:
            if playback_stop_event.is_set():
                break

            # Get base positions
            positions = {int(motor_id): int(pos) for motor_id, pos in point['positions'].items()}

            # Apply focus configuration
            if 'focus' in point:
                focus_pos = apply_focus_tracking(
                    point['focus'],
                    focus_controller,
                    steps_to_units(positions[MOTOR_IDS['slider']], 'slider')
                )
                positions.update(focus_pos)

            # Move to position
            safe_dxl_operation(dxl.bulk_write_goal_positions, positions)
            
            # Wait for position with continuous focus updates
            while not playback_stop_event.is_set():
                current_positions = safe_dxl_operation(dxl.bulk_read_positions)
                if not current_positions:
                    time.sleep(focus_update_rate)
                    continue

                # Update focus if continuous tracking is enabled
                if continuous_focus and 'focus' in point:
                    slider_pos = steps_to_units(current_positions[MOTOR_IDS['slider']], 'slider')
                    focus_pos = apply_focus_tracking(point['focus'], focus_controller, slider_pos)
                    if focus_pos:
                        safe_dxl_operation(dxl.bulk_write_goal_positions, focus_pos)

                # Check if target position is reached
                all_reached = True
                for motor_id, target_pos in positions.items():
                    if motor_id in [MOTOR_IDS['pan'], MOTOR_IDS['tilt'], MOTOR_IDS['focus']]:
                        continue  # Skip focus-related motors in position check
                    current_pos = current_positions.get(motor_id, 0)
                    if abs(current_pos - target_pos) >= 5:
                        all_reached = False
                        break
                
                if all_reached:
                    break
                
                time.sleep(focus_update_rate)
                
    except Exception as e:
        print(f"Error in profile playback: {str(e)}")
    finally:
        playback_stop_event.clear()

@app.route('/profile/play', methods=['POST'])
def play_profile():
    global current_playback_thread, playback_stop_event
    
    try:
        if current_playback_thread and current_playback_thread.is_alive():
            return jsonify({'error': 'Playback already in progress'}), 400
            
        data = request.json
        profile = data['profile']
        settings = data['settings']
        
        playback_stop_event.clear()
        current_playback_thread = Thread(target=run_profile, args=(profile, settings))
        current_playback_thread.start()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/profile/stop', methods=['POST'])
def stop_profile():
    global playback_stop_event
    try:
        playback_stop_event.set()
        current_positions = safe_dxl_operation(dxl.bulk_read_positions)
        if current_positions:
            safe_dxl_operation(dxl.bulk_write_goal_positions, current_positions)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Focus control routes
@app.route('/focus/points', methods=['GET'])
def get_focus_points():
    return jsonify(focus_points)

@app.route('/focus/point/<int:index>', methods=['GET', 'DELETE'])
def manage_focus_point(index):
    if request.method == 'GET':
        if 0 <= index < len(focus_points):
            return jsonify(focus_points[index])
        return jsonify({"error": "Point not found"}), 404
    elif request.method == 'DELETE':
        if 0 <= index < len(focus_points):
            focus_points.pop(index)
            return jsonify({"success": True})
        return jsonify({"error": "Point not found"}), 404

@app.route('/focus/save_point', methods=['POST'])
def save_focus_point():
    point = request.json
    if all(k in point for k in ('x', 'y', 'z')):
        focus_points.append(point)
        return jsonify({"success": True})
    return jsonify({"error": "Invalid point data"}), 400

def steps_to_units(steps, motor):
    """Convert motor steps to real units (mm or degrees)"""
    value = steps * CONVERSION_FACTORS[motor]
    if motor in MOTOR_OFFSETS:
        return value - MOTOR_OFFSETS[motor]
    return value

def units_to_steps(units, motor):
    """Convert real units (mm or degrees) to motor steps"""
    if motor in MOTOR_OFFSETS:
        units += MOTOR_OFFSETS[motor]
    return round(units / CONVERSION_FACTORS[motor])

def track_focus_point(point):
    """Background task for focus tracking"""
    global focus_controller
    
    if focus_controller is None:
        focus_controller = FocusController(object_position=(point['x'], point['y'], point['z']))
    else:
        focus_controller.object_x = point['x']
        focus_controller.object_y = point['y']
        focus_controller.object_z = point['z']
    
    try:
        safe_dxl_operation(dxl.enable_torque)
        
        while not tracking_stop_event.is_set():
            positions = safe_dxl_operation(dxl.bulk_read_positions)
            if not positions:
                time.sleep(0.1)
                continue
                
            # Get current slider position in mm
            slider_pos = steps_to_units(positions[MOTOR_IDS['slider']], 'slider')
            
            # Calculate motor positions for current slider position
            motor_positions = focus_controller.get_motor_positions(slider_pos)
            
            # Convert angles to steps
            target_positions = {
                MOTOR_IDS['pan']: units_to_steps(motor_positions['pan'], 'pan'),
                MOTOR_IDS['tilt']: units_to_steps(motor_positions['tilt'], 'tilt'),
                MOTOR_IDS['focus']: units_to_steps(motor_positions['focus'], 'focus')
            }
            
            safe_dxl_operation(dxl.bulk_write_goal_positions, target_positions)
            time.sleep(0.05)  # 50ms update interval
            
    except Exception as e:
        print(f"Error during focus tracking: {str(e)}")
    finally:
        tracking_stop_event.clear()
        if not playback_stop_event.is_set():  # Only disable if not in playback mode
            safe_dxl_operation(dxl.disable_torque)

@app.route('/focus/start_tracking', methods=['POST'])
def start_focus_tracking():
    global current_tracking_thread
    
    if current_tracking_thread and current_tracking_thread.is_alive():
        return jsonify({"error": "Tracking already in progress"}), 400
    
    point = request.json
    if not all(k in point for k in ('x', 'y', 'z')):
        return jsonify({"error": "Invalid point data"}), 400
    
    tracking_stop_event.clear()
    current_tracking_thread = Thread(target=track_focus_point, args=(point,))
    current_tracking_thread.start()
    
    return jsonify({"success": True})

@app.route('/focus/stop_tracking', methods=['POST'])
def stop_focus_tracking():
    tracking_stop_event.set()
    return jsonify({"success": True})

if __name__ == '__main__':
    # Load focus points on startup
    focus_points = load_focus_points()
    print("Loaded focus points:", focus_points)
    
    # Debug: Print all available profiles
    profile_dir = os.path.join(os.path.dirname(__file__), 'profiles')
    if os.path.exists(profile_dir):
        print("Available profiles in", profile_dir + ":")
        for f in os.listdir(profile_dir):
            print(" -", f)
    else:
        print("Profile directory not found:", profile_dir)
    
    app.run(host='0.0.0.0', port=5000)
