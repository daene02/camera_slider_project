#!/usr/bin/env python3
"""
Detaillierter Test für einzelne PID-Parameter
Testet jeden Parameter einzeln mit Backup und Wiederherstellung
"""

import sys
import time
from typing import Dict, Any
from src.dxl_manager import DynamixelManager
from src.settings import MOTOR_IDS, MOTOR_NAMES

class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

class PIDParameterTester:
    def __init__(self):
        self.manager = DynamixelManager()
        self.results = []

    def print_header(self, text: str):
        print(f"\n{Colors.BLUE}{'='*50}")
        print(text)
        print(f"{'='*50}{Colors.RESET}")

    def format_result_row(self, param_name: str, original: int, test_value: int, read_value: int) -> str:
        success = test_value == read_value
        status = f"{Colors.GREEN}OK{Colors.RESET}" if success else f"{Colors.RED}FEHLER{Colors.RESET}"
        return f"| {param_name:<12} | {original:<8} | {test_value:<10} | {read_value:<8} | {status:<8} |"

    def test_parameter(self, motor_id: int, param_name: str, address: int, test_value: int):
        """Test eines einzelnen Parameters mit Backup und Wiederherstellung"""
        print(f"\nTeste {param_name} für Motor {motor_id} ({MOTOR_NAMES.get(motor_id, 'Unknown')})...")
        
        # Original-Wert lesen
        original = self.manager._read_register(motor_id, address)
        print(f"Original-Wert: {original}")
        
        # Test-Wert schreiben
        print(f"Schreibe Test-Wert: {test_value}")
        success = self.manager._write_register(motor_id, address, test_value)
        if not success:
            print(f"{Colors.RED}Fehler beim Schreiben{Colors.RESET}")
            return
        
        # Kurze Pause für Register-Update
        time.sleep(0.1)
        
        # Neuen Wert lesen
        read_value = self.manager._read_register(motor_id, address)
        print(f"Gelesener Wert: {read_value}")
        
        # Original wiederherstellen
        print("Stelle Original-Wert wieder her...")
        self.manager._write_register(motor_id, address, original)
        
        # Ergebnis speichern
        self.results.append({
            'param': param_name,
            'original': original,
            'test': test_value,
            'read': read_value
        })

    def print_results_table(self):
        """Zeigt Testergebnisse als Tabelle"""
        print("\nTestergebnisse:")
        print("+--------------+----------+------------+----------+----------+")
        print("| Parameter    | Original | Test-Wert  | Gelesen  | Status   |")
        print("+--------------+----------+------------+----------+----------+")
        for r in self.results:
            print(self.format_result_row(r['param'], r['original'], r['test'], r['read']))
        print("+--------------+----------+------------+----------+----------+")

    def test_all_parameters(self, motor_id: int):
        """Testet alle PID Parameter eines Motors"""
        self.results = []  # Reset results
        self.print_header(f"PID Parameter Test für Motor {motor_id}")

        # Velocity PID Tests
        self.test_parameter(motor_id, "Velocity I", 76, 100)    # I-Gain
        time.sleep(0.1)
        self.test_parameter(motor_id, "Velocity P", 78, 1000)   # P-Gain
        time.sleep(0.1)

        # Position PID Tests
        self.test_parameter(motor_id, "Position P", 84, 800)    # P-Gain
        time.sleep(0.1)
        self.test_parameter(motor_id, "Position I", 82, 0)      # I-Gain
        time.sleep(0.1)
        self.test_parameter(motor_id, "Position D", 80, 0)      # D-Gain
        
        self.print_results_table()

    def main_menu(self):
        """Hauptmenü"""
        while True:
            self.print_header("PID Parameter Test")
            print("\nVerfügbare Tests:")
            print("1. Einzelner Motor Test")
            print("2. Alle Motoren testen")
            print("3. Parameter einzeln testen")
            print("0. Beenden")

            try:
                choice = input("\nWähle eine Option: ")
                
                if choice == "0":
                    break
                elif choice == "1":
                    print("\nVerfügbare Motoren:")
                    for motor_id in self.manager.dxl_ids:
                        print(f"{motor_id}: {MOTOR_NAMES.get(motor_id, 'Unknown')}")
                    motor_id = int(input("\nMotor ID wählen: "))
                    if motor_id in self.manager.dxl_ids:
                        self.test_all_parameters(motor_id)
                    else:
                        print(f"{Colors.RED}Ungültige Motor ID{Colors.RESET}")
                elif choice == "2":
                    for motor_id in self.manager.dxl_ids:
                        self.test_all_parameters(motor_id)
                elif choice == "3":
                    self.parameter_menu()
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"{Colors.RED}Fehler: {str(e)}{Colors.RESET}")
                continue
            
            input("\nDrücke Enter um fortzufahren...")

    def parameter_menu(self):
        """Menü für einzelne Parameter"""
        self.print_header("Parameter Test")
        print("\nVerfügbare Parameter:")
        print("1. Velocity I Gain (76)")
        print("2. Velocity P Gain (78)")
        print("3. Position P Gain (84)")
        print("4. Position I Gain (82)")
        print("5. Position D Gain (80)")
        
        try:
            param = int(input("\nParameter wählen (1-5): "))
            motor_id = int(input("Motor ID: "))
            test_value = int(input("Test-Wert: "))
            
            if motor_id not in self.manager.dxl_ids:
                print(f"{Colors.RED}Ungültige Motor ID{Colors.RESET}")
                return
                
            if param == 1:
                self.test_parameter(motor_id, "Velocity I", 76, test_value)
            elif param == 2:
                self.test_parameter(motor_id, "Velocity P", 78, test_value)
            elif param == 3:
                self.test_parameter(motor_id, "Position P", 84, test_value)
            elif param == 4:
                self.test_parameter(motor_id, "Position I", 82, test_value)
            elif param == 5:
                self.test_parameter(motor_id, "Position D", 80, test_value)
            else:
                print(f"{Colors.RED}Ungültiger Parameter{Colors.RESET}")
                
        except ValueError:
            print(f"{Colors.RED}Ungültige Eingabe{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.RED}Fehler: {str(e)}{Colors.RESET}")

if __name__ == "__main__":
    tester = PIDParameterTester()
    try:
        tester.main_menu()
    finally:
        tester.manager.disable_torque()
        tester.manager.close()
