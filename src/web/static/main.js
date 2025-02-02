// Conversion factors (matching motor_controller.py)
const CONVERSION_FACTORS = {
    1: 360 / 4096,    // Turntable: 1 rotation = 360 degrees
    2: 64 / 4096,     // Slider: 1 rotation = 64mm
    3: 360 / 4096,    // Pan: 1 rotation = 360 degrees
    4: 360 / 4096,    // Tilt: 1 rotation = 360 degrees
    5: 360 / 4096,    // Zoom: 1 rotation = 360 degrees
    6: 360 / 4096     // Focus: 1 rotation = 360 degrees
};

// Motor type mapping
const MOTOR_TYPES = {
    1: "turntable",
    2: "slider",
    3: "pan",
    4: "tilt",
    5: "zoom",
    6: "focus"
};

// Get the unit for a motor
function getMotorUnit(motorId) {
    return motorId === 2 ? "mm" : "°";  // Only slider uses mm, all others use degrees
}

// Convert steps to units (mm or degrees)
function stepsToUnits(steps, motorId) {
    if (!CONVERSION_FACTORS[motorId]) return steps;
    let value = steps * CONVERSION_FACTORS[motorId];
    if (motorId === 3 || motorId === 4) { // Pan or Tilt
        value = value - 180; // Apply offset
    }
    return Math.round(value * 100) / 100; // Round to 2 decimal places
}

// Convert units (mm or degrees) to steps
function unitsToSteps(units, motorId) {
    if (!CONVERSION_FACTORS[motorId]) return units;
    if (motorId === 3 || motorId === 4) { // Pan or Tilt
        units = parseFloat(units) + 180; // Apply offset
    }
    return Math.round(units / CONVERSION_FACTORS[motorId]);
}

function updateMotorData(motorId, data) {
    const motorElement = document.querySelector(`[data-motor-id="${motorId}"]`);
    if (!motorElement) return;

    // Update motor name color and border based on torque status
    const motorName = motorElement.querySelector('.motor-name');
    if (motorName) {
        const color = data.torque_enabled ? 'rgba(0,255,0,1)' : 'rgba(255,0,0,1)';
        motorName.style.color = color;
        motorElement.style.borderColor = color;
    }

    // Convert position to proper units and update display
    const convertedPosition = stepsToUnits(data.position, motorId);
    const unit = getMotorUnit(motorId);
    motorElement.querySelector('.position-value').textContent = `${convertedPosition}${unit}`;
    motorElement.querySelector('.temperature-value').textContent = data.temperature;
    motorElement.querySelector('.voltage-value').textContent = data.voltage;
    motorElement.querySelector('.current-value').textContent = data.current;
    motorElement.querySelector('.speed-value').textContent = data.speed;
    motorElement.querySelector('.load-value').textContent = data.load;
}

function toggleTorque(motorId, enable) {
    fetch(`/torque/${motorId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ enable: enable })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const motorBox = document.querySelector(`[data-motor-id="${motorId}"]`);
            const motorName = motorBox.querySelector('.motor-name');
            const color = enable ? 'rgba(0,255,0,1)' : 'rgba(255,0,0,1)';
            if (motorName) {
                motorName.style.color = color;
                motorBox.style.borderColor = color;
            }
        }
    })
    .catch(error => console.error('Error:', error));
}

function toggleAllTorque(enable) {
    fetch('/torque/all', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ enable: enable })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const color = enable ? 'rgba(0,255,0,1)' : 'rgba(255,0,0,1)';
            document.querySelectorAll('.motor-box').forEach(box => {
                const name = box.querySelector('.motor-name');
                if (name) {
                    name.style.color = color;
                    box.style.borderColor = color;
                }
            });
        }
    })
    .catch(error => console.error('Error:', error));
}

function updateMotorPosition(motorId) {
    const input = document.getElementById(`position_${motorId}`);
    const unitValue = parseFloat(input.value);
    const position = unitsToSteps(unitValue, motorId);
    
    fetch(`/motor/${motorId}/position`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ position: position })
    })
    .catch(error => console.error('Error:', error));
}

function updateMotorVelocity(motorId) {
    const input = document.getElementById(`velocity_${motorId}`);
    const velocity = parseInt(input.value);
    
    fetch(`/motor/${motorId}/velocity`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ velocity: velocity })
    })
    .catch(error => console.error('Error:', error));
}

function updateMotorAcceleration(motorId) {
    const input = document.getElementById(`acceleration_${motorId}`);
    const acceleration = parseInt(input.value);
    
    fetch(`/motor/${motorId}/acceleration`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ acceleration: acceleration })
    })
    .catch(error => console.error('Error:', error));
}

// Update motor values every 2 seconds
setInterval(() => {
    fetch('/motor/status')
        .then(response => response.json())
        .then(motors => {
            motors.forEach(motor => {
                updateMotorData(motor.id, motor);
            });
        })
        .catch(error => console.error('Error fetching motor status:', error));
}, 2000);
