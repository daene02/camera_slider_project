#!/usr/bin/env python3
"""
Umfassender Test aller Dynamixel-Parameter
Liest und schreibt alle verfügbaren Register und Parameter
"""

import sys
import time
from typing import Dict, Any
from src.hardware.dynamixel.pid_manager import DynamixelPIDManager
from src.settings import MOTOR_IDS, MOTOR_NAMES
from src.hardware.dynamixel.constants import *

class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

class BulkParameterTester:
    def __init__(self):
        self.manager = DynamixelPIDManager()
        self.results = []

    def print_header(self, text: str):
        print(f"\n{Colors.BLUE}{'='*50}")
        print(text)
        print(f"{'='*50}{Colors.RESET}")

    def format_row(self, name: str, before: Any, after: Any = None) -> str:
        if after is None:
            return f"| {name:<15} | {str(before):<22} |"
        else:
            status = f"{Colors.GREEN}{before} -> {after}{Colors.RESET}" if before != after else \
                    f"{Colors.YELLOW}{before} -> {after} (unverändert){Colors.RESET}"
            return f"| {name:<15} | {status:<22} |"

    def test_parameter_read(self, motor_id: int):
        """Test Lesen aller Parameter eines Motors"""
        self.print_header(f"Parameter Test Motor {motor_id}")
        
        print("\n+-----------------+------------------------+")
        print("| Parameter       | Value                  |")
        print("+-----------------+------------------------+")

        # Velocity PID
        vel_i = self.manager.bulk_read_velocity_i_gains()[motor_id]
        vel_p = self.manager.bulk_read_velocity_p_gains()[motor_id]
        print(self.format_row("Velocity I", vel_i))
        print(self.format_row("Velocity P", vel_p))

        # Position PID
        pos_p = self.manager.bulk_read_position_p_gains()[motor_id]
        pos_i = self.manager.bulk_read_position_i_gains()[motor_id]
        pos_d = self.manager.bulk_read_position_d_gains()[motor_id]
        print(self.format_row("Position P", pos_p))
        print(self.format_row("Position I", pos_i))
        print(self.format_row("Position D", pos_d))

        print("+-----------------+------------------------+")

    def test_parameter_write(self, motor_id: int):
        """Test Schreiben von Parametern"""
        self.print_header(f"Schreib-Test Motor {motor_id}")

        # Test Werte (angepasste Standard-Werte)
        test_values = {
            "Velocity I": (ADDR_PRO_VELOCITY_I_GAIN, 150),
            "Velocity P": (ADDR_PRO_VELOCITY_P_GAIN, 1100),
            "Position P": (ADDR_PRO_POSITION_P_GAIN, 800),
            "Position I": (ADDR_PRO_POSITION_I_GAIN, 400),
            "Position D": (ADDR_PRO_POSITION_D_GAIN, 100)
        }

        print("\nLese aktuelle Werte...")
        before_values = {
            "Velocity I": self.manager.bulk_read_velocity_i_gains()[motor_id],
            "Velocity P": self.manager.bulk_read_velocity_p_gains()[motor_id],
            "Position P": self.manager.bulk_read_position_p_gains()[motor_id],
            "Position I": self.manager.bulk_read_position_i_gains()[motor_id],
            "Position D": self.manager.bulk_read_position_d_gains()[motor_id]
        }

        print("\n+-----------------+------------------------+")
        print("| Parameter       | Vorher -> Nachher     |")
        print("+-----------------+------------------------+")

        # Parameter einzeln testen
        for name, (addr, value) in test_values.items():
            print(f"\nTeste {name}...")
            success = False
            
            # Schreiben
            if name == "Velocity I":
                success = self.manager.bulk_write_velocity_i_gains({motor_id: value})
            elif name == "Velocity P":
                success = self.manager.bulk_write_velocity_p_gains({motor_id: value})
            elif name == "Position P":
                success = self.manager.bulk_write_position_p_gains({motor_id: value})
            elif name == "Position I":
                success = self.manager.bulk_write_position_i_gains({motor_id: value})
            elif name == "Position D":
                success = self.manager.bulk_write_position_d_gains({motor_id: value})
            
            time.sleep(0.1)  # Warten auf Register-Update
            
            # Neuen Wert lesen
            after_value = None
            if name == "Velocity I":
                after_value = self.manager.bulk_read_velocity_i_gains()[motor_id]
            elif name == "Velocity P":
                after_value = self.manager.bulk_read_velocity_p_gains()[motor_id]
            elif name == "Position P":
                after_value = self.manager.bulk_read_position_p_gains()[motor_id]
            elif name == "Position I":
                after_value = self.manager.bulk_read_position_i_gains()[motor_id]
            elif name == "Position D":
                after_value = self.manager.bulk_read_position_d_gains()[motor_id]

            # Status anzeigen
            print(self.format_row(name, before_values[name], after_value))
            
            # Original wiederherstellen
            if name == "Velocity I":
                self.manager.bulk_write_velocity_i_gains({motor_id: before_values[name]})
            elif name == "Velocity P":
                self.manager.bulk_write_velocity_p_gains({motor_id: before_values[name]})
            elif name == "Position P":
                self.manager.bulk_write_position_p_gains({motor_id: before_values[name]})
            elif name == "Position I":
                self.manager.bulk_write_position_i_gains({motor_id: before_values[name]})
            elif name == "Position D":
                self.manager.bulk_write_position_d_gains({motor_id: before_values[name]})
            
        print("+-----------------+------------------------+")

    def main_menu(self):
        """Hauptmenü"""
        while True:
            self.print_header("Dynamixel Parameter Test")
            print("\nVerfügbare Tests:")
            print("1. Parameter lesen")
            print("2. Parameter schreiben")
            print("3. Beide Tests")
            print("0. Beenden")
            
            try:
                choice = input("\nWahl (0-3): ")
                
                if choice == "0":
                    break
                
                motor_id = int(input("\nMotor ID (1-6): "))
                if motor_id not in self.manager.dxl_ids:
                    print(f"{Colors.RED}Ungültige Motor ID{Colors.RESET}")
                    continue
                    
                if choice == "1":
                    self.test_parameter_read(motor_id)
                elif choice == "2":
                    self.test_parameter_write(motor_id)
                elif choice == "3":
                    self.test_parameter_read(motor_id)
                    self.test_parameter_write(motor_id)
                    self.test_parameter_read(motor_id)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"{Colors.RED}Fehler: {str(e)}{Colors.RESET}")
                continue
            
            input("\nDrücke Enter zum Fortfahren...")

if __name__ == "__main__":
    tester = BulkParameterTester()
    try:
        tester.main_menu()
    finally:
        tester.manager.disable_torque()
        tester.manager.close()
