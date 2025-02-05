from flask import Flask, render_template, request, send_from_directory, jsonify, make_response
from src.web.controllers.motor_controller import motor_controller
from src.web.controllers.profile_controller import profile_controller
from src.web.controllers.focus_controller import focus_controller
import asyncio
import os
import logging

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
        print(f"Error in profiles route: {str(e)}")
        import traceback
        traceback.print_exc()
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

@app.route('/profile/play', methods=['POST'])
def play_profile():
    try:
        data = request.json
        success, error = profile_controller.start_playback(data['profile'], data['settings'])
        if success:
            return jsonify({'success': True})
        return jsonify({'error': error}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/profile/stop', methods=['POST'])
def stop_profile():
    success, error = profile_controller.stop_playback()
    if success:
        return jsonify({'success': True})
    return jsonify({'error': error}), 500

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
            
        # Validate coordinate values
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
        print(f"Error in start_focus_tracking: {str(e)}")
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
        print(f"Error in stop_focus_tracking: {str(e)}")
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
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success, error = loop.run_until_complete(profile_controller.connect_camera())
        if success:
            return jsonify({"success": True})
        return jsonify({"error": error}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/camera/status', methods=['GET'])
def get_camera_status():
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        if not profile_controller.camera_connected:
            return jsonify({"connected": False})
            
        storage_info = loop.run_until_complete(profile_controller.camera.get_storage_info())
        camera_settings = loop.run_until_complete(profile_controller.camera.get_settings())
        
        return jsonify({
            "connected": True,
            "recording": profile_controller.recording_active,
            "storage": storage_info,
            "settings": camera_settings,
            "live_view": profile_controller.camera.live_view_enabled
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/camera/capture', methods=['POST'])
def capture_photo():
    if not profile_controller.camera_connected:
        return jsonify({"error": "Camera not connected"}), 400
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success = loop.run_until_complete(profile_controller.camera.capture_photo())
        if success:
            return jsonify({"success": True})
        return jsonify({"error": "Failed to capture photo"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/camera/video/start', methods=['POST'])
def start_video():
    if not profile_controller.camera_connected:
        return jsonify({"error": "Camera not connected"}), 400
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success = loop.run_until_complete(profile_controller.camera.start_video())
        if success:
            profile_controller.recording_active = True
            return jsonify({"success": True})
        return jsonify({"error": "Failed to start recording"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/camera/video/stop', methods=['POST'])
def stop_video():
    if not profile_controller.camera_connected:
        return jsonify({"error": "Camera not connected"}), 400
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success = loop.run_until_complete(profile_controller.camera.stop_video())
        if success:
            profile_controller.recording_active = False
            return jsonify({"success": True})
        return jsonify({"error": "Failed to stop recording"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/camera/live_view')
def get_live_view():
    if not profile_controller.camera_connected:
        return jsonify({"error": "Camera not connected"}), 400
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Ensure live view is enabled
        if not profile_controller.camera.live_view_enabled:
            success = loop.run_until_complete(profile_controller.camera.toggle_live_view(True))
            if not success:
                return jsonify({"error": "Failed to enable live view"}), 500
            # Give camera time to start live view
            loop.run_until_complete(asyncio.sleep(0.2))
        
        # Capture preview
        preview = loop.run_until_complete(profile_controller.camera.capture_preview())
        if not preview:
            return jsonify({"error": "Failed to capture preview"}), 500

            
        file_data = preview.get_data_and_size()
        response = make_response(file_data)
        response.headers.set('Content-Type', 'image/jpeg')
        return response
    except Exception as e:
        logger.error(f"Live view error: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/camera/live_view/toggle', methods=['POST'])
def toggle_live_view():
    if not profile_controller.camera_connected:
        return jsonify({"error": "Camera not connected"}), 400
    try:
        enable = request.json.get('enable')
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success = loop.run_until_complete(profile_controller.camera.toggle_live_view(enable))
        if success:
            return jsonify({"success": True, "enabled": profile_controller.camera.live_view_enabled})
        return jsonify({"error": "Failed to toggle live view"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/camera/settings', methods=['POST'])
def update_camera_settings():
    if not profile_controller.camera_connected:
        return jsonify({"error": "Camera not connected"}), 400
    try:
        settings = request.json
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success = loop.run_until_complete(profile_controller.camera.update_settings(settings))
        if success:
            return jsonify({"success": True})
        return jsonify({"error": "Failed to update camera settings"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("Starting Camera Slider Web Interface...")
    app.run(host='0.0.0.0', port=5000)
