from flask import Flask, render_template, request, jsonify
from motor_control import MotorController
from settings import MOTOR_IDS, MOTOR_LIMITS
import json
import os
import subprocess

app = Flask(__name__)
controller = MotorController()
PROFILES_FILE = "/home/pi/camera_slider_project/profiles/profiles.json"

if not os.path.exists(os.path.dirname(PROFILES_FILE)):
    os.makedirs(os.path.dirname(PROFILES_FILE))
if not os.path.exists(PROFILES_FILE):
    with open(PROFILES_FILE, 'w') as f:
        json.dump({}, f)

from flask import Flask, jsonify
import subprocess

app = Flask(__name__)

@app.route('/upload_to_github', methods=['POST'])
def upload_to_github():
    try:
        result = subprocess.run(['/bin/bash', '/home/pi/camera_slider_project/upload_to_github.sh'], 
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            return jsonify({'status': 'success', 'message': result.stdout})
        else:
            return jsonify({'status': 'error', 'message': result.stderr}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/save_profile', methods=['POST'])
def save_profile():
    data = request.json
    profile_name = data.get('name')
    profile_points = data.get('points')

    if not profile_name or not isinstance(profile_points, list):
        return jsonify({"status": "error", "message": "Invalid profile data"}), 400

    try:
        with open(PROFILES_FILE, 'r') as f:
            profiles = json.load(f)

        profiles[profile_name] = profile_points

        with open(PROFILES_FILE, 'w') as f:
            json.dump(profiles, f, indent=4)

        return jsonify({"status": "success", "message": "Profile saved successfully"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/load_profile', methods=['POST'])
def load_profile():
    data = request.json
    profile_name = data.get('name')

    if not profile_name:
        return jsonify({"status": "error", "message": "Profile name is required"}), 400

    try:
        with open(PROFILES_FILE, 'r') as f:
            profiles = json.load(f)

        profile_points = profiles.get(profile_name)
        if not profile_points:
            return jsonify({"status": "error", "message": "Profile not found"}), 404

        return jsonify({"status": "success", "points": profile_points}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/')
def index():
    try:
        motor_data = controller.bulk_read_positions(list(MOTOR_IDS.values()))
        return render_template('index.html', motor_ids=MOTOR_IDS, motor_limits=MOTOR_LIMITS, motor_data=motor_data, show_pid_button=True, show_turntable_button=True)
    except AttributeError:
        return jsonify({"status": "error", "message": "Die Funktion bulk_read_positions ist nicht verfügbar."}), 500

@app.route('/run_script/<script_name>', methods=['POST'])
def run_script(script_name):
    scripts = {
        "video_drehteller1": "/home/pi/camera_slider_project/video_drehteller1.py",
        "zeitlupe_start": "/home/pi/camera_slider_project/zeitlupe_start.py",
        "zeitlupe_stop": "/home/pi/camera_slider_project/zeitlupe_stop.py"
    }

    if script_name not in scripts:
        return jsonify({"status": "error", "message": "Script not found"}), 400

    script_path = scripts[script_name]

    try:
        subprocess.Popen(["python3", script_path])
        return jsonify({"status": "success", "message": f"{script_name} is running"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/set_motor', methods=['POST'])
def set_motor():
    try:
        data = request.json
        motor_id = data.get("motor_id")
        goal_position = data.get("goal_position")
        profile_velocity = data.get("profile_velocity")

        if not motor_id or goal_position is None or profile_velocity is None:
            return {"error": "Ungültige Eingabe"}, 400

        print(f"Setze Motor: ID={motor_id}, Zielposition={goal_position}, Profilgeschwindigkeit={profile_velocity}")

        controller.set_profile(motor_id, int(profile_velocity), acceleration=50)
        controller.set_goal_position(motor_id, goal_position)

        return {"status": "success"}, 200
    except Exception as e:
        print(f"Fehler beim Setzen des Motors: {e}")
        return {"error": str(e)}, 500


@app.route('/set_turntable_mode', methods=['POST'])
def set_turntable_mode():
    data = request.json
    mode = data.get('mode')
    try:
        controller.configure_turntable_mode(motor_id=MOTOR_IDS['turntable'], mode=mode)
        return jsonify({"status": "success", "mode": mode})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/toggle_all_torque', methods=['POST'])
def toggle_all_torque():
    try:
        data = request.json
        torque_enable = data.get('torque_enable')

        if torque_enable is None:
            return jsonify({"status": "error", "message": "Ungültige Eingabe"}), 400

        print(f"Schalte Torque {'ein' if torque_enable else 'aus'} für alle Motoren")

        for motor_id in MOTOR_IDS.values():
            if torque_enable:
                controller.enable_torque(motor_id)
            else:
                controller.disable_torque(motor_id)

        return jsonify({"status": "success", "torque_enabled": torque_enable})
    except Exception as e:
        print(f"Fehler in /toggle_all_torque: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/error_log', methods=['POST'])
def error_log():
    try:
        error_message = request.json.get('error_message')
        if not error_message:
            return {"status": "error", "message": "Kein Fehler angegeben"}, 400

        print(f"Fehleranzeige: {error_message}")
        return {"status": "success", "message": "Fehler aufgezeichnet"}, 200
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500

@app.route('/shutdown', methods=['POST'])
def shutdown():
    try:
        subprocess.Popen(['sudo', 'shutdown', 'now'])
        return jsonify({"status": "success", "message": "System shutting down..."}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/motordata', methods=['GET'])
def get_motor_data():
    motor_data = {
        "temperature": motor.get_temperature(),
        "current_position": motor.get_position(),
        "current": motor.get_current(),
        "volt": motor.get_voltage(),
        "torque": motor.get_torque()
    }
    return jsonify(motor_data)


@app.route('/bulk_read', methods=['POST'])
def bulk_read():
    try:
        motor_ids = list(MOTOR_IDS.values())
        status_data = controller.read_status_sync(motor_ids)
        print("DEBUG: Daten aus Bulk-Read:", status_data)  # Debug-Ausgabe
        return jsonify({"status": "success", "data": status_data}), 200
    except Exception as e:
        print("Fehler beim Bulk-Read:", e)
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/save_profile_v2', methods=['POST'])
def save_profile_v2():
    data = request.json
    profile_name = data.get('name')
    points = data.get('points')

    if not profile_name or not isinstance(points, list):
        return jsonify({"status": "error", "message": "Ungültige Profildaten"}), 400

    try:
        with open(PROFILES_FILE, 'r') as f:
            profiles = json.load(f)

        profiles[profile_name] = [
            {
                "slider": point.get('slider'),
                "pan": point.get('pan'),
                "tilt": point.get('tilt'),
                "duration": point.get('duration')
            } for point in points
        ]

        with open(PROFILES_FILE, 'w') as f:
            json.dump(profiles, f, indent=4)

        return jsonify({"status": "success", "message": "Profile gespeichert"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
