export class TrackingHandler {
    constructor() {
        this.isTrackingActive = false;
        this.currentPointId = null;
        this.updateCallback = null;
        console.log("TrackingHandler initialized");
    }

    setUpdateCallback(callback) {
        console.log("Setting tracking update callback");
        this.updateCallback = callback;
    }

    isTracking() {
        return this.isTrackingActive;
    }

    getCurrentPointId() {
        return this.currentPointId;
    }

    async startTracking(point) {
        console.log("\n=== Starting Tracking ===");
        console.log("Point:", point);
        
        try {
            const response = await fetch('/focus/start_tracking', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(point)
            });

            const result = await response.json();
            console.log("Start tracking response:", result);

            if (result.success) {
                this.isTrackingActive = true;
                this.currentPointId = point.id;
                
                if (this.updateCallback) {
                    console.log("Calling update callback - tracking started");
                    this.updateCallback(true);
                }
                
                return true;
            } else {
                console.error("Failed to start tracking:", result.error);
                return false;
            }
        } catch (error) {
            console.error("Error starting tracking:", error);
            return false;
        }
    }

    async stopTracking() {
        console.log("\n=== Stopping Tracking ===");
        
        try {
            const response = await fetch('/focus/stop_tracking', {
                method: 'POST'
            });

            const result = await response.json();
            console.log("Stop tracking response:", result);

            if (result.success) {
                this.isTrackingActive = false;
                this.currentPointId = null;
                
                if (this.updateCallback) {
                    console.log("Calling update callback - tracking stopped");
                    this.updateCallback(false);
                }
                
                return true;
            } else {
                console.error("Failed to stop tracking:", result.error);
                return false;
            }
        } catch (error) {
            console.error("Error stopping tracking:", error);
            return false;
        }
    }

    // Called when a point is selected/clicked
    async selectPoint(point) {
        console.log("\n=== Selecting Point ===");
        console.log("Point:", point);
        
        // If already tracking this point, do nothing
        if (this.currentPointId === point.id && this.isTrackingActive) {
            console.log("Already tracking this point");
            return true;
        }
        
        // If tracking a different point, stop current tracking
        if (this.isTrackingActive) {
            console.log("Stopping current tracking before switching points");
            await this.stopTracking();
        }
        
        // Start tracking new point
        return this.startTracking(point);
    }
}
