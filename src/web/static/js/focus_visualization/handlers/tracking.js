export class TrackingHandler {
    constructor() {
        this.isTrackingActive = false;
        this.currentPointId = null;
        this.updateCallback = null;
        console.log("TrackingHandler initialized");
        
        // Start polling for tracking state
        this.startPolling();
    }

    setUpdateCallback(callback) {
        console.log("Setting tracking update callback");
        this.updateCallback = callback;
    }

    isTracking() {
        return this.isTrackingActive;
    }

    async setTracking(enabled) {
        console.log("Setting tracking state:", enabled);
        if (enabled === this.isTrackingActive) {
            return; // Already in desired state
        }
        
        if (enabled) {
            // Only try to start tracking if we have a current point
            if (this.currentPointId !== null) {
                return await this.startTracking({ id: this.currentPointId });
            }
            return false;
        } else {
            return await this.stopTracking();
        }
    }

    getCurrentPointId() {
        return this.currentPointId;
    }

    async checkTrackingState() {
        try {
            const response = await fetch('/focus/status');
            const status = await response.json();
            
            const wasTracking = this.isTrackingActive;
            const previousPointId = this.currentPointId;
            
            this.isTrackingActive = status.tracking_active;
            this.currentPointId = status.current_point_id;
            
            // Call update callback if state changed
            if (this.updateCallback && 
                (wasTracking !== this.isTrackingActive || 
                previousPointId !== this.currentPointId)) {
                console.log("Tracking state changed:", 
                    {tracking: this.isTrackingActive, pointId: this.currentPointId});
                this.updateCallback(this.isTrackingActive);
            }
        } catch (error) {
            console.error("Error checking tracking state:", error);
        }
    }

    startPolling() {
        // Poll every 100ms for state changes
        setInterval(() => this.checkTrackingState(), 100);
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
                // State will be updated by polling
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
                // State will be updated by polling
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
        
        // Start tracking new point (backend handles stopping previous tracking)
        const success = await this.startTracking(point);
        
        // State will be updated by polling
        return success;
    }
}
