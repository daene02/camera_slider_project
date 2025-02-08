// Motor position and velocity charting with Chart.js

const CHART_CONFIG = {
    type: 'line',
    options: {
        animation: false,
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'top',
                labels: {
                    color: '#ddd',
                    font: {
                        size: 11
                    }
                }
            },
            title: { display: false }
        },
        scales: {
            x: {
                type: 'time',
                time: {
                    unit: 'second',
                    displayFormats: {
                        second: 'HH:mm:ss'
                    }
                },
                grid: {
                    color: '#333',
                    borderColor: '#444'
                },
                ticks: {
                    color: '#bbb',
                    font: {
                        size: 10
                    }
                },
                title: {
                    display: true,
                    text: 'Time',
                    color: '#ddd',
                    font: {
                        size: 12
                    }
                }
            },
            y: {
                type: 'linear',
                display: true,
                grid: {
                    color: '#333',
                    borderColor: '#444'
                },
                ticks: {
                    color: '#bbb',
                    font: {
                        size: 10
                    }
                },
                title: {
                    display: true,
                    text: 'Value',
                    color: '#ddd',
                    font: {
                        size: 12
                    }
                }
            }
        }
    }
};

class MotorChart {
    constructor(motorId, maxDataPoints = 100) {
        this.motorId = motorId;
        this.maxDataPoints = maxDataPoints;
        this.chart = null;
        this.datasets = {
            position: [],
            estimatedPosition: [],
            velocity: []
        };
        this.init();
    }

    init() {
        const canvas = document.getElementById(`motor${this.motorId}_chart`);
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        this.chart = new Chart(ctx, {
            ...CHART_CONFIG,
            data: {
                datasets: [
                    {
                        label: 'Position',
                        data: this.datasets.position,
                        borderColor: '#4a9eff',
                        tension: 0.2
                    },
                    {
                        label: 'Estimated Position',
                        data: this.datasets.estimatedPosition,
                        borderColor: '#44ff44',
                        borderDash: [5, 5],
                        tension: 0.2
                    },
                    {
                        label: 'Velocity',
                        data: this.datasets.velocity,
                        borderColor: '#ff9944',
                        yAxisID: 'velocity',
                        tension: 0.2
                    }
                ]
            },
            options: {
                ...CHART_CONFIG.options,
                scales: {
                    ...CHART_CONFIG.options.scales,
                    velocity: {
                        type: 'linear',
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Velocity'
                        },
                        grid: {
                            drawOnChartArea: false
                        }
                    }
                }
            }
        });
    }

    update(position, estimatedPosition, velocity) {
        const now = new Date();
        
        // Add new data points
        this.datasets.position.push({ x: now, y: position });
        this.datasets.estimatedPosition.push({ x: now, y: estimatedPosition });
        this.datasets.velocity.push({ x: now, y: velocity });
        
        // Remove old data points
        if (this.datasets.position.length > this.maxDataPoints) {
            this.datasets.position.shift();
            this.datasets.estimatedPosition.shift();
            this.datasets.velocity.shift();
        }
        
        // Update chart
        if (this.chart) {
            this.chart.update('quiet');
        }
    }
}

// Initialize charts for motors that need them
const motorCharts = {};

document.addEventListener('DOMContentLoaded', () => {
    // Initialize charts for slider, pan, and tilt motors
    [2, 3, 4].forEach(motorId => {
        motorCharts[motorId] = new MotorChart(motorId);
    });
});

// Update charts with new data
function updateMotorChart(motorId, data) {
    const chart = motorCharts[motorId];
    if (chart) {
        chart.update(
            data.position || 0,
            data.estimated_position || 0,
            data.estimated_velocity || 0
        );
    }
}
