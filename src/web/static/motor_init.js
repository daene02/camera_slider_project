// Motor initialization and conversion functions

function stepsToUnits(steps, motorId) {
    // Convert motor steps to user units (mm or degrees)
    const conversionFactors = {
        1: 360/4096,  // turntable (degrees)
        2: 0.08789122581892,  // slider (mm)
        3: 360/4096,  // pan (degrees)
        4: 360/4096,  // tilt (degrees)
        5: 360/4096,  // zoom (degrees)
        6: 360/4096   // focus (degrees)
    };
    
    return (steps * conversionFactors[motorId]).toFixed(2);
}

function unitsToSteps(units, motorId) {
    // Convert user units (mm or degrees) to motor steps
    const conversionFactors = {
        1: 4096/360,  // turntable
        2: 1/0.08789122581892,  // slider
        3: 4096/360,  // pan
        4: 4096/360,  // tilt
        5: 4096/360,  // zoom
        6: 4096/360   // focus
    };
    
    return Math.round(units * conversionFactors[motorId]);
}

// Initialize motor input and display values
function initializeMotorValues(motorData) {
    motorData.forEach(motor => {
        const position = stepsToUnits(motor.position, motor.id);
        
        // Update input field
        const input = document.getElementById(`position_${motor.id}`);
        if (input) {
            input.value = position;
        }
        
        // Update display value
        const display = document.querySelector(`.position-value[data-motor-id="${motor.id}"]`);
        if (display) {
            display.textContent = position;
        }
    });
}
