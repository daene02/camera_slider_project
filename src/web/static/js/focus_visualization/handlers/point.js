export class PointHandler {
    constructor() {
        this.points = [];
        this.updateCallback = null;
        this.isLoading = false;
        console.log("PointHandler initialized");
    }

    setUpdateCallback(callback) {
        console.log("Setting update callback");
        this.updateCallback = callback;
    }

    async loadPoints() {
        console.log("=== loadPoints start ===");
        if (this.isLoading) {
            console.log("Already loading points, skipping");
            return;
        }
        
        this.isLoading = true;
        console.log("Loading focus points...");
        
        try {
            const response = await fetch('/focus/points');
            console.log("Response status:", response.status);
            
            const text = await response.text();
            console.log("Raw response:", text);
            
            let data;
            try {
                data = JSON.parse(text);
                console.log("Parsed data:", data);
            } catch (e) {
                console.error("Failed to parse JSON:", e);
                throw e;
            }
            
            // Reset points array
            this.points = [];
            
            if (Array.isArray(data)) {
                console.log(`Processing ${data.length} points`);
                this.points = data.map((point, index) => {
                    console.log(`Processing point ${index}:`, point);
                    return {
                        id: point.id,
                        name: point.name || `Point ${point.id}`,
                        x: parseFloat(point.x),
                        y: parseFloat(point.y),
                        z: parseFloat(point.z),
                        color: point.color || '#4a9eff'
                    };
                });
                console.log("Final processed points:", this.points);
            } else {
                console.error("Received non-array data:", data);
            }
            
        } catch (error) {
            console.error('Error loading points:', error);
            this.points = [];
        } finally {
            this.isLoading = false;
            console.log("Loading complete, points count:", this.points.length);
            
            if (this.updateCallback) {
                console.log("Calling update callback");
                this.updateCallback();
            } else {
                console.log("No update callback registered");
            }
        }
        console.log("=== loadPoints end ===");
    }

    getPoints() {
        console.log("getPoints called, returning:", this.points);
        return this.points;
    }

    async addPoint(point) {
        console.log("Adding point:", point);
        try {
            const response = await fetch('/focus/save_point', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(point)
            });

            const text = await response.text();
            console.log("Add point response text:", text);
            
            const result = JSON.parse(text);
            console.log("Add point parsed response:", result);
            
            if (result.success && result.point) {
                this.points.push(result.point);
                console.log("Updated points array:", this.points);
                
                if (this.updateCallback) {
                    console.log("Calling update callback after add");
                    this.updateCallback();
                }
                return true;
            }
            return false;
        } catch (error) {
            console.error('Error adding point:', error);
            return false;
        }
    }

    async updatePoint(pointId, updates) {
        console.log("Updating point:", pointId, updates);
        try {
            const response = await fetch(`/focus/point/${pointId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(updates)
            });

            const text = await response.text();
            console.log("Update point response text:", text);
            
            const updatedPoint = JSON.parse(text);
            console.log("Update point parsed response:", updatedPoint);
            
            const index = this.points.findIndex(p => p.id === pointId);
            if (index !== -1) {
                this.points[index] = updatedPoint;
                console.log("Updated points array:", this.points);
                
                if (this.updateCallback) {
                    console.log("Calling update callback after update");
                    this.updateCallback();
                }
                return true;
            }
            return false;
        } catch (error) {
            console.error('Error updating point:', error);
            return false;
        }
    }

    async removePoint(pointId) {
        console.log("Removing point:", pointId);
        try {
            const response = await fetch(`/focus/point/${pointId}`, {
                method: 'DELETE'
            });

            const text = await response.text();
            console.log("Remove point response text:", text);
            
            const result = JSON.parse(text);
            console.log("Remove point parsed response:", result);
            
            if (result.success) {
                this.points = this.points.filter(p => p.id !== pointId);
                console.log("Updated points array after remove:", this.points);
                
                if (this.updateCallback) {
                    console.log("Calling update callback after remove");
                    this.updateCallback();
                }
                return true;
            }
            return false;
        } catch (error) {
            console.error('Error removing point:', error);
            return false;
        }
    }
}
