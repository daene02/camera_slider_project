#!/usr/bin/env python3
"""
Interaktives Test-Skript für Dynamixel Manager
Fokus auf Velocity PID und andere kritische Register
"""

import sys
import time
from typing import Dict, Any
from src.dxl_manager import DynamixelManager
from src.settings import MOTOR_IDS, MOTOR_NAMES

class InteractiveTester:
    def __init__(self):
        self.manager = DynamixelManager()
        self.current_motor = None

    def print_header(self, text: str):
        print("\n" + "="*50)
        print(text)
        print("="*50)

    def read_single_register(self, motor_id: int, address: int, size: int) -> int:
        """Liest einen einzelnen Register direkt"""
        with self.manager.lock:
            try:
                result, value, error = self.manager.packetHandler.read2ByteTxRx(
                    self.manager.portHandler, motor_id, address)
                if result != 0 or error != 0:
                    print(f"Fehler beim Lesen: {result}, {error}")
                    return None
                return value
            except Exception as e:
                print(f"Fehler: {str(e)}")
                return None

    def write_single_register(self, motor_id: int, address: int, value: int) -> bool:
        """Schreibt einen einzelnen Register direkt"""
        with self.manager.lock:
            try:
                result, error = self.manager.packetHandler.write2ByteTxRx(
                    self.manager.portHandler, motor_id, address, value)
                if result != 0 or error != 0:
                    print(f"Fehler beim Schreiben: {result}, {error}")
                    return False
                return True
            except Exception as e:
                print(f"Fehler: {str(e)}")
                return False

    def test_single_motor(self, motor_id: int):
        """Testet alle Register eines Motors"""
        self.print_header(f"Test Motor ID {motor_id} ({MOTOR_NAMES.get(motor_id, 'Unbekannt')})")
        
        # Velocity I Gain (Address 762)
        i_gain = self.read_single_register(motor_id, 76, 2)
        print(f"Velocity I Gain (762): {i_gain}")
        
        # Velocity P Gain (Address 782)
        p_gain = self.read_single_register(motor_id, 78, 2)
        print(f"Velocity P Gain (782): {p_gain}")
        
        # Position P Gain (Address 84)
        pos_p = self.read_single_register(motor_id, 84, 2)
        print(f"Position P Gain (84): {pos_p}")

    def manual_register_access(self):
        """Ermöglicht manuellen Zugriff auf Register"""
        self.print_header("Manueller Register-Zugriff")
        
        while True:
            print("\n1. Register lesen")
            print("2. Register schreiben")
            print("0. Zurück")
            
            choice = input("\nWähle eine Option: ")
            
            if choice == "0":
                break
                
            motor_id = int(input("Motor ID: "))
            address = int(input("Register-Adresse: "))
            
            if choice == "1":
                value = self.read_single_register(motor_id, address, 2)
                print(f"Wert: {value}")
            elif choice == "2":
                value = int(input("Neuer Wert: "))
                if self.write_single_register(motor_id, address, value):
                    print("Erfolgreich geschrieben")
                else:
                    print("Fehler beim Schreiben")

    def main_menu(self):
        """Hauptmenü"""
        while True:
            self.print_header("Dynamixel Register Test")
            print("\n1. Motor für Test auswählen")
            print("2. Manueller Register-Zugriff")
            print("3. Velocity PID Test")
            print("0. Beenden")
            
            try:
                choice = input("\nWähle eine Option: ")
                
                if choice == "0":
                    break
                elif choice == "1":
                    print("\nVerfügbare Motoren:")
                    for motor_id in self.manager.dxl_ids:
                        print(f"{motor_id}: {MOTOR_NAMES.get(motor_id, 'Unbekannt')}")
                    motor_id = int(input("\nMotor ID wählen: "))
                    self.test_single_motor(motor_id)
                elif choice == "2":
                    self.manual_register_access()
                elif choice == "3":
                    self.test_velocity_pid()
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Fehler: {str(e)}")
                continue
                
            input("\nDrücke Enter um fortzufahren...")

    def test_velocity_pid(self):
        """Testet Velocity PID Register"""
        self.print_header("Velocity PID Test")
        
        # Test für jeden Motor
        for motor_id in self.manager.dxl_ids:
            print(f"\nTeste Motor {motor_id} ({MOTOR_NAMES.get(motor_id, 'Unbekannt')})")
            
            # Direkte Register-Lesezugriffe
            i_gain = self.read_single_register(motor_id, 76, 2)
            p_gain = self.read_single_register(motor_id, 78, 2)
            
            print(f"Direkte Register-Lesung:")
            print(f"Velocity I Gain (76): {i_gain}")
            print(f"Velocity P Gain (78): {p_gain}")
            
            # Test der Manager-Funktionen
            print("\nTest über Manager-Funktionen:")
            gains = self.manager.bulk_read_velocity_pid_gains()
            if motor_id in gains:
                print(f"Bulk Read Gains: {gains[motor_id]}")
            else:
                print("Keine Gains über Bulk Read verfügbar")
            
            # Optional: Schreiben testen
            if input("\nVelocity PID Werte setzen? (j/n): ").lower() == 'j':
                try:
                    new_i = int(input("Neuer I-Gain (1-16383): "))
                    new_p = int(input("Neuer P-Gain (1000-16383): "))
                    
                    # Direktes Schreiben
                    print("\nSchreibe Werte direkt...")
                    if self.write_single_register(motor_id, 76, new_i):
                        print(f"I-Gain erfolgreich gesetzt")
                    if self.write_single_register(motor_id, 78, new_p):
                        print(f"P-Gain erfolgreich gesetzt")
                        
                    # Verifizieren
                    time.sleep(0.1)
                    i_gain = self.read_single_register(motor_id, 76, 2)
                    p_gain = self.read_single_register(motor_id, 78, 2)
                    print(f"\nNeue Werte:")
                    print(f"Velocity I Gain: {i_gain}")
                    print(f"Velocity P Gain: {p_gain}")
                    
                except ValueError:
                    print("Ungültige Eingabe")
                except Exception as e:
                    print(f"Fehler: {str(e)}")

if __name__ == "__main__":
    tester = InteractiveTester()
    try:
        tester.main_menu()
    finally:
        tester.manager.disable_torque()
        tester.manager.close()
