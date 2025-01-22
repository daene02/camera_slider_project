function saveProfile() {
    const profileName = document.getElementById('profile_name').value;
    if (!profileName) {
        alert('Bitte einen Profilnamen eingeben.');
        return;
    }
    fetch('/save_profile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: profileName, points })
    }).then(response => response.json()).then(data => {
        if (data.status === 'success') {
            alert(`Profil "${profileName}" gespeichert.`);
        } else {
            alert(`Fehler: ${data.message}`);
        }
    }).catch(error => console.error('Fehler beim Speichern des Profils:', error));
}

function loadProfile() {
    const profileName = document.getElementById('profile_name').value;
    if (!profileName) {
        alert('Bitte einen Profilnamen eingeben.');
        return;
    }
    fetch('/load_profile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: profileName })
    }).then(response => response.json()).then(data => {
        if (data.status === 'success') {
            points = data.points;
            updatePointList();
            alert(`Profil "${profileName}" geladen.`);
        } else {
            alert(`Fehler: ${data.message}`);
        }
    }).catch(error => console.error('Fehler beim Laden des Profils:', error));
}

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

    const profileVelocity = profileVelocityInSeconds * 1000;

    console.log(`Sende: Motor ID=${motorId}, Zielposition=${goalPosition}, Profilgeschwindigkeit=${profileVelocity} ms`);
    fetch('/set_motor', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ motor_id: motorId, goal_position: goalPosition, profile_velocity: profileVelocity })
    }).then(response => {
        if (!response.ok) {
            return response.text().then(error => {
                throw new Error(`HTTP-Fehler ${response.status}: ${error}`);
            });
        }
        return response.json();
    }).then(data => {
        console.log(`Antwort: ${JSON.stringify(data)}`);
        if (data.status === "success") {
            alert(`Motor ${motorId} erfolgreich gesetzt.`);
        } else {
            alert(`Fehler: ${data.message}`);
        }
    }).catch(error => {
        console.error('Fehler beim Setzen des Motors:', error);
        alert('Fehler beim Setzen des Motors!');
    });
}

function fetchMotorData() {
    fetch('/motor_data')
        .then(response => response.json())
        .then(data => {
            document.getElementById('temperature').innerText = `Temperatur: ${data.temperature}°C`;
            document.getElementById('position').innerText = `Position: ${data.current_position}`;
            document.getElementById('current').innerText = `Strom: ${data.current} A`;
            document.getElementById('volt').innerText = `Spannung: ${data.volt} V`;
            document.getElementById('torque').innerText = `Drehmoment: ${data.torque} Nm`;
        })
        .catch(error => console.error('Fehler beim Abrufen der Motordaten:', error));
}

function createMotorBox(motorId, motorName) {
    const container = document.getElementById('motor_controls');
    const motorBox = document.createElement('div');
    motorBox.className = 'motor-box';

    motorBox.innerHTML = `
        <h3>${motorName}</h3>
        <p>Aktuelle Position: <span id="current_position_${motorId}">-</span></p>
        <p>Soll-Position: <span id="goal_position_${motorId}">-</span></p>
        <p>Temperatur: <span id="temperature_${motorId}">-</span></p>
        <label for="goal_position_input_${motorId}">Zielposition:</label>
        <input type="number" id="goal_position_input_${motorId}" min="0" max="4096" step="1" value="0">
        <label for="duration_${motorId}">Dauer (Sekunden):</label>
        <input type="number" id="duration_${motorId}" min="0.1" step="0.1" value="1">
        <button onclick="setMotor(${motorId})">Setzen</button>
    `;

    container.appendChild(motorBox);
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
        <button onclick="loadProfile()">Profil laden</button>
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

    setInterval(fetchMotorData, 2000);

document.addEventListener('DOMContentLoaded', initializeInterface);
