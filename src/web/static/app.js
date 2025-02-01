function runScript(scriptPath) {
    fetch('/run_script', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ script: scriptPath }),
    })
    .then(response => {
        if (response.ok) {
            console.log(`${scriptPath} erfolgreich ausgeführt.`);
        } else {
            console.error(`Fehler beim Ausführen von ${scriptPath}:`, response.statusText);
        }
    })
    .catch(error => console.error('Fehler:', error));
}

// Motor Control Script (modified to handle separate bulk calls for position, temperature, current, etc.)

/**
 * Ruft beim Server einen kombinierten Endpunkt auf, der Positionen, Temperatur,
 * Spannung und Strom der Motoren per Bulk-Leseoperationen ermittelt und
 * als JSON zurückgibt.
 * Erwartete Server-Antwort:
 * {
 *   "status": "success",
 *   "data": {
 *     "1": { "position": 2048, "temperature": 35, "current": 21, "voltage": 120 },
 *     "2": { "position": 1024, "temperature": 36, "current": 10, "voltage": 120 }
 *     ...
 *   }
 * }
 */
function fetchMotorData() {
    fetch('/bulk_read_data')
        .then(response => response.json())
        .then(data => {
            if (data.status === "success") {
                for (const [motorName, info] of Object.entries(data.data)) {
                    const motorId = MOTOR_IDS[motorName];
                    const posElem = document.getElementById(`current_position_${motorName}`);
                    const tempElem = document.getElementById(`temperature_${motorName}`);
                    const currElem = document.getElementById(`current_${motorName}`);
                    const voltElem = document.getElementById(`voltage_${motorName}`);

                    if (posElem) posElem.innerText = info.position?.toFixed(2) ?? '-';
                    if (tempElem) tempElem.innerText = info.temperature !== null ? `${info.temperature}°C` : '-';
                    if (currElem) currElem.innerText = info.current !== null ? `${info.current}mA` : '-';
                    if (voltElem) voltElem.innerText = info.voltage !== null ? `${info.voltage/10}V` : '-';
                }
            } else {
                console.error('Fehler beim Abrufen der Motordaten:', data.message);
            }
        })
        .catch(error => console.error('Fehler beim Abrufen der Motordaten:', error));
}

/**
 * Schickt ein POST an '/set_motor', um den Servo mit goal_position
 * und einer Profilgeschwindigkeit zu setzen.
 * Die Dauer (Sekunden) wird in 'profile_velocity' (z.B. ms) umgerechnet.
 */
function setMotor(motorId) {
      const goalPositionElement = document.getElementById(`goal_position_input_${motorId}`);
      const velocityElement = document.getElementById(`duration_${motorId}`);

      if (!goalPositionElement || !velocityElement) {
        console.error(`Elemente für Motor ID=${motorId} nicht gefunden.`);
        alert(`Fehler: Elemente für Motor ${motorId} fehlen.`);
        return;
      }

      const goalPosition = parseFloat(goalPositionElement.value);
      const profileVelocityInSeconds = parseFloat(velocityElement.value);

      if (isNaN(goalPosition) || isNaN(profileVelocityInSeconds) || profileVelocityInSeconds <= 0) {
        alert("Fehler: Ungültige Eingaben!");
        return;
      }

      // Beispiel: wir interpretieren 'Dauer' -> Velocity (einfacher Ansatz)
      const profileVelocity = profileVelocityInSeconds * 1000;

      console.log(`Sende: Motor ID=${motorId}, Zielposition=${goalPosition}, Profilgeschwindigkeit=${profileVelocity} ms/s`);

      fetch('/set_motor', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          motor_id: motorId,
          goal_position: goalPosition,
          profile_velocity: profileVelocity
        })
      })
      .then(response => {
        if (!response.ok) {
          return response.text().then(error => {
            throw new Error(`HTTP-Fehler ${response.status}: ${error}`);
          });
        }
        return response.json();
      })
      .then(data => {
        console.log(`Antwort: ${JSON.stringify(data)}`);
        if (data.status === "success") {
          alert(`Motor ${motorId} erfolgreich gesetzt.`);
        } else {
          alert(`Fehler: ${data.message}`);
        }
      })
      .catch(error => {
        console.error('Fehler beim Setzen des Motors:', error);
        alert('Fehler beim Setzen des Motors!');
      });
    }

    /**
     * Baut dynamisch eine Box für jeden Motor.
     * Erwartet, dass ein <div id="motor_controls"> im DOM existiert.
     */
function createMotorBox(motorId, motorName) {
      const container = document.getElementById('motor_controls');
      const motorBox = document.createElement('div');
      motorBox.className = 'motor-box';

      motorBox.innerHTML = `
        <h3>${motorName} (ID: ${motorId})</h3>
        <p>Aktuelle Position: <span id="current_position_${motorId}">-</span></p>
        <p>Temperatur: <span id="temperature_${motorId}">-</span></p>
        <p>Strom: <span id="current_${motorId}">-</span></p>
        <p>Spannung: <span id="voltage_${motorId}">-</span></p>

        <label for="goal_position_input_${motorId}">Zielposition:</label>
        <input type="number" id="goal_position_input_${motorId}" min="0" max="4096" step="1" value="0">
        <inbel for="duration_${motorId}">Dauer (Sek.):</label>
        <input type="number" id="duration_${motorId}" min="1" , max="32000" ,step="1" value="5000">
        <button onclick="setMotor(${motorId})">Setzen</button>
      `;

      container.appendChild(motorBox);
}


function saveProfile() {
    const profileName = document.getElementById('profile_name').value;
    if (!profileName) {
        alert('Bitte einen Profilnamen eingeben!');
        return;
    }

    fetch('/save_profile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ profile_name: profileName })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            alert('Profil erfolgreich gespeichert.');
            updateProfileList();
        } else {
            alert(`Fehler beim Speichern des Profils: ${data.message}`);
        }
    })
    .catch(error => {
        console.error('Fehler beim Speichern des Profils:', error);
        alert('Fehler beim Speichern des Profils.');
    });
}
    const profileName = document.getElementById('profile_name').value;
    if (!profileName) {
        alert('Bitte einen Profilnamen eingeben!');
        return;
    }

    fetch('/save_profile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ profile_name: profileName })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            alert('Profil erfolgreich gespeichert.');
            updateProfileList();
        } else {
            alert(`Fehler beim Speichern des Profils: ${data.message}`);
        }
    })
    .catch(error => {
        console.error('Fehler beim Speichern des Profils:', error);
        alert('Fehler beim Speichern des Profils.');
    });
}

function addPointToProfile() {
    const profileName = document.getElementById('profile_name').value;
    if (!profileName) {
        alert('Bitte einen Profilnamen eingeben, bevor ein Punkt hinzugefügt wird!');
        return;
    }

    fetch('/add_point', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ profile_name: profileName })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            alert('Punkt erfolgreich zum Profil hinzugefügt.');
        } else {
            alert(`Fehler beim Hinzufügen eines Punktes: ${data.message}`);
        }
    })
    .catch(error => {
        console.error('Fehler beim Hinzufügen eines Punktes:', error);
        alert('Fehler beim Hinzufügen eines Punktes.');
    });
}
    const profileName = document.getElementById('profile_name').value;
    if (!profileName) {
        alert('Bitte einen Profilnamen eingeben, bevor ein Punkt hinzugefügt wird!');
        return;
    }

    fetch('/add_point', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ profile_name: profileName })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            alert('Punkt erfolgreich zum Profil hinzugefügt.');
        } else {
            alert(`Fehler beim Hinzufügen eines Punktes: ${data.message}`);
        }
    })
    .catch(error => {
        console.error('Fehler beim Hinzufügen eines Punktes:', error);
        alert('Fehler beim Hinzufügen eines Punktes.');
    });
}

function playProfile() {
    const profileName = document.getElementById('profile_list').value;
    if (!profileName) {
        alert('Bitte ein Profil auswählen!');
        return;
    }

    fetch('/play_profile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ profile_name: profileName })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            alert('Profil erfolgreich gestartet.');
        } else {
            alert(`Fehler beim Starten des Profils: ${data.message}`);
        }
    })
    .catch(error => {
        console.error('Fehler beim Starten des Profils:', error);
        alert('Fehler beim Starten des Profils.');
    });
}
    const profileName = document.getElementById('profile_list').value;
    if (!profileName) {
        alert('Bitte ein Profil auswählen!');
        return;
    }

    fetch('/play_profile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ profile_name: profileName })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            alert('Profil erfolgreich gestartet.');
        } else {
            alert(`Fehler beim Starten des Profils: ${data.message}`);
        }
    })
    .catch(error => {
        console.error('Fehler beim Starten des Profils:', error);
        alert('Fehler beim Starten des Profils.');
    });
}

function startFocusTracking() {
    const startPos = parseFloat(document.getElementById('focus_start_pos').value);
    const endPos = parseFloat(document.getElementById('focus_end_pos').value);
    const duration = parseFloat(document.getElementById('focus_duration').value);
    const numSteps = parseInt(document.getElementById('focus_steps').value);

    fetch('/start_focus_tracking', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            start_pos: startPos,
            end_pos: endPos,
            duration: duration,
            num_steps: numSteps,
            velocity: 8000,
            acceleration: 5000
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            alert('Fokus-Tracking gestartet');
        } else {
            alert(`Fehler: ${data.message}`);
        }
    })
    .catch(error => {
        console.error('Fehler:', error);
        alert('Fehler beim Starten des Fokus-Trackings');
    });
}

function updateObjectPosition() {
    const x = parseFloat(document.getElementById('object_x').value);
    const y = parseFloat(document.getElementById('object_y').value);
    const z = parseFloat(document.getElementById('object_z').value);

    if (isNaN(x) || isNaN(y) || isNaN(z)) {
        alert('Bitte gültige Zahlenwerte für die Position eingeben');
        return;
    }

    fetch('/update_object_position', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ x, y, z })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            updateStatus('Objektposition aktualisiert');
        } else {
            updateStatus('Fehler: ' + data.message);
        }
    })
    .catch(error => updateStatus('Fehler: ' + error));
}

function updateMotionSettings() {
    const interpolationSteps = parseInt(document.getElementById('interpolation_steps').value);
    const velocityScale = parseInt(document.getElementById('velocity_scale').value);
    const accelerationScale = parseInt(document.getElementById('acceleration_scale').value);

    if (isNaN(interpolationSteps) || isNaN(velocityScale) || isNaN(accelerationScale)) {
        alert('Bitte gültige Zahlenwerte eingeben');
        return;
    }

    fetch('/update_motion_settings', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            interpolation_steps: interpolationSteps,
            velocity_scale: velocityScale,
            acceleration_scale: accelerationScale
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            updateStatus('Bewegungseinstellungen aktualisiert');
        } else {
            updateStatus('Fehler: ' + data.message);
        }
    })
    .catch(error => updateStatus('Fehler: ' + error));
}

function initializeInterface() {
    const container = document.createElement('div');
    container.id = 'motor_controls';
    document.body.appendChild(container);

    for (const [motorName, motorId] of Object.entries(MOTOR_IDS)) {
        createMotorBox(motorId, motorName);
    }

    const profileBox = document.createElement('div');
    profileBox.id = 'profile_controls';
    profileBox.innerHTML = `
        <h3>Profile Verwaltung</h3>
        <label for="profile_name">Profilname:</label>
        <input type="text" id="profile_name">
        <button onclick="saveProfile()">Profil speichern</button>
        <button onclick="addPointToProfile()">Punkt speichern</button>
        <button onclick="playProfile()">Profil abspielen</button>
        <select id="profile_list"></select>
    `;
    document.body.appendChild(profileBox);

    const torqueBox = document.createElement('div');
    torqueBox.id = 'torque_controls';
    torqueBox.innerHTML = `
        <h3>Drehmoment Steuerung</h3>
        <button onclick="toggleAllTorque(true)">Torque An</button>
        <button onclick="toggleAllTorque(false)">Torque Aus</button>
    `;
    document.body.appendChild(torqueBox);

    const scriptBox = document.createElement('div');
    scriptBox.id = 'script_controls';
    scriptBox.innerHTML = `
        <h3>Skriptsteuerung</h3>
        <button onclick="runScript('video_drehteller1')">Video Drehteller 1</button>
        <button onclick="runScript('zeitlupe_start')">Zeitlupe Start</button>
        <button onclick="runScript('zeitlupe_stop')">Zeitlupe Stop</button>
    `;
    document.body.appendChild(scriptBox);

    const errorBox = document.createElement('div');
    errorBox.id = 'error_logs';
    errorBox.innerHTML = `
        <h3>Fehlermeldungen</h3>
        <div id="error_display">Keine Fehlermeldungen</div>
    `;
    document.body.appendChild(errorBox);

    // Add focus tracking controls
    const focusBox = document.createElement('div');
    focusBox.id = 'focus_controls';
    focusBox.innerHTML = `
        <h3>Fokus-Tracking</h3>
        <div>
            <label for="focus_start_pos">Start Position (mm):</label>
            <input type="number" id="focus_start_pos" value="0">
        </div>
        <div>
            <label for="focus_end_pos">End Position (mm):</label>
            <input type="number" id="focus_end_pos" value="600">
        </div>
        <div>
            <label for="focus_duration">Dauer (s):</label>
            <input type="number" id="focus_duration" value="30">
        </div>
        <div>
            <label for="focus_steps">Anzahl Schritte:</label>
            <input type="number" id="focus_steps" value="50">
        </div>
        <button onclick="startFocusTracking()">Fokus-Tracking starten</button>
    `;
    document.body.appendChild(focusBox);

    // Add motion settings controls
    const motionSettingsBox = document.createElement('div');
    motionSettingsBox.id = 'motion_settings_controls';
    motionSettingsBox.innerHTML = `
        <h3>Bewegungseinstellungen</h3>
        <div>
            <label for="interpolation_steps">Interpolationsschritte:</label>
            <input type="number" id="interpolation_steps" value="10">
        </div>
        <div>
            <label for="velocity_scale">Geschwindigkeitsskala:</label>
            <input type="number" id="velocity_scale" value="100">
        </div>
        <div>
            <label for="acceleration_scale">Beschleunigungsskala:</label>
            <input type="number" id="acceleration_scale" value="100">
        </div>
        <button onclick="updateMotionSettings()">Bewegungseinstellungen aktualisieren</button>
    `;
    document.body.appendChild(motionSettingsBox);

    setInterval(fetchMotorData, 2000);
}

document.addEventListener('DOMContentLoaded', initializeInterface);
