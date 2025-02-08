"""
S-Kurven-Bewegungsprofile für sanfte Beschleunigung und Verzögerung.
"""
from typing import Dict, Tuple, Optional
import numpy as np

class SCurveProfile:
    def __init__(self, max_velocity: float, max_acceleration: float):
        """
        Initialisiert einen S-Kurven-Profil-Generator
        
        Args:
            max_velocity: Maximale Geschwindigkeit
            max_acceleration: Maximale Beschleunigung
        """
        self.max_velocity = max_velocity
        self.max_acceleration = max_acceleration
        
    def calculate_profile(self, 
                         start_pos: float,
                         end_pos: float,
                         duration: float) -> Dict[str, float]:
        """
        Berechnet ein S-Kurven-Bewegungsprofil
        
        Args:
            start_pos: Startposition
            end_pos: Zielposition
            duration: Gewünschte Bewegungsdauer
            
        Returns:
            Dictionary mit Profilparametern
        """
        distance = abs(end_pos - start_pos)
        direction = 1 if end_pos > start_pos else -1
        
        # Zeitaufteilung (30-40-30)
        accel_time = duration * 0.3
        const_time = duration * 0.4
        decel_time = duration * 0.3
        
        # Berechne benötigte Geschwindigkeit
        cruise_velocity = distance / (const_time + 0.5 * (accel_time + decel_time))
        
        # Limitiere Geschwindigkeit
        velocity = min(cruise_velocity, self.max_velocity)
        
        # Berechne benötigte Beschleunigung
        acceleration = velocity / accel_time
        
        # Limitiere Beschleunigung
        if acceleration > self.max_acceleration:
            acceleration = self.max_acceleration
            # Passe Zeiten an
            accel_time = velocity / acceleration
            const_time = (distance - velocity * accel_time) / velocity
            decel_time = accel_time
            
        return {
            'velocity': velocity * direction,
            'acceleration': acceleration * direction,
            'accel_time': accel_time,
            'const_time': const_time,
            'decel_time': decel_time,
            'total_time': accel_time + const_time + decel_time,
            'direction': direction
        }
    
    def get_position_at_time(self, 
                           profile: Dict[str, float],
                           start_pos: float,
                           current_time: float) -> Tuple[float, float]:
        """
        Berechnet Position und Geschwindigkeit zu einem bestimmten Zeitpunkt
        
        Args:
            profile: Bewegungsprofil von calculate_profile()
            start_pos: Startposition
            current_time: Aktueller Zeitpunkt in der Bewegung
            
        Returns:
            (position, velocity)
        """
        v = profile['velocity']
        a = profile['acceleration']
        t1 = profile['accel_time']
        t2 = t1 + profile['const_time']
        t3 = t2 + profile['decel_time']
        
        if current_time <= t1:  # Beschleunigungsphase
            pos = start_pos + 0.5 * a * current_time**2
            vel = a * current_time
        elif current_time <= t2:  # Konstante Geschwindigkeit
            pos = start_pos + 0.5 * a * t1**2 + v * (current_time - t1)
            vel = v
        elif current_time <= t3:  # Verzögerungsphase
            dt = current_time - t2
            pos = (start_pos + v * t2 + 
                  v * dt - 0.5 * a * dt**2)
            vel = v - a * dt
        else:  # Bewegung beendet
            pos = start_pos + profile['direction'] * abs(v * t2)
            vel = 0.0
            
        return pos, vel
