// Motor status and filter data update handling with polling

// Polling configuration
const POLL_INTERVAL = 50;   // 50ms = 20Hz für flüssigere Updates
const MIN_UPDATE_INTERVAL = 50;  // Minimale Zeit zwischen Updates reduziert
let pollTimer = null;
let lastUpdateTime = 0;
let updatePending = false;

const updateValues = (element, newValue, animate = true) => {
    if (element && element.textContent !== newValue) {
        if (animate) {
            element.classList.remove('value-updated');
            void element.offsetWidth; // Force reflow
            element.classList.add('value-updated');
        }
        element.textContent = newValue;
    }
};

const formatPidValues = (pid, type) => {
    if (type === 'position') {
        return `P: ${pid.p}, I: ${pid.i}, D: ${pid.d}`;
    } else {
        return `P: ${pid.p}, I: ${pid.i}`;
    }
};

const updateFilterStatus = (motorId, data) => {
    // Update each filter status value
    const metrics = [
        'prediction-time', 
        'estimated-position', 
        'estimated-velocity', 
        'prediction-error', 
        'filter-uncertainty'
    ];

    metrics.forEach(metric => {
        const element = document.querySelector(`.${metric}-value[data-motor-id="${motorId}"]`);
        if (element) {
            let value = data[metric.replace(/-/g, '_')];
            
            // Format values
            if (metric === 'prediction-time') {
                value = value.toFixed(3); // 3 decimal places for ms
            } else {
                value = value.toFixed(2); // 2 decimal places for other metrics
            }
            
            // Add warning/error classes for prediction error
            if (metric === 'prediction-error') {
                const maxError = 10; // From settings
                element.classList.remove('warning', 'error');
                if (value > maxError) {
                    element.classList.add('error');
                } else if (value > maxError * 0.7) {
                    element.classList.add('warning');
                }
            }

            updateValues(element, value);
        }
    });

    // Update PID values
    if (data.position_pid) {
        const posPidElement = document.querySelector(`.position-pid[data-motor-id="${motorId}"] span:last-child`);
        updateValues(posPidElement, formatPidValues(data.position_pid, 'position'));
    }

    if (data.velocity_pid) {
        const velPidElement = document.querySelector(`.velocity-pid[data-motor-id="${motorId}"] span:last-child`);
        updateValues(velPidElement, formatPidValues(data.velocity_pid, 'velocity'));
    }
};

const updateAllMotorStatus = async () => {
    // Prüfe ob Update zu früh
    const now = Date.now();
    if (now - lastUpdateTime < MIN_UPDATE_INTERVAL) {
        if (!updatePending) {
            updatePending = true;
            setTimeout(updateAllMotorStatus, MIN_UPDATE_INTERVAL);
        }
        return;
    }
    
    updatePending = false;
    lastUpdateTime = now;
    
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 2000);  // 2 Sekunden Timeout
        
        const response = await fetch('/motor/status', {
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (!response.ok) {
            throw new Error('Failed to fetch motor status');
        }
        
        const motors = await response.json();
        motors.forEach(motor => {
            if ([2, 3, 4].includes(motor.id)) {
                try {
                    updateFilterStatus(motor.id, {
                        prediction_time: motor.prediction_time || 0,
                        estimated_position: motor.estimated_position || 0,
                        estimated_velocity: motor.estimated_velocity || 0,
                        prediction_error: motor.prediction_error || 0,
                        filter_uncertainty: motor.filter_uncertainty || 0,
                        position_pid: motor.position_pid || { p: 0, i: 0, d: 0 },
                        velocity_pid: motor.velocity_pid || { p: 0, i: 0 }
                    });
                } catch (updateError) {
                    console.warn(`Error updating motor ${motor.id}:`, updateError);
                }
            }
        });
    } catch (error) {
        if (error.name === 'AbortError') {
            console.warn('Status update timed out');
        } else {
            console.error('Error updating motor status:', error);
        }
        // Reduziere Update-Frequenz bei Fehlern
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
};

// Start polling when page loads
document.addEventListener('DOMContentLoaded', () => {
    // Start immediate polling
    pollTimer = setInterval(updateAllMotorStatus, POLL_INTERVAL);
    
    // Initial update
    updateAllMotorStatus();
});

// Clean up when page unloads
window.addEventListener('beforeunload', () => {
    if (pollTimer) {
        clearInterval(pollTimer);
    }
});
