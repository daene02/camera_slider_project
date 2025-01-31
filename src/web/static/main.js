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

    // Update each value display
    motorElement.querySelector('.position-value').textContent = data.position;
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
    const position = parseInt(input.value);
    
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
