import { TrackingHandler } from './tracking.js';

export class PointHandler {
    constructor() {
        this.focusPoints = [];
        this.currentPointId = null;
        this.updateCallback = null;
        this.trackingHandler = new TrackingHandler();
    }

    setUpdateCallback(callback) {
        this.updateCallback = callback;
    }

    async loadPoints() {
        try {
            const response = await fetch('/focus/points');
            this.focusPoints = await response.json();
            this.notifyUpdate();
        } catch (error) {
            console.error('Error loading focus points:', error);
        }
    }

    async selectPoint(pointId) {
        if (pointId === undefined || pointId === null) {
            console.error('Invalid point ID');
            return;
        }

        try {
            if (this.currentPointId === pointId) {
                // Stop tracking current point
                await this.trackingHandler.stopTracking();
                this.currentPointId = null;
            } else {
                // Start tracking new point
                const point = this.focusPoints.find(p => p.id === pointId);
                if (!point) throw new Error('Point not found');

                if (this.trackingHandler.isPointTracking()) {
                    await this.trackingHandler.stopTracking();
                }

                await this.trackingHandler.startTracking(point);
                this.currentPointId = pointId;
            }
            this.notifyUpdate();
        } catch (error) {
            console.error('Error:', error);
            throw error;
        }
    }

    async deletePoint(pointId) {
        try {
            // If deleting currently tracked point, stop tracking first
            if (this.trackingHandler.isPointTracking() && this.currentPointId === pointId) {
                await this.trackingHandler.stopTracking();
                this.currentPointId = null;
            }

            const response = await fetch(`/focus/point/${pointId}`, { 
                method: 'DELETE'
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to delete point');
            }

            await this.loadPoints();
            if (this.currentPointId === pointId) {
                this.currentPointId = null;
            }
            this.notifyUpdate();
        } catch (error) {
            console.error('Error:', error);
            throw error;
        }
    }

    async updatePointColor(pointId, color) {
        const point = this.focusPoints.find(p => p.id === pointId);
        if (point) {
            point.color = color;
            try {
                const response = await fetch(`/focus/point/${pointId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(point)
                });
                if (!response.ok) throw new Error('Failed to update point color');
                this.notifyUpdate();
            } catch (error) {
                console.error('Error updating point color:', error);
                throw error;
            }
        }
    }

    getPoints() {
        return this.focusPoints;
    }

    getCurrentPointId() {
        return this.currentPointId;
    }

    isPointTracking() {
        return this.trackingHandler.isPointTracking();
    }

    notifyUpdate() {
        if (this.updateCallback) {
            this.updateCallback({
                points: this.focusPoints,
                currentPointId: this.currentPointId,
                isTracking: this.trackingHandler.isPointTracking()
            });
        }
    }
}
