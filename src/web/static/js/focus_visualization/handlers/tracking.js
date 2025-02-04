export class TrackingHandler {
    constructor() {
        this.isTracking = false;
    }

    async startTracking(point) {
        try {
            const response = await fetch('/focus/start_tracking', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    x: point.x,
                    y: point.y,
                    z: point.z
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to start tracking');
            }

            this.isTracking = true;
        } catch (error) {
            console.error('Error starting tracking:', error);
            throw error;
        }
    }

    async stopTracking() {
        try {
            const response = await fetch('/focus/stop_tracking', { method: 'POST' });
            if (!response.ok) {
                throw new Error('Failed to stop tracking');
            }
            this.isTracking = false;
        } catch (error) {
            console.error('Error stopping tracking:', error);
            throw error;
        }
    }

    async switchTracking(point) {
        if (this.isTracking) {
            await this.stopTracking();
            return false;
        } else {
            await this.startTracking(point);
            return true;
        }
    }

    isPointTracking() {
        return this.isTracking;
    }
}
