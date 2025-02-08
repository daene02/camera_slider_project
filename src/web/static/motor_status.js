// Motor status and filter data update handling with polling

// Polling und Update-Konfiguration
const POLL_INTERVAL = 20; // 20ms = 50Hz für sehr flüssige Anzeige
const DISPLAY_UPDATE_INTERVAL = 50; // 50ms = 20Hz für UI-Updates
const UPDATE_THRESHOLD = 0.1; // Nur Änderungen > 0.1 anzeigen
const ANIMATION_DURATION = 500; // Animation duration in ms

// Monitoring thresholds (from settings.py)
const MONITORING_THRESHOLDS = {
    temperature: { warning: 55, error: 65 },
    voltage: { warning: 11.5, error: 11.0 },
   // current: { warning: 800000, error: 1000000 },
   // load: { warning: 7000000, error: 8500000 }
};

let pollTimer = null;
let displayTimer = null;
let lastUpdateTime = 0;

// Zwischenspeicher für aktuelle Werte
let currentValues = {};
let lastPositions = {};

const updateValues = (element, newValue, animate = true) => {
    if (!element) return;

    const currentValue = parseFloat(element.textContent);
    const newValueFloat = parseFloat(newValue);
    
    // Prüfe ob Aktualisierung notwendig
    const timeSinceLastUpdate = Date.now() - lastUpdateTime;
    const shouldUpdate = isNaN(currentValue) || isNaN(newValueFloat) ||
                        Math.abs(currentValue - newValueFloat) > UPDATE_THRESHOLD;
    
    if (shouldUpdate && timeSinceLastUpdate >= DISPLAY_UPDATE_INTERVAL) {
        if (animate) {
            element.style.transition = `color ${ANIMATION_DURATION}ms ease-out`;
            element.style.color = '#4a9eff';  // Highlight-Farbe
            element.textContent = newValue;
            
            // Reset color after animation
            setTimeout(() => {
                element.style.color = '';
                element.style.transition = '';
            }, ANIMATION_DURATION);
        } else {
            element.textContent = newValue;
        }
        
        lastUpdateTime = Date.now();
    }
};

const checkThreshold = (value, thresholds, motorId, type, message) => {
    if (!thresholds) return;
    
    const prevState = currentValues[motorId]?.['state_' + type] || 'normal';
    let newState = 'normal';
    
    if (value >= thresholds.error) {
        newState = 'error';
        if (prevState !== 'error') {
            notificationManager.show(
                `${message} (${value})`,
                NOTIFICATION_TYPES.ERROR,
                motorId
            );
        }
    } else if (value >= thresholds.warning) {
        newState = 'warning';
        if (prevState !== 'warning' && prevState !== 'error') {
            notificationManager.show(
                `${message} (${value})`,
                NOTIFICATION_TYPES.WARNING,
                motorId
            );
        }
    }
    
    if (currentValues[motorId]) {
        currentValues[motorId]['state_' + type] = newState;
    }
    
    return newState;
};

const updateStatus = (element, value, thresholds, motorId, type, message) => {
    if (!element) return;
    
    const state = checkThreshold(value, thresholds, motorId, type, message);
    
    element.classList.remove('warning', 'error');
    if (state === 'error') {
        element.classList.add('error');
    } else if (state === 'warning') {
        element.classList.add('warning');
    }
    
    updateValues(element, value);
};

const updateDisplay = () => {
    Object.entries(currentValues).forEach(([motorId, data]) => {
        if (data) {
            // Update motor values with monitoring
            updateStatus(
                document.querySelector(`.temperature-value[data-motor-id="${motorId}"]`),
                data.temperature,
                MONITORING_THRESHOLDS.temperature,
                motorId,
                'temperature',
                'High temperature detected'
            );
            
            updateStatus(
                document.querySelector(`.voltage-value[data-motor-id="${motorId}"]`),
                data.voltage,
                MONITORING_THRESHOLDS.voltage,
                motorId,
                'voltage',
                'Low voltage warning'
            );
            
            updateStatus(
                document.querySelector(`.current-value[data-motor-id="${motorId}"]`),
                data.current,
                MONITORING_THRESHOLDS.current,
                motorId,
                'current',
                'High current detected'
            );
            
            updateStatus(
                document.querySelector(`.load-value[data-motor-id="${motorId}"]`),
                data.load,
                MONITORING_THRESHOLDS.load,
                motorId,
                'load',
                'High load warning'
            );
            
            // Update filter status
            updateFilterStatus(motorId, data);
        }
    });
};

const formatPidValues = (pid, type) => {
    if (type === 'position') {
        return `P: ${pid.p}, I: ${pid.i}, D: ${pid.d}`;
    } else {
        return `P: ${pid.p}, I: ${pid.i}`;
    }
};

const updateFilterStatus = (motorId, data) => {
    // Update estimated values
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
    try {
        const response = await fetch('/motor/status');
        if (!response.ok) throw new Error('Failed to fetch motor status');
        
        const motors = await response.json();
        motors.forEach(motor => {
            if ([2, 3, 4].includes(motor.id)) {
                // Convert values to user units (mm or degrees)
                const position = stepsToUnits(motor.position, motor.id);
                const estimatedPosition = stepsToUnits(motor.estimated_position || 0, motor.id);
                
                // Calculate actual velocity from position change
                let actualVelocity = 0;
                if (lastPositions[motor.id] !== undefined) {
                    const dt = POLL_INTERVAL / 1000; // Convert ms to seconds
                    actualVelocity = (position - lastPositions[motor.id]) / dt;
                }
                lastPositions[motor.id] = position;
                
                // Store all motor values
                currentValues[motor.id] = {
                    position,
                    estimatedPosition,
                    velocity: actualVelocity,
                    temperature: motor.temperature,
                    voltage: motor.voltage,
                    current: motor.current,
                    load: motor.load,
                    prediction_time: motor.prediction_time || 0,
                    estimated_position: estimatedPosition,
                    estimated_velocity: motor.estimated_velocity || 0,
                    prediction_error: motor.prediction_error || 0,
                    filter_uncertainty: motor.filter_uncertainty || 0,
                    position_pid: motor.position_pid || { p: 0, i: 0, d: 0 },
                    velocity_pid: motor.velocity_pid || { p: 0, i: 0 }
                };
                
                // Update charts
                updateMotorChart(motor.id, {
                    position,
                    estimated_position: estimatedPosition,
                    velocity: actualVelocity
                });
            }
        });
    } catch (error) {
        console.error('Error updating motor status:', error);
    }
};

// Initialize everything when page loads
document.addEventListener('DOMContentLoaded', () => {
    // Start data polling (high frequency)
    pollTimer = setInterval(updateAllMotorStatus, POLL_INTERVAL);
    
    // Start display updates (lower frequency)
    displayTimer = setInterval(updateDisplay, DISPLAY_UPDATE_INTERVAL);
    
    // Initial updates
    updateAllMotorStatus();
    updateDisplay();
});

// Clean up when page unloads
window.addEventListener('beforeunload', () => {
    if (pollTimer) clearInterval(pollTimer);
    if (displayTimer) clearInterval(displayTimer);
    currentValues = {};
    lastPositions = {};
});
