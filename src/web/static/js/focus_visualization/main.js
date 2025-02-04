import { CanvasManager } from './canvas.js';
import { AxisRenderer } from './renderer/axis.js';
import { SliderRenderer } from './renderer/slider.js';
import { PointsRenderer } from './renderer/points.js';
import { MotorPositionHandler } from './handlers/motor.js';
import { PointHandler } from './handlers/point.js';

export class FocusVisualization {
    constructor(canvasId) {
        // Initialize canvas and renderers
        this.canvasManager = new CanvasManager(canvasId);
        this.axisRenderer = new AxisRenderer(this.canvasManager);
        this.sliderRenderer = new SliderRenderer(this.canvasManager);
        this.pointsRenderer = new PointsRenderer(this.canvasManager);

        // Initialize handlers
        this.motorHandler = new MotorPositionHandler();
        this.pointHandler = new PointHandler();

        // Setup callbacks
        this.setupCallbacks();
        
        // Start animation and polling
        this.startAnimation();
        this.motorHandler.startPolling();
        this.pointHandler.loadPoints();
    }

    setupCallbacks() {
        // Motor position updates
        this.motorHandler.setUpdateCallback(() => {
            this.render();
        });

        // Point updates
        this.pointHandler.setUpdateCallback(() => {
            this.render();
            this.updatePointList();
        });

        // Setup window resize handler
        window.addEventListener('resize', () => {
            this.render();
        });
    }

    render() {
        this.canvasManager.clear();
        
        // Draw axis
        this.axisRenderer.draw();
        
        // Draw slider and motors
        const { sliderPosition, panAngle, tiltAngle } = this.motorHandler.getCurrentPositions();
        this.sliderRenderer.draw(sliderPosition, panAngle, tiltAngle);
        
        // Draw points
        const points = this.pointHandler.getPoints();
        const currentPointId = this.pointHandler.getCurrentPointId();
        const isTracking = this.pointHandler.isPointTracking();
        this.pointsRenderer.draw(points, currentPointId, isTracking);
    }

    startAnimation() {
        const animate = () => {
            this.render();
            this.animationFrame = requestAnimationFrame(animate);
        };
        animate();
    }

    stopAnimation() {
        if (this.animationFrame) {
            cancelAnimationFrame(this.animationFrame);
        }
    }

    updatePointList() {
        const pointList = document.getElementById('pointList');
        if (!pointList) return;

        const points = this.pointHandler.getPoints();
        const currentPointId = this.pointHandler.getCurrentPointId();
        const isTracking = this.pointHandler.isPointTracking();

        pointList.innerHTML = points.map(point => `
            <div class="point-item ${point.id === currentPointId ? 'active' : ''}"
                 title="${point.id === currentPointId && isTracking ? 'Currently tracking this point' : 'Click to track this point'}">
                <div class="point-content" onclick="focusVis.handlePointClick(${point.id})">
                    <div class="point-name">${point.name}</div>
                    <div class="point-coordinates">
                        Position: ${Math.round(point.y)}mm, Offset: ${point.x > 0 ? 'Right' : 'Left'} ${Math.abs(point.x)}
                    </div>
                </div>
                <div class="point-controls">
                    <input type="color" 
                           value="${point.color || '#4a9eff'}" 
                           onchange="focusVis.handleColorChange(${point.id}, this.value)">
                    <button onclick="event.stopPropagation(); focusVis.handlePointDelete(${point.id})" 
                            class="btn btn-sm btn-danger">×</button>
                </div>
            </div>
        `).join('');
    }

    // Event handlers exposed to HTML
    async handlePointClick(pointId) {
        try {
            await this.pointHandler.selectPoint(pointId);
        } catch (error) {
            alert(error.message || 'Failed to select point');
        }
    }

    async handlePointDelete(pointId) {
        try {
            await this.pointHandler.deletePoint(pointId);
        } catch (error) {
            alert(error.message || 'Failed to delete point');
        }
    }

    async handleColorChange(pointId, color) {
        try {
            await this.pointHandler.updatePointColor(pointId, color);
        } catch (error) {
            alert(error.message || 'Failed to update point color');
        }
    }

    cleanup() {
        this.stopAnimation();
        this.motorHandler.stopPolling();
    }
}

// Initialize visualization when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.focusVis = new FocusVisualization('focusVisualization');
});
