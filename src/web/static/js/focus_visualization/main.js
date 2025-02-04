import { CanvasManager } from './canvas.js';
import { SliderRenderer } from './renderer/slider.js';
import { AxisRenderer } from './renderer/axis.js';
import { PointsRenderer } from './renderer/points.js';
import { MotorPositionHandler } from './handlers/motor.js';
import { TrackingHandler } from './handlers/tracking.js';
import { PointHandler } from './handlers/point.js';

export class FocusVisualization {
    constructor(canvasId) {
        console.log("\n=== Initializing FocusVisualization ===");
        
        // Initialize all components
        // Initialize components
        this.canvasManager = new CanvasManager(canvasId);
        this.sliderRenderer = new SliderRenderer(this.canvasManager);
        this.axisRenderer = new AxisRenderer(this.canvasManager);
        this.motorHandler = new MotorPositionHandler();
        this.trackingHandler = new TrackingHandler();
        this.pointHandler = new PointHandler();
        
        // Connect axis renderer to canvas manager
        this.canvasManager.setAxisRenderer(this.axisRenderer);
        
        // Initialize points renderer with all handlers
        this.pointsRenderer = new PointsRenderer(
            this.canvasManager,
            this.motorHandler
        );
        
        // Connect tracking handler to points renderer
        this.pointsRenderer.setTrackingHandler(this.trackingHandler);
        
        // Set up draw callback
        this.canvasManager.onDraw = () => this.draw();
        
        // Setup motor position updates
        this.motorHandler.setUpdateCallback(positions => {
            if (positions && positions.sliderPosition !== undefined) {
                this.canvasManager.setCurrentPosition(0, positions.sliderPosition);
            }
            this.draw();
        });
        
        // Setup point updates
        this.pointHandler.setUpdateCallback(() => {
            const points = this.pointHandler.getPoints();
            this.canvasManager.setPoints(points);
            this.draw();
        });
        
        // Handle point selections from tracking updates
        this.trackingHandler.setUpdateCallback(isTracking => {
            this.draw();
        });

        // Start motor position polling
        this.motorHandler.startPolling();
        
        // Initial points load
        this.loadPointsAndDraw();
    }
    
    async loadPointsAndDraw() {
        console.log("\n=== Initial Points Load ===");
        await this.pointHandler.loadPoints();
        const points = this.pointHandler.getPoints();
        this.canvasManager.setPoints(points);
        console.log("Loaded points:", points);
        this.draw();
    }
    
    draw() {
        try {
            // Clear canvas
            this.canvasManager.clear();
            
            // Get current state
            const positions = this.motorHandler.getCurrentPositions();
            const points = this.pointHandler.getPoints();
            const currentPointId = this.trackingHandler.getCurrentPointId();
            const isTracking = this.trackingHandler.isTracking();
            
            // Draw layers in order (background to foreground)
            this.axisRenderer.draw();
            this.sliderRenderer.draw(
                positions ? positions.sliderPosition : 0,
                positions ? positions.panAngle : 0,
                positions ? positions.tiltAngle : 0
            );
            this.pointsRenderer.draw(points, currentPointId, isTracking);
            
            // Draw points list overlay last (always on top)
            this.canvasManager.drawPointsList(points, currentPointId);
            
        } catch (error) {
            console.error("Error in draw cycle:", error);
        }
    }
}
