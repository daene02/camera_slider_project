from modules.drive import Drive

def main():
    drive = Drive()
    drive.enable_motors()

    # Beispiel: Zielpositionen für die Motoren
    goal_positions = {
        "turntable": 1000,
        "slider": 20000,
        "pan": 1500,
        "tilt": 2000,
        "zoom": 1000,
        "focus": 500
    }

    # Setze die Zielpositionen
    drive.set_goal_positions(goal_positions)

    # Warte, bis die Motoren die Positionen erreicht haben
    import time
    time.sleep(5)

    # Lese die aktuellen Positionen
    current_positions = drive.get_current_positions()
    print("Current Positions:", current_positions)

    drive.disable_motors()
    drive.close()

if __name__ == "__main__":
    main()
