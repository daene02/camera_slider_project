// Motor monitoring and initialization

class MotorMonitor {
    constructor() {
        this.thresholds = {
            temperature: { warning: 55, error: 65 },
            voltage: { warning: 11.5, error: 11.0 },
            current: { warning: 800, error: 1000 },
            load: { warning: 70000, error: 850000 }
        };
    }

    initialize(motorData) {
        // Initialize motor values
        initializeMotorValues(motorData);
        
        // Show startup notification
        notificationManager.show('Motor status monitoring active', 'info');
        
        // Check initial states
        this.checkMotorStates(motorData);
        
        // Start monitoring
        this.startMonitoring();
    }

    checkMotorStates(motors) {
        motors.forEach(motor => {
            this.checkMotorConditions(motor);
        });
    }

    checkMotorConditions(motor) {
        const checks = [
            {
                value: motor.temperature,
                thresholds: this.thresholds.temperature,
                name: 'temperature',
                unit: '°C',
                message: `High temperature detected`
            },
            {
                value: motor.voltage,
                thresholds: this.thresholds.voltage,
                name: 'voltage',
                unit: 'V',
                message: `Low voltage warning`,
                invert: true  // For voltage, lower is worse
            },
            {
                value: motor.current,
                thresholds: this.thresholds.current,
                name: 'current',
                unit: 'mA',
                message: `High current detected`
            },
            {
                value: motor.load,
                thresholds: this.thresholds.load,
                name: 'load',
                unit: '%',
                message: `High load warning`
            },
            {
                value: motor.prediction_error,
                thresholds: { warning: 7, error: 10 },
                name: 'prediction_error',
                unit: '',
                message: `High prediction error`,
                condition: motor.id in [2, 3, 4],  // Only for motors with Kalman filter
                visualElement: '.prediction-error'
            },
            {
                value: motor.filter_uncertainty,
                thresholds: { warning: 10, error: 20 },
                name: 'filter_uncertainty',
                unit: '',
                message: `High filter uncertainty`,
                condition: motor.id in [2, 3, 4],  // Only for motors with Kalman filter
                visualElement: '.filter-uncertainty'
            }
        ];

        checks.forEach(check => {
            const value = check.value;
            const compare = check.invert ? 
                (v, threshold) => v < threshold :
                (v, threshold) => v > threshold;

            // Skip check if condition is defined and false
            if (check.condition !== undefined && !check.condition) {
                return;
            }

            if (compare(value, check.thresholds.error)) {
                const formattedValue = value.toFixed(2);
                notificationManager.show(
                    `${check.message} (${formattedValue}${check.unit})`,
                    'error',
                    motor.id
                );

                // Add visual feedback if element selector is provided
                if (check.visualElement) {
                    const element = document.querySelector(`${check.visualElement}[data-motor-id="${motor.id}"]`);
                    if (element) {
                        element.classList.remove('warning');
                        element.classList.add('error');
                        
                        // Add glow effect for uncertainty
                        if (check.name === 'filter_uncertainty') {
                            element.style.textShadow = '0 0 10px rgba(255, 68, 68, 0.7)';
                        }
                    }
                }
            } else if (compare(value, check.thresholds.warning)) {
                const formattedValue = value.toFixed(2);
                notificationManager.show(
                    `${check.message} (${formattedValue}${check.unit})`,
                    'warning',
                    motor.id
                );

                // Add visual feedback if element selector is provided
                if (check.visualElement) {
                    const element = document.querySelector(`${check.visualElement}[data-motor-id="${motor.id}"]`);
                    if (element) {
                        element.classList.remove('error');
                        element.classList.add('warning');
                        
                        // Add softer glow effect for uncertainty
                        if (check.name === 'filter_uncertainty') {
                            element.style.textShadow = '0 0 8px rgba(255, 187, 0, 0.7)';
                        }
                    }
                }
            } else if (check.visualElement) {
                // Reset classes and effects when resolved
                const element = document.querySelector(`${check.visualElement}[data-motor-id="${motor.id}"]`);
                if (element) {
                    element.classList.remove('error', 'warning');
                    if (check.name === 'filter_uncertainty') {
                        element.style.textShadow = '';
                    }
                }
            }
        });
    }

    startMonitoring() {
        // Monitor motor states during runtime
        const CHECK_INTERVAL = 1000; // Check every second
        
        setInterval(() => {
            fetch('/motor/status')
                .then(response => response.json())
                .then(motors => {
                    this.checkMotorStates(motors);
                })
                .catch(error => {
                    console.error('Error monitoring motors:', error);
                    notificationManager.show(
                        'Motor monitoring error: ' + error.message,
                        'error'
                    );
                });
        }, CHECK_INTERVAL);
    }
}

// Create global motor monitor instance
window.motorMonitor = new MotorMonitor();
