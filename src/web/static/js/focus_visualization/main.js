import { CanvasManager } from './canvas.js';
import { SliderRenderer } from './renderer/slider.js';
import { AxisRenderer } from './renderer/axis.js';
import { PointsRenderer } from './renderer/points.js';
import { MotorPositionHandler } from './handlers/motor.js';
import { TrackingHandler } from './handlers/tracking.js';
import { PointHandler } from './handlers/point.js';
import { ProfileManager } from './profile_manager.js';

export class FocusVisualization {
    constructor(canvasId) {
        console.log("\n=== Initializing FocusVisualization ===");
        
        // Initialize all components
        this.canvasManager = new CanvasManager(canvasId);
        this.sliderRenderer = new SliderRenderer(this.canvasManager);
        this.axisRenderer = new AxisRenderer(this.canvasManager);
        this.motorHandler = new MotorPositionHandler();
        this.trackingHandler = new TrackingHandler();
        this.pointHandler = new PointHandler();
        this.profileManager = new ProfileManager();
        this.profileManager.setTrackingHandler(this.trackingHandler);
        
        // Initialize points renderer with all handlers
        this.pointsRenderer = new PointsRenderer(
            this.canvasManager,
            this.motorHandler
        );

        // Connect profile manager with points handler
        this.pointHandler.setUpdateCallback((points) => {
            this.profileManager.updatePoints(points);
            this.canvasManager.setPoints(points);
            this.draw();
        });
        
        // Connect tracking handler and points renderer
        this.pointsRenderer.setTrackingHandler(this.trackingHandler);
        
        // Connect components to canvas
        this.canvasManager.setAxisRenderer(this.axisRenderer);
        this.canvasManager.setTrackingHandler(this.trackingHandler);
        this.canvasManager.setPointsRenderer(this.pointsRenderer);
        
        // Setup tracking callback for UI updates
        this.trackingHandler.setUpdateCallback(isTracking => {
            console.log("Tracking state changed:", isTracking);
            this.draw();
        });
        
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
            this.profileManager.updatePoints(points);
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
        this.profileManager.updatePoints(points);
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
            
        } catch (error) {
            console.error("Error in draw cycle:", error);
        }
    }
}
