from flask import Flask, render_template, request, send_from_directory, jsonify
from src.web.controllers.motor_controller import motor_controller
from src.web.controllers.profile_controller import profile_controller
from src.web.controllers.focus_controller import focus_controller
import os

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
    return jsonify(focus_controller.focus_points)

@app.route('/focus/point/<int:index>', methods=['GET', 'DELETE'])
def manage_focus_point(index):
    if request.method == 'GET':
        point = focus_controller.get_focus_point(index)
        if point:
            return jsonify(point)
        return jsonify({"error": "Point not found"}), 404
    elif request.method == 'DELETE':
        if focus_controller.remove_focus_point(index):
            return jsonify({"success": True})
        return jsonify({"error": "Point not found"}), 404

@app.route('/focus/save_point', methods=['POST'])
def save_focus_point():
    if focus_controller.add_focus_point(request.json):
        return jsonify({"success": True})
    return jsonify({"error": "Invalid point data"}), 400

@app.route('/focus/start_tracking', methods=['POST'])
def start_focus_tracking():
    point_data = request.json
    if not point_data or not all(k in point_data for k in ['x', 'y', 'z']):
        return jsonify({"error": "Invalid point data"}), 400

    success, error = focus_controller.start_tracking(point_data)
    if success:
        return jsonify({"success": True})
    return jsonify({"error": error}), 400

@app.route('/focus/stop_tracking', methods=['POST'])
def stop_focus_tracking():
    if focus_controller.stop_tracking():
        return jsonify({"success": True})
    return jsonify({"error": "Failed to stop tracking"}), 500

if __name__ == '__main__':
    print("Starting Camera Slider Web Interface...")
    app.run(host='0.0.0.0', port=5000)
