from flask import Flask, render_template, request, send_from_directory, jsonify
from src.web.controllers.motor_controller import motor_controller
from src.web.controllers.profile_controller import profile_controller
from src.web.controllers.focus_controller import focus_controller
from src.web.routes.camera_routes import camera_routes, cleanup_streamer
import asyncio
import logging
import time

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Register blueprints
app.register_blueprint(camera_routes, url_prefix='/camera')

# Background images for each page
PAGE_BACKGROUNDS = {
    'home': 'images/backgrounds/home-bg.jpg',
    'motor': 'images/backgrounds/motor-bg.jpg',
    'focus': 'images/backgrounds/focus-bg.jpg',
    'profiles': 'images/backgrounds/profiles-bg.jpg',
    'video': 'images/backgrounds/video-bg.jpg',
    'photo': 'images/backgrounds/photo-bg.jpg'
}

def run_async(coro):
    """Helper to run coroutines in Flask routes."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

def get_background_image(endpoint):
    """Get the background image for the current page"""
    return PAGE_BACKGROUNDS.get(endpoint, PAGE_BACKGROUNDS['home'])

# Main page routes
@app.route('/')
def home():
    return render_template('home.html', background_image=get_background_image('home'))

@app.route('/focus')
def focus():
    return render_template('focus.html', background_image=get_background_image('focus'))

# Motor operation timeout
MOTOR_OPERATION_TIMEOUT = 1.0  # 1 second timeout

@app.route('/motor')
def motor():
    try:
        start_time = time.time()
        motors = motor_controller.get_motor_status()
        
        # Check for timeout
        if time.time() - start_time > MOTOR_OPERATION_TIMEOUT:
            logger.warning("Motor status request timed out")
            motors = []
        elif motors is None:
            logger.error("Failed to get motor status")
            motors = []
            
        return render_template(
            'motor.html',
            motors=motors,
            background_image=get_background_image('motor')
        )
    except Exception as e:
        logger.error(f"Error in motor route: {str(e)}")
        return render_template(
            'motor.html',
            motors=[],
            background_image=get_background_image('motor')
        )

@app.route('/profiles')
def profiles():
    try:
        profiles_list = profile_controller.list_profiles()
        return render_template('profiles.html', profiles=profiles_list, background_image=get_background_image('profiles'))
    except Exception as e:
        logger.error(f"Error in profiles route: {str(e)}", exc_info=True)
        return render_template('profiles.html', profiles=[], background_image=get_background_image('profiles'))

@app.route('/video')
def video():
    return render_template('video.html', background_image=get_background_image('video'))

@app.route('/photo')
def photo():
    return render_template('photo.html', background_image=get_background_image('photo'))

@app.route('/focus/visualization')
def focus_visualization():
    """Render the focus visualization page."""
    return render_template('focus_visualization.html', background_image=get_background_image('focus'))

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

# Motor control routes
@app.route('/torque/all', methods=['POST'])
def toggle_all_torque():
    enable = request.json.get('enable', False)
    motor_controller.toggle_torque(enable=enable)
    return jsonify({"success": True})

@app.route('/torque/<int:motor_id>', methods=['POST'])
def toggle_motor_torque(motor_id):
    enable = request.json.get('enable', False)
    motor_controller.toggle_torque(motor_id=motor_id, enable=enable)
    return jsonify({"success": True})

@app.route('/motor/<int:motor_id>/position', methods=['POST'])
def update_motor_position(motor_id):
    try:
        position = int(request.json.get('position', 512))
        # Für den Slider (ID 2) immer False, für andere True als Standard
        use_prediction = request.json.get('use_prediction', motor_id != 2)
        motor_controller.update_motor_position(motor_id, position, use_prediction)
        return jsonify({"success": True})
    except ValueError as e:
        return jsonify({"error": "Invalid position value"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/motors/profile', methods=['POST'])
def move_motors_profile():
    """Bewegung mehrerer Motoren mit Bewegungsprofil"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        positions = data.get('positions', {})
        duration = float(data.get('duration', 2.0))
        
        # Validiere Positionen
        try:
            positions = {int(k): int(v) for k, v in positions.items()}
        except ValueError:
            return jsonify({"error": "Invalid position values"}), 400
            
        if not positions:
            return jsonify({"error": "No positions provided"}), 400
            
        # Führe Bewegung aus
        motor_controller.move_motors_profile(positions, duration)
        return jsonify({"success": True})
        
    except Exception as e:
        logger.error(f"Error in move_motors_profile: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/motor/<int:motor_id>/velocity', methods=['POST'])
def update_motor_velocity(motor_id):
    try:
        velocity = int(request.json.get('velocity', 100))
        motor_controller.update_motor_velocity(motor_id, velocity)
        return jsonify({"success": True})
    except ValueError:
        return jsonify({"error": "Invalid velocity value"}), 400

@app.route('/motor/<int:motor_id>/acceleration', methods=['POST'])
def update_motor_acceleration(motor_id):
    try:
        acceleration = int(request.json.get('acceleration', 50))
        motor_controller.update_motor_acceleration(motor_id, acceleration)
        return jsonify({"success": True})
    except ValueError:
        return jsonify({"error": "Invalid acceleration value"}), 400

@app.route('/motor/pid', methods=['GET'])
def get_pid_values():
    """Liest die PID-Werte aller Motoren"""
    try:
        pid_values = motor_controller.manager.bulk_read_pid_gains()
        return jsonify(pid_values)
    except Exception as e:
        logger.error(f"Error reading PID values: {str(e)}")
        return jsonify({"error": "Failed to read PID values"}), 500

@app.route('/motor/pid', methods=['POST'])
def set_pid_values():
    """Setzt die PID-Werte für ausgewählte Motoren"""
    try:
        pid_dict = request.json
        if not pid_dict:
            return jsonify({"error": "No PID values provided"}), 400
            
        # Validiere die Eingabedaten
        for motor_id, gains in pid_dict.items():
            if not isinstance(gains, dict):
                return jsonify({"error": f"Invalid gain format for motor {motor_id}"}), 400
            if not all(k in gains for k in ('p', 'i', 'd')):
                return jsonify({"error": f"Missing PID values for motor {motor_id}"}), 400
            
            # Konvertiere zu Integers und validiere Bereiche
            try:
                gains['p'] = int(gains['p'])
                gains['i'] = int(gains['i'])
                gains['d'] = int(gains['d'])
                
                # Validiere Wertebereiche (beispielhaft)
                if not (0 <= gains['p'] <= 16383 and
                       0 <= gains['i'] <= 16383 and
                       0 <= gains['d'] <= 16383):
                    return jsonify({"error": f"PID values out of range for motor {motor_id}"}), 400
            except ValueError:
                return jsonify({"error": f"Invalid PID values for motor {motor_id}"}), 400
        
        success = motor_controller.manager.bulk_write_pid_gains(pid_dict)
        if success:
            # Lese die Werte zur Bestätigung
            new_values = motor_controller.manager.bulk_read_pid_gains()
            return jsonify({
                "success": True,
                "values": new_values
            })
        return jsonify({"error": "Failed to write PID values"}), 500
            
    except Exception as e:
        logger.error(f"Error setting PID values: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/motor/status')
def motor_status():
    try:
        start_time = time.time()
        motors = motor_controller.get_motor_status()
        
        # Check for timeout
        if time.time() - start_time > MOTOR_OPERATION_TIMEOUT:
            logger.warning("Motor status request timed out")
            return jsonify({"error": "Operation timed out"}), 504
            
        if motors is None:
            return jsonify({"error": "Failed to get motor status"}), 500
            
        return jsonify(motors)
    except Exception as e:
        logger.error(f"Error in motor status: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/motors/positions')
def get_motor_positions():
    """Liest gefilterte Motorpositionen und -zustände"""
    try:
        motors = motor_controller.get_motor_status()
        if motors is None:
            return jsonify({"error": "Failed to read positions"}), 500
            
        # Extrahiere nur die relevanten Zustandsdaten
        states = {
            motor["id"]: {
                "position": motor["position"],
                "velocity": motor["filtered_velocity"],
                "acceleration": motor["filtered_acceleration"]
            }
            for motor in motors
        }
        return jsonify(states)
    except Exception as e:
        logger.error(f"Error reading motor positions: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

# Focus control routes
@app.route('/focus/points', methods=['GET'])
def get_focus_points():
    logger.debug("Fetching focus points")
    logger.debug(f"Current focus points: {focus_controller.focus_points}")
    return jsonify(focus_controller.focus_points)

@app.route('/focus/point/<int:point_id>', methods=['GET', 'PUT', 'DELETE'])
def manage_focus_point(point_id):
    if request.method == 'GET':
        point = focus_controller.get_focus_point(point_id)
        if point:
            return jsonify(point)
        return jsonify({"error": "Point not found"}), 404
    elif request.method == 'PUT':
        success, result = focus_controller.update_focus_point(point_id, request.json)
        if success:
            return jsonify(result)
        return jsonify({"error": result}), 400
    elif request.method == 'DELETE':
        success, error = focus_controller.remove_focus_point(point_id)
        if success:
            return jsonify({"success": True})
        return jsonify({"error": error}), 404

@app.route('/focus/save_point', methods=['POST'])
def save_focus_point():
    success, point = focus_controller.add_focus_point(request.json)
    if success:
        return jsonify({"success": True, "point": point})
    return jsonify({"error": "Invalid point data"}), 400

@app.route('/focus/manual', methods=['POST'])
def set_manual_focus():
    """Set manual focus position"""
    try:
        focus_value = request.json.get('focus_value')
        if focus_value is None:
            return jsonify({"error": "No focus value provided"}), 400

        success, result = focus_controller.set_manual_focus(focus_value)
        if success:
            return jsonify({
                "success": True,
                "focus_value": result
            })
        return jsonify({"error": result}), 400
    except Exception as e:
        logger.error(f"Error setting manual focus: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/focus/start_tracking', methods=['POST'])
def start_focus_tracking():
    try:
        point_data = request.json
        if not point_data:
            return jsonify({"error": "No point data provided"}), 400
            
        required_fields = ['x', 'y', 'z']
        if not all(k in point_data for k in required_fields):
            missing_fields = [k for k in required_fields if k not in point_data]
            return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400
            
        try:
            for field in required_fields:
                point_data[field] = float(point_data[field])
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid coordinate values. Must be numbers."}), 400

        # Get auto_focus parameter, default to False
        auto_focus = request.json.get('auto_focus', False)
        
        success, error = focus_controller.start_tracking(point_data)
        if success:
            return jsonify({
                "success": True,
                "message": "Focus tracking started successfully",
                "point": point_data
            })
        return jsonify({"error": error}), 400
    except Exception as e:
        logger.error(f"Error in start_focus_tracking: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@app.route('/focus/stop_tracking', methods=['POST'])
def stop_focus_tracking():
    try:
        if focus_controller.stop_tracking():
            return jsonify({
                "success": True,
                "message": "Focus tracking stopped successfully"
            })
        return jsonify({"error": "Failed to stop tracking"}), 500
    except Exception as e:
        logger.error(f"Error in stop_focus_tracking: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@app.route('/focus/status')
def get_focus_status():
    try:
        active_point = focus_controller.active_point
        tracking_thread = focus_controller.current_tracking_thread
        current_positions = motor_controller.get_motor_positions()
        
        status = {
            "tracking_active": tracking_thread is not None and tracking_thread.is_alive(),
            "current_point_id": active_point['id'] if active_point else None,
            "current_positions": current_positions if current_positions else {},
            "focus_enabled": focus_controller.auto_focus if hasattr(focus_controller, 'auto_focus') else False
        }
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error getting focus status: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/focus/motors/positions')
def get_focus_motor_positions():
    positions = motor_controller.get_motor_positions()
    if positions is None:
        return jsonify({"error": "Failed to read positions"}), 500
    return jsonify(positions)

# Profile routes
@app.route('/profile/list')
def list_profiles():
    profiles = profile_controller.list_profiles()
    return jsonify(profiles)

@app.route('/profile/<name>')
def get_profile(name):
    profile_data = profile_controller.get_profile(name)
    if profile_data is None:
        return jsonify({'error': 'Profile not found'}), 404
    return jsonify(profile_data)

@app.route('/profile/save', methods=['POST'])
def save_profile():
    success = profile_controller.save_profile(request.json)
    if success:
        return jsonify({'success': True})
    return jsonify({'error': 'Failed to save profile'}), 500

@app.route('/profile/status')
def get_profile_status():
    try:
        playback_active = profile_controller.current_playback_thread is not None and profile_controller.current_playback_thread.is_alive()
        current_point = None
        if playback_active:
            for i, point in enumerate(profile_controller.current_profile.get('points', [])):
                if point.get('focus_point_id') == focus_controller.active_point.get('id'):
                    current_point = i
                    break
        
        return jsonify({
            "playback_active": playback_active,
            "current_point_index": current_point,
            "complete": not playback_active and current_point == len(profile_controller.current_profile.get('points', [])) - 1 if profile_controller.current_profile else False
        })
    except Exception as e:
        logger.error(f"Error getting profile status: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/profile/play', methods=['POST'])
def play_profile():
    try:
        profile_data = request.json.get('profile')
        if not profile_data:
            return jsonify({"error": "No profile data provided"}), 400
            
        settings = request.json.get('settings', {})
        logger.debug(f"Starting playback for profile: {profile_data.get('name', 'unnamed')}")
        
        success, error = profile_controller.start_playback(profile_data, settings)
        if success:
            return jsonify({
                "success": True,
                "message": "Profile playback started"
            })
        return jsonify({
            "success": False,
            "error": error or "Failed to start profile playback"
        }), 400
    except Exception as e:
        logger.error(f"Error starting profile playback: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/profile/stop', methods=['POST'])
def stop_profile():
    try:
        success, error = profile_controller.stop_playback()
        if success:
            return jsonify({
                "success": True,
                "message": "Profile playback stopped"
            })
        return jsonify({
            "success": False,
            "error": error or "Failed to stop profile playback"
        }), 400
    except Exception as e:
        logger.error(f"Error stopping profile playback: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("Starting Camera Slider Web Interface...")
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
    finally:
        cleanup_streamer()
