from flask import Flask, request, jsonify, render_template
from src.camera_slider import CameraSlider
from src.focus import FocusController
from src.settings import MOTOR_IDS, MOTOR_LIMITS
import logging
import time

app = Flask(__name__, template_folder="templates")
camera_slider = CameraSlider()
focus_controller = FocusController(object_position=(-400, 600, -300))

@app.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        logging.error(f"Fehler: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/move_to_start", methods=["POST"])
def move_to_start():
    if not request.is_json:
        return jsonify({"status": "error", "message": "Content-Type must be application/json"}), 400
    try:
        # Bewege alle Motoren in Startposition
        start_positions = {
            "slider": 0,
            "pan": 0,
            "tilt": 0,
            "focus": 0,
            "turntable": 0,
            "zoom": 0
        }
        camera_slider.move_motors([start_positions], velocity=1000, acceleration=500, duration=5)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route("/start_focus_tracking", methods=["POST"])
def start_focus_tracking():
    if not request.is_json:
        return jsonify({"status": "error", "message": "Content-Type must be application/json"}), 400
    try:
        data = request.json or {}
        start_pos = data.get("start_pos", 0)
        end_pos = data.get("end_pos", 900)
        
        # Erhöhe die Anzahl der Schritte für flüssigere Bewegung
        num_steps = data.get("num_steps", 1800)  # Doppelte Anzahl der Schritte
        duration = data.get("duration", 50)
        
        sequence = focus_controller.generate_movement_sequence(start_pos, end_pos, num_steps)
        movement_sequence = []
        
        for i, motors in enumerate(sequence):
            slider_pos = (end_pos / (num_steps - 1)) * i
            position_dict = {
                "slider": slider_pos,
                "pan": motors["pan"],
                "tilt": motors["tilt"],
                "focus": motors["focus"],
                "turntable": 0,
                "zoom": 0
            }
            movement_sequence.append(position_dict)
        
        # Reduzierte Geschwindigkeit und Beschleunigung für sanftere Bewegung
        velocity = 80  # Reduziert von 100
        acceleration = 1200  # Reduziert von 1800
        
        camera_slider.move_motors(movement_sequence, velocity, acceleration, duration)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route("/emergency_stop", methods=["POST"])
def emergency_stop():
    if not request.is_json:
        return jsonify({"status": "error", "message": "Content-Type must be application/json"}), 400
    try:
        camera_slider.disable_motors()
        return jsonify({"status": "success", "message": "Notaus erfolgreich"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route("/bulk_read_data", methods=["GET"])
def bulk_read_data():
    try:
        # Add small delays between operations
        positions = camera_slider.read_positions()
        time.sleep(0.01)  # 50ms delay
        temperatures = camera_slider.manager.bulk_read_temperature()
        time.sleep(0.01)
        currents = camera_slider.manager.bulk_read_current()
        time.sleep(0.01)
        voltages = camera_slider.manager.bulk_read_voltage()

        data = {}
        for motor_name, motor_id in MOTOR_IDS.items():
            data[motor_name] = {
                "position": positions.get(motor_name),
                "temperature": temperatures.get(motor_id),
                "current": currents.get(motor_id),
                "voltage": voltages.get(motor_id)
            }

        return jsonify({
            "status": "success",
            "data": data
        })
    except Exception as e:
        logging.error(f"Fehler beim Lesen der Motordaten: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route("/update_object_position", methods=["POST"])
def update_object_position():
    if not request.is_json:
        return jsonify({"status": "error", "message": "Content-Type must be application/json"}), 400
    try:
        data = request.json
        x = data.get("x", -400)
        y = data.get("y", 600)
        z = data.get("z", -300)
        
        # Aktualisiere die Objektposition im FocusController
        focus_controller.object_x = x
        focus_controller.object_y = y
        focus_controller.object_z = z
        
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/update_motion_settings", methods=["POST"])
def update_motion_settings():
    if not request.is_json:
        return jsonify({"status": "error", "message": "Content-Type must be application/json"}), 400
    try:
        data = request.json
        interpolation_steps = data.get("interpolation_steps", 100)
        velocity_scale = data.get("velocity_scale", 80) / 100.0
        acceleration_scale = data.get("acceleration_scale", 60) / 100.0
        
        # Aktualisiere die Einstellungen im CameraSlider
        camera_slider.interpolation_steps = interpolation_steps
        camera_slider.velocity_scale = velocity_scale
        camera_slider.acceleration_scale = acceleration_scale
        
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    camera_slider.enable_motors()
    try:
        app.run(host="0.0.0.0", port=5000, debug=True)
    finally:
        camera_slider.disable_motors()
        camera_slider.close()
