import numpy as np
from typing import Dict, Tuple
from src.dxl_manager import DynamixelManager

class KalmanFilter:
    """
    Implementiert einen Kalman Filter für Motor State Estimation.
    State Vector: [position, velocity, acceleration]
    """
    def __init__(self, dt: float = None):
        # Lade Einstellungen aus settings.py
        from src.settings import MOTION_CONTROL
        kalman_settings = MOTION_CONTROL["slave_kalman"]
        
        # State vector dimension [position, velocity, acceleration]
        self.state_dim = 3
        self.measurement_dim = 1
        
        # Update rate aus Settings oder Standardwert
        self.dt = dt if dt is not None else kalman_settings["update_rate"]
        
        # Initial state
        self.x = np.zeros((self.state_dim, 1))
        
        # State transition matrix
        self.F = np.array([
            [1, self.dt, 0.5*self.dt**2],
            [0, 1, self.dt],
            [0, 0, 1]
        ])
        
        # Measurement matrix
        self.H = np.array([[1, 0, 0]])
        
        # Process noise covariance aus Settings
        self.Q = np.diag([
            kalman_settings["process_noise"]["position"],
            kalman_settings["process_noise"]["velocity"],
            kalman_settings["process_noise"]["acceleration"]
        ])
        
        # Measurement noise covariance aus Settings
        self.R = np.array([[kalman_settings["measurement_noise"]]])
        
        # Error covariance matrix aus Settings
        self.P = np.eye(self.state_dim) * kalman_settings["initial_uncertainty"]
        
    def predict(self) -> np.ndarray:
        """Vorhersage-Schritt"""
        self.x = self.F @ self.x
        self.P = self.F @ self.P @ self.F.T + self.Q
        return self.x
        
    def update(self, measurement: float) -> np.ndarray:
        """Update-Schritt mit Messung"""
        z = np.array([[measurement]])
        
        # Kalman Gain
        S = self.H @ self.P @ self.H.T + self.R
        K = self.P @ self.H.T @ np.linalg.inv(S)
        
        # State Update
        y = z - self.H @ self.x
        self.x = self.x + K @ y
        
        # Covariance Update
        self.P = (np.eye(self.state_dim) - K @ self.H) @ self.P
        
        return self.x

    def get_state(self) -> Tuple[float, float, float]:
        """Returns current position, velocity, and acceleration estimates"""
        return (float(self.x[0]), float(self.x[1]), float(self.x[2]))

class EnhancedMotorControl:
    def __init__(self, manager: DynamixelManager):
        from src.settings import MOTION_CONTROL, MOTOR_IDS, MOTOR_ID_TO_NAME
        
        self.manager = manager
        self.filters: Dict[int, KalmanFilter] = {}
        self.motor_ids = MOTOR_IDS
        self.id_to_name = MOTOR_ID_TO_NAME
        self.config = MOTION_CONTROL
        
        # Initialisiere Filter nur für Slave-Motoren
        for motor_name, config in self.config["synchronized_motors"].items():
            if config["prediction_enabled"]:
                motor_id = self.motor_ids[motor_name]
                self.filters[motor_id] = KalmanFilter(
                    dt=self.config["slave_kalman"]["update_rate"]
                )
    
    def update_motor_state(self, motor_id: int, position: float) -> Tuple[float, float, float]:
        """
        Aktualisiert den Zustand eines Motors mit Kalman Filtering
        Returns: (gefilterte_position, geschwindigkeit, beschleunigung)
        """
        if motor_id not in self.filters:
            self.filters[motor_id] = KalmanFilter(dt=self.config["slave_kalman"]["update_rate"])
        
        # Predict
        state_prediction = self.filters[motor_id].predict()
        
        # Update mit gemessener Position
        updated_state = self.filters[motor_id].update(position)
        
        # Extrahiere gefilterte Werte
        filtered_pos, velocity, accel = self.filters[motor_id].get_state()
        
        return filtered_pos, velocity, accel
    
    def get_filtered_positions(self) -> Dict[int, Tuple[float, float, float]]:
        """
        Liest aktuelle Motorpositionen und wendet Kalman Filter an
        Returns: Dictionary mit {motor_id: (position, velocity, acceleration)}
        """
        # Rohe Positionen lesen
        raw_positions = self.manager.bulk_read_positions()
        
        filtered_states = {}
        for motor_id, pos in raw_positions.items():
            if pos is not None:
                filtered_states[motor_id] = self.update_motor_state(motor_id, float(pos))
            else:
                filtered_states[motor_id] = (None, None, None)
                
        return filtered_states
    
    def move_to_position(self, motor_id: int, target_position: float, use_prediction: bool = True) -> None:
        """
        Bewegt einen Motor zur Zielposition.
        Direkter Modus für Master, prädiktive Kontrolle für Slaves.
        """
        motor_name = self.id_to_name[motor_id]
        
        # Prüfe ob es der Master-Motor ist
        # Direkter Modus für Master-Motor, unabhängig von use_prediction
        if motor_name == self.config["master_motor"]:
            # Für den Slider immer direkte Bewegung
            self.manager.bulk_write_goal_positions({motor_id: int(target_position)})
            return
        else:
            # Prüfe ob der Motor ein Slave ist
            is_slave = False
            for slave_name, config in self.config["synchronized_motors"].items():
                if motor_name == slave_name and config["prediction_enabled"]:
                    is_slave = True
                    break
            
            if is_slave and motor_id in self.filters and use_prediction:
                # Hole aktuellen gefilterten Zustand
                current_pos, velocity, accel = self.update_motor_state(
                    motor_id, 
                    self.manager.bulk_read_positions()[motor_id]
                )
                
                # Berechne prädiktive Position
                pred_time = self.config["prediction"]["time"]
                predicted_offset = (velocity * pred_time + 
                                 0.5 * accel * pred_time * pred_time)
                adjusted_target = target_position - predicted_offset
                
                # Wende Glättung an
                smoothing = self.config["prediction"]["smoothing"]
                if velocity:
                    smooth_factor = min(
                        smoothing["max_factor"],
                        abs(velocity) / smoothing["velocity_scale"] + smoothing["min_factor"]
                    )
                else:
                    smooth_factor = smoothing["min_factor"]
                
                current_pos = self.manager.bulk_read_positions()[motor_id]
                smoothed_target = current_pos * (1 - smooth_factor) + int(adjusted_target) * smooth_factor
                
                # Sende Position
                self.manager.bulk_write_goal_positions({motor_id: int(smoothed_target)})
            else:
                # Fallback: Direkte Bewegung
                self.manager.bulk_write_goal_positions({motor_id: int(target_position)})

    def move_with_profile(self, positions: Dict[int, float], duration: float) -> None:
        """
        Führt eine profilierte Bewegung für mehrere Motoren aus
        """
        # Verarbeite zuerst den Master-Motor
        master_name = self.config["master_motor"]
        master_id = self.motor_ids[master_name]
        
        if master_id in positions:
            # Setze Master-Geschwindigkeit
            current_pos = self.manager.bulk_read_positions()[master_id]
            distance = abs(positions[master_id] - current_pos)
            master_velocity = int(distance / duration)
            
            # Setze Master-Profil
            self.manager.bulk_write_profile_velocity({master_id: master_velocity})
            
            # Bewege Master
            self.move_to_position(master_id, positions[master_id])
            
            # Entferne Master aus der Position-Liste
            slave_positions = positions.copy()
            del slave_positions[master_id]
            
            # Verarbeite Slave-Motoren
            if slave_positions:
                # Berechne Geschwindigkeiten für Slaves
                velocities = {}
                for motor_id, target_pos in slave_positions.items():
                    current_pos = self.manager.bulk_read_positions()[motor_id]
                    if current_pos is not None:
                        distance = abs(target_pos - current_pos)
                        velocity = int(distance / duration)
                        velocities[motor_id] = velocity
                
                # Setze Geschwindigkeitsprofile für Slaves
                if velocities:
                    self.manager.bulk_write_profile_velocity(velocities)
                
                # Bewege Slave-Motoren
                for motor_id, target_pos in slave_positions.items():
                    self.move_to_position(motor_id, target_pos)
        else:
            # Wenn kein Master-Motor, bewege alle direkt
            velocities = {}
            for motor_id, target_pos in positions.items():
                current_pos = self.manager.bulk_read_positions()[motor_id]
                if current_pos is not None:
                    distance = abs(target_pos - current_pos)
                    velocity = int(distance / duration)
                    velocities[motor_id] = velocity
            
            if velocities:
                self.manager.bulk_write_profile_velocity(velocities)
            
            for motor_id, target_pos in positions.items():
                self.move_to_position(motor_id, target_pos)
    
    def get_pid_values(self) -> Dict[int, Dict[str, int]]:
        """Liest aktuelle PID-Werte"""
        return self.manager.bulk_read_pid_gains()
    
    def set_pid_values(self, pid_dict: Dict[int, Dict[str, int]]) -> bool:
        """Setzt neue PID-Werte"""
        return self.manager.bulk_write_pid_gains(pid_dict)

if __name__ == "__main__":
    # Test-Code
    dxl_manager = DynamixelManager()
    enhanced_control = EnhancedMotorControl(dxl_manager)
    
    try:
        # PID-Werte auslesen
        print("\nAktuelle PID-Werte:")
        pid_values = enhanced_control.get_pid_values()
        print(pid_values)
        
        # Filtered Position Test
        print("\nPositions-Tracking Test:")
        for _ in range(5):
            states = enhanced_control.get_filtered_positions()
            print("Gefilterte Zustände:", states)
            
        # Bewegungstest
        print("\nBewegungstest:")
        test_positions = {1: 500, 2: 1000}
        enhanced_control.move_with_profile(test_positions, duration=2.0)
        
    finally:
        dxl_manager.disable_torque()
        dxl_manager.close()
