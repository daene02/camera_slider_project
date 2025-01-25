from flask import Flask, render_template, request, jsonify
from motor_control.bulk import BulkOperations
from settings import MOTOR_IDS, MOTOR_LIMITS, DEVICENAME, BAUDRATE, PROTOCOL_VERSION, MOTOR_NAMES
from dynamixel_sdk import PortHandler, PacketHandler
import json
import os
import subprocess
import signal
import logging

app = Flask(__name__)

# Initialisiere Port und PacketHandler
port_handler = PortHandler(DEVICENAME)
packet_handler = PacketHandler(PROTOCOL_VERSION)
if not port_handler.openPort():
    raise RuntimeError("Port konnte nicht geöffnet werden.")
if not port_handler.setBaudRate(BAUDRATE):
    raise RuntimeError("Baudrate konnte nicht gesetzt werden.")

# Initialisiere BulkOperations
bulk_operations = BulkOperations(port_handler, packet_handler)

PROFILES_FILE = "/home/pi/camera_slider_project/profiles/profiles.json"
if not os.path.exists(os.path.dirname(PROFILES_FILE)):
    os.makedirs(os.path.dirname(PROFILES_FILE))
if not os.path.exists(PROFILES_FILE):
    with open(PROFILES_FILE, 'w') as f:
        json.dump({}, f)
              
@app.route('/')
def index():
    try:
        motor_ids = list(MOTOR_IDS.values())
        motor_data = bulk_operations.bulk_read_all(motor_ids)

        for motor_id in motor_ids:
            individual_data = bulk_operations.read_individual(motor_id)
            motor_data[motor_id].update(individual_data)

        motor_data = bulk_operations.clean_data(motor_data)

        return render_template('index.html', motor_ids=MOTOR_IDS, motor_limits=MOTOR_LIMITS, motor_data=motor_data, show_pid_button=True, show_turntable_button=True)
    except Exception as e:
        logging.error(f"Fehler im Index-Endpunkt: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/run_script")
def run_script():
    script = request.args.get("script")
    if not script:
        return jsonify({"error": "Script not specified"}), 400

    script_path = os.path.join(os.getcwd(), script)
    
    if not os.path.exists(script_path):
        return jsonify({"error": f"Script {script} not found in {os.getcwd()}"}), 404

    try:
        result = subprocess.run(["python3", script_path], capture_output=True, text=True)
        return jsonify({"output": result.stdout, "error": result.stderr, "returncode": result.returncode})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/set_motor', methods=['POST'])
def set_motor():
    try:
        data = request.json
        logging.info(f"Rohdaten empfangen: {data}")  # Debug-Ausgabe der gesamten empfangenen JSON-Daten
        
        motor_id = data.get("motor_id")
        goal_position = data.get("goal_position")
        profile_velocity = data.get("profile_velocity")
        profile_acceleration = data.get("profile_acceleration", 0)  # Optionaler Beschleunigungswert

        # Debugging-Log, um die empfangenen Daten zu prüfen
        logging.info(f"Empfangene Daten: Motor ID={motor_id}, Zielposition={goal_position}, Profilgeschwindigkeit={profile_velocity}, Beschleunigung={profile_acceleration}")

        if not motor_id or goal_position is None or profile_velocity is None:
            return {"error": "Ungültige Eingabe"}, 400

        bulk_operations.bulk_write_all({
            motor_id: {
                "goal_position": goal_position,
                "velocity": profile_velocity,
                "acceleration": profile_acceleration
            }
        })

        return {"status": "success"}, 200
    except Exception as e:
        logging.error(f"Fehler beim Setzen des Motors: {e}")
        return {"error": str(e)}, 500

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
                bulk_operations.enable_torque(motor_id)
            else:
                bulk_operations.disable_torque(motor_id)

        return jsonify({"status": "success", "torque_enabled": torque_enable})
    except Exception as e:
        print(f"Fehler in /toggle_all_torque: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/bulk_read', methods=['GET'])
def bulk_read():
    try:
        motor_ids = list(MOTOR_IDS.values())
        motor_data = bulk_operations.bulk_read_all(motor_ids)

        for motor_id in motor_ids:
            individual_data = bulk_operations.read_individual(motor_id)
            motor_data[motor_id].update(individual_data)

        # Formatierte Ausgabe
        motor_data_formatted = {
            MOTOR_NAMES[motor_id]: {
                "position": motor_info.get("position", 0),
                "temperature": motor_info.get("temperature", 0),
                "current": motor_info.get("current", 0),
                "voltage": motor_info.get("voltage", 0)
            }
            for motor_id, motor_info in motor_data.items()
        }

        return jsonify({"status": "success", "data": motor_data_formatted}), 200
    except Exception as e:
        logging.error(f"Fehler beim Bulk-Read: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

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


@app.route('/terminate_app', methods=['POST'])
def terminate_app():
    try:
        pid = os.getpid()
        os.kill(pid, signal.SIGTERM)
        return jsonify({"status": "success", "message": "Application terminated."}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
