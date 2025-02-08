#!/usr/bin/env python3
"""
Test-Skript für den Dynamixel Manager
Testet alle Funktionen der neuen modularen Implementierung
"""

import sys
import time
from typing import Dict, Any

# Farbkonstanten für Konsolenausgabe
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    YELLOW = '\033[93m'
    RESET = '\033[0m'
from src.dxl_manager import DynamixelManager
from src.settings import MOTOR_IDS, MOTOR_NAMES

class DynamixelTester:
    def __init__(self):
        self.manager = DynamixelManager()
        print(f"{Colors.BLUE}DynamixelManager initialisiert{Colors.RESET}")

    def print_success(self, message: str):
        print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")

    def print_error(self, message: str):
        print(f"{Colors.RED}✗ {message}{Colors.RESET}")

    def print_info(self, message: str):
        print(f"{Colors.CYAN}ℹ {message}{Colors.RESET}")

    def test_basic_functions(self):
        """Test grundlegender Funktionen"""
        print("\n=== Teste Basis-Funktionen ===")
        
        # Test Torque Enable/Disable
        print("\nTeste Torque Enable/Disable...")
        try:
            self.manager.disable_torque()
            self.print_success("Torque Disable erfolgreich")
            
            self.manager.enable_torque()
            self.print_success("Torque Enable erfolgreich")
            
            torque_states = self.manager.bulk_read_torque_enable()
            self.print_info(f"Torque Status: {torque_states}")
        except Exception as e:
            self.print_error(f"Torque Test fehlgeschlagen: {str(e)}")

        # Test Positionsabfrage
        print("\nTeste Positionsabfrage...")
        try:
            positions = self.manager.bulk_read_positions()
            self.print_success("Positionsabfrage erfolgreich")
            self.print_info(f"Positionen: {positions}")
        except Exception as e:
            self.print_error(f"Positionsabfrage fehlgeschlagen: {str(e)}")

    def test_motion_control(self):
        """Test der Bewegungssteuerung"""
        print("\n=== Teste Bewegungssteuerung ===")
        
        # Test Geschwindigkeitsprofile
        print("\nTeste Geschwindigkeitsprofile...")
        try:
            velocities = self.manager.bulk_read_profile_velocity()
            self.print_success("Geschwindigkeitsprofile auslesen erfolgreich")
            self.print_info(f"Geschwindigkeiten: {velocities}")
            
            test_velocity = {2: 100}  # Test mit Slider
            self.manager.bulk_write_profile_velocity(test_velocity)
            self.print_success("Geschwindigkeitsprofil setzen erfolgreich")
        except Exception as e:
            self.print_error(f"Geschwindigkeitstest fehlgeschlagen: {str(e)}")

        # Test Beschleunigungsprofile
        print("\nTeste Beschleunigungsprofile...")
        try:
            accels = self.manager.bulk_read_profile_acceleration()
            self.print_success("Beschleunigungsprofile auslesen erfolgreich")
            self.print_info(f"Beschleunigungen: {accels}")
            
            test_accel = {2: 50}  # Test mit Slider
            self.manager.bulk_write_profile_acceleration(test_accel)
            self.print_success("Beschleunigungsprofil setzen erfolgreich")
        except Exception as e:
            self.print_error(f"Beschleunigungstest fehlgeschlagen: {str(e)}")

    def test_pid_settings(self):
        """Test der PID-Einstellungen"""
        print("\n=== Teste PID-Einstellungen ===")
        
        # Position PID
        print("\nTeste Position PID...")
        try:
            pos_gains = self.manager.bulk_read_position_pid_gains()
            self.print_success("Position PID auslesen erfolgreich")
            self.print_info(f"Position PID Werte: {pos_gains}")
            
            test_pos_pid = {
                2: {'p': 800, 'i': 0, 'd': 0}  # Test mit Slider
            }
            self.manager.bulk_write_position_pid_gains(test_pos_pid)
            self.print_success("Position PID setzen erfolgreich")
        except Exception as e:
            self.print_error(f"Position PID Test fehlgeschlagen: {str(e)}")

        # Velocity PID
        print("\nTeste Velocity PID...")
        try:
            vel_gains = self.manager.bulk_read_velocity_pid_gains()
            self.print_success("Velocity PID auslesen erfolgreich")
            self.print_info(f"Velocity PID Werte: {vel_gains}")
            
            test_vel_pid = {
                2: {'p': 1000, 'i': 100}  # Test mit Slider
            }
            self.manager.bulk_write_velocity_pid_gains(test_vel_pid)
            self.print_success("Velocity PID setzen erfolgreich")
        except Exception as e:
            self.print_error(f"Velocity PID Test fehlgeschlagen: {str(e)}")

    def test_status_readings(self):
        """Test der Status-Abfragen"""
        print("\n=== Teste Status-Abfragen ===")
        
        # Temperatur
        print("\nTeste Temperaturabfrage...")
        try:
            temps = self.manager.bulk_read_temperature()
            self.print_success("Temperaturabfrage erfolgreich")
            self.print_info(f"Temperaturen: {temps}")
        except Exception as e:
            self.print_error(f"Temperaturtest fehlgeschlagen: {str(e)}")

        # Spannung
        print("\nTeste Spannungsabfrage...")
        try:
            volts = self.manager.bulk_read_voltage()
            self.print_success("Spannungsabfrage erfolgreich")
            self.print_info(f"Spannungen: {volts}")
        except Exception as e:
            self.print_error(f"Spannungstest fehlgeschlagen: {str(e)}")

        # Strom
        print("\nTeste Stromabfrage...")
        try:
            currents = self.manager.bulk_read_current()
            self.print_success("Stromabfrage erfolgreich")
            self.print_info(f"Ströme: {currents}")
        except Exception as e:
            self.print_error(f"Stromtest fehlgeschlagen: {str(e)}")

    def run_movement_test(self):
        """Führt einen interaktiven Bewegungstest durch"""
        print("\n=== Bewegungstest ===")
        
        try:
            # Aktuelle Positionen anzeigen
            positions = self.manager.bulk_read_positions()
            print("\nAktuelle Positionen:")
            for motor_id, pos in positions.items():
                name = MOTOR_NAMES.get(motor_id, f"Motor {motor_id}")
                print(f"{name} (ID {motor_id}): {pos}")

            # Benutzer wählt Motor und Position
            motor_id = int(input("\nMotor ID zum Testen: "))
            if motor_id not in MOTOR_IDS:
                self.print_error("Ungültige Motor ID")
                return
                
            target = int(input("Zielposition (0-4095): "))
            if target < 0 or target > 4095:
                self.print_error("Ungültige Position")
                return

            # Bewegung ausführen
            self.print_info(f"Bewege Motor {motor_id} zu Position {target}...")
            self.manager.bulk_write_goal_positions({motor_id: target})
            
            # Warte und zeige neue Position
            time.sleep(2)
            new_pos = self.manager.bulk_read_positions()[motor_id]
            self.print_info(f"Neue Position: {new_pos}")
            
            if abs(new_pos - target) < 20:
                self.print_success("Bewegungstest erfolgreich")
            else:
                self.print_error("Position nicht genau erreicht")
                
        except Exception as e:
            self.print_error(f"Bewegungstest fehlgeschlagen: {str(e)}")

    def cleanup(self):
        """Aufräumen nach den Tests"""
        try:
            self.manager.disable_torque()
            self.print_success("Torque disabled")
        except:
            self.print_error("Fehler beim Deaktivieren des Torque")
        finally:
            self.manager.close()

def main():
    tester = DynamixelTester()
    
    while True:
        print(f"\n{Colors.YELLOW}=== Dynamixel Manager Test Menu ==={Colors.RESET}")
        print("1. Test Basis-Funktionen")
        print("2. Test Bewegungssteuerung")
        print("3. Test PID-Einstellungen")
        print("4. Test Status-Abfragen")
        print("5. Interaktiver Bewegungstest")
        print("0. Beenden")
        
        try:
            choice = input("\nWähle einen Test (0-5): ")
            
            if choice == "1":
                tester.test_basic_functions()
            elif choice == "2":
                tester.test_motion_control()
            elif choice == "3":
                tester.test_pid_settings()
            elif choice == "4":
                tester.test_status_readings()
            elif choice == "5":
                tester.run_movement_test()
            elif choice == "0":
                print("\nBeende Tests...")
                break
            else:
                print(f"{Colors.RED}Ungültige Eingabe{Colors.RESET}")
                
            input("\nDrücke Enter um fortzufahren...")
                
        except KeyboardInterrupt:
            print("\nTest abgebrochen")
            break
        except Exception as e:
            print(f"{Colors.RED}Fehler: {str(e)}{Colors.RESET}")
            break
            
    tester.cleanup()

if __name__ == "__main__":
    main()
