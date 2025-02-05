from flask import Flask, render_template, request, send_from_directory, jsonify, make_response
from src.web.controllers.motor_controller import motor_controller
from src.web.controllers.profile_controller import profile_controller
from src.web.controllers.focus_controller import focus_controller
import asyncio
import os
import logging
import time

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

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

def check_camera_connected():
    """Check if camera is connected and return error response if not."""
    if not profile_controller.camera_connected:
        return jsonify({"error": "Camera not connected"}), 400
    return None

# Main page routes
@app.route('/')
def home():
    return render_template('home.html', background_image=get_background_image('home'))

@app.route('/focus')
def focus():
    return render_template('focus.html', background_image=get_background_image('focus'))

@app.route('/motor')
def motor():
    motors = motor_controller.get_motor_status()
    if motors is None:
        return jsonify({"error": "Failed to get motor status"}), 500
    return render_template('motor.html', motors=motors, background_image=get_background_image('motor'))

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
    return render_template('focus_visualization.html')

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
        motor_controller.update_motor_position(motor_id, position)
        return jsonify({"success": True})
    except ValueError:
        return jsonify({"error": "Invalid position value"}), 400

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

@app.route('/motor/status')
def motor_status():
    motors = motor_controller.get_motor_status()
    if motors is None:
        return jsonify({"error": "Failed to get motor status"}), 500
    return jsonify(motors)

@app.route('/motors/positions')
def get_motor_positions():
    positions = motor_controller.get_motor_positions()
    if positions is None:
        return jsonify({"error": "Failed to read positions"}), 500
    return jsonify(positions)

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
        return jsonify({
            "tracking_active": focus_controller.current_tracking_thread is not None and focus_controller.current_tracking_thread.is_alive(),
            "current_point_id": active_point['id'] if active_point else None
        })
    except Exception as e:
        logger.error(f"Error getting focus status: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/focus/motors/positions')
def get_focus_motor_positions():
    positions = motor_controller.get_motor_positions()
    if positions is None:
        return jsonify({"error": "Failed to read positions"}), 500
    return jsonify(positions)

# Camera control routes
@app.route('/camera/connect', methods=['POST'])
def connect_camera():
    try:
        success, error = run_async(profile_controller.connect_camera())
        if success:
            return jsonify({"success": True})
        return jsonify({"error": error}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/camera/status', methods=['GET'])
def get_camera_status():
    try:
        if not profile_controller.camera_connected:
            return jsonify({"connected": False})
            
        storage_info = run_async(profile_controller.camera.get_storage_info())
        camera_settings = run_async(profile_controller.camera.get_settings())
        
        return jsonify({
            "connected": True,
            "recording": profile_controller.recording_active,
            "storage": storage_info,
            "settings": camera_settings,
            "live_view": profile_controller.camera.live_view_enabled
        })
    except Exception as e:
        logger.error(f"Error getting camera status: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/camera/capture', methods=['POST'])
def capture_photo():
    if error_response := check_camera_connected():
        return error_response
        
    try:
        success = run_async(profile_controller.camera.capture_photo())
        if success:
            return jsonify({"success": True})
        return jsonify({"error": "Failed to capture photo"}), 500
    except Exception as e:
        logger.error(f"Error capturing photo: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/camera/video/start', methods=['POST'])
def start_video():
    if error_response := check_camera_connected():
        return error_response
        
    try:
        success = run_async(profile_controller.camera.start_video())
        if success:
            profile_controller.recording_active = True
            return jsonify({"success": True})
        return jsonify({"error": "Failed to start recording"}), 500
    except Exception as e:
        logger.error(f"Error starting video: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/camera/video/stop', methods=['POST'])
def stop_video():
    if error_response := check_camera_connected():
        return error_response
        
    try:
        success = run_async(profile_controller.camera.stop_video())
        if success:
            profile_controller.recording_active = False
            return jsonify({"success": True})
        return jsonify({"error": "Failed to stop recording"}), 500
    except Exception as e:
        logger.error(f"Error stopping video: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/camera/live_view')
def get_live_view():
    try:
        # Check camera connection
        if error_response := check_camera_connected():
            logger.error("Camera not connected during live view request")
            return error_response

        camera = profile_controller.camera
        if not camera:
            logger.error("Camera object is None")
            return jsonify({"error": "Camera not properly initialized"}), 500
        
        # Verify live view state
        if not camera.live_view_enabled:
            logger.debug("Live view not enabled, enabling now...")
            success = run_async(camera.toggle_live_view(True))
            if not success:
                logger.error("Failed to enable live view")
                return jsonify({"error": "Failed to enable live view"}), 500
                
        # Capture preview with retries and increasing delays
        max_retries = 3
        base_delay = 0.5
        for attempt in range(max_retries):
            delay = base_delay * (attempt + 1)  # Increasing delay for each retry
            logger.debug(f"Attempting preview capture (attempt {attempt + 1}/{max_retries})")
            
            preview = run_async(camera.capture_preview())
            if not preview and attempt < max_retries - 1:
                logger.warning(f"Preview capture failed, waiting {delay}s before retry")
                time.sleep(delay)
            if preview:
                try:
                    if not preview:
                        logger.error("No preview data received")
                        raise ValueError("Preview data is empty")
                        
                    # Handle potential tuple return (data, size)
                    if isinstance(preview, tuple):
                        data = preview[0]
                        logger.debug(f"Got preview data from tuple, size: {len(data) if data else 0}")
                    else:
                        data = preview
                        logger.debug(f"Got preview data directly, size: {len(data) if data else 0}")
                    
                    if not data:
                        raise ValueError("No valid preview data")
                        
                    # Create response with preview bytes
                    response = make_response(data)
                    response.headers['Content-Type'] = 'image/jpeg'
                    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
                    logger.debug("Sending preview response")
                    return response
                except Exception as e:
                    logger.error(f"Error processing preview data: {str(e)}", exc_info=True)
                    continue
            else:
                logger.error("Preview capture returned None")
                
        logger.error("Failed to capture preview after all retries")
        return jsonify({"error": "Failed to capture preview after multiple attempts"}), 500
    except Exception as e:
        logger.error(f"Live view error: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/camera/settings', methods=['POST'])
def update_camera_settings():
    if error_response := check_camera_connected():
        return error_response
        
    try:
        settings = request.json
        success = run_async(profile_controller.camera.update_settings(settings))
        if success:
            return jsonify({"success": True})
        return jsonify({"error": "Failed to update camera settings"}), 500
    except Exception as e:
        logger.error(f"Error updating camera settings: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/camera/live_view/toggle', methods=['POST'])
def toggle_live_view():
    if error_response := check_camera_connected():
        return error_response
        
    try:
        enable = request.json.get('enable')
        success = run_async(profile_controller.camera.toggle_live_view(enable))
        if success:
            return jsonify({
                "success": True,
                "enabled": profile_controller.camera.live_view_enabled
            })
        return jsonify({"error": "Failed to toggle live view"}), 500
    except Exception as e:
        logger.error(f"Error toggling live view: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

# Profile routes
@app.route('/profile/list')
def list_profiles():
    profiles = profile_controller.list_profiles()
    return jsonify(profiles)

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
    app.run(host='0.0.0.0', port=5000)
