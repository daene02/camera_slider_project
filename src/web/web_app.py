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

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/focus')
def focus():
    return render_template('focus.html')

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

@app.route('/motor', methods=['GET'])
def motor():
    motors = get_motor_status()
    if motors is None:
        return jsonify({"error": "Failed to get motor status"}), 500
    return render_template('motor.html', motors=motors)

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

@app.route('/video')
def video():
    return render_template('video.html')

@app.route('/photo')
def photo():
    return render_template('photo.html')

@app.route('/profiles')
def profiles():
    try:
        profile_dir = os.path.join(os.path.dirname(__file__), 'profiles')
        if not os.path.exists(profile_dir):
            os.makedirs(profile_dir)
        profiles = [f[:-5] for f in os.listdir(profile_dir) if f.endswith('.json')]
        return render_template('profiles.html', profiles=profiles)
    except Exception as e:
        print(f"Error loading profiles: {str(e)}")
        return render_template('profiles.html', profiles=[])

@app.route('/motors/positions')
def get_motor_positions():
    positions = safe_dxl_operation(dxl.bulk_read_positions)
    if positions is None:
        return jsonify({"error": "Failed to read positions"}), 500
    return jsonify(positions)

@app.route('/profile/<name>')
def get_profile(name):
    try:
        profile_path = os.path.join(os.path.dirname(__file__), 'profiles', f'{name}.json')
        with open(profile_path, 'r') as f:
            return jsonify(json.load(f))
    except Exception as e:
        return jsonify({'error': str(e)}), 404

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

def run_profile(profile, settings):
    global playback_stop_event
    
    try:
        # Geschwindigkeit und Beschleunigung für alle Motoren setzen
        velocity_dict = {motor_id: int(settings['velocity']) for motor_id in dxl.dxl_ids}
        accel_dict = {motor_id: int(settings['acceleration']) for motor_id in dxl.dxl_ids}
        
        safe_dxl_operation(dxl.bulk_write_profile_velocity, velocity_dict)
        safe_dxl_operation(dxl.bulk_write_profile_acceleration, accel_dict)

        # Fokus-Modus aktivieren wenn gewünscht
        if settings.get('focusMode', False):
            # TODO: Implementiere Fokus-Modus-Logik
            pass

        # Für jeden Punkt die Motoren bewegen
        for point in profile['points']:
            if playback_stop_event.is_set():
                break

            # Konvertiere alle Positions-Werte zu Integers
            positions = {int(motor_id): int(pos) for motor_id, pos in point['positions'].items()}
            safe_dxl_operation(dxl.bulk_write_goal_positions, positions)
            
            # Warten bis die Motoren die Position erreicht haben
            while not playback_stop_event.is_set():
                current_positions = safe_dxl_operation(dxl.bulk_read_positions)
                if not current_positions:
                    time.sleep(0.1)
                    continue
                    
                all_reached = True
                for motor_id, target_pos in positions.items():
                    current_pos = current_positions.get(motor_id, 0)
                    if abs(current_pos - target_pos) >= 5:
                        all_reached = False
                        break
                
                if all_reached:
                    break
                    
                time.sleep(0.1)
                
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
    app.run(host='0.0.0.0', port=5000)
