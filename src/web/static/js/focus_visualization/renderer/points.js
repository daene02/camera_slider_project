export class PointsRenderer {
    constructor(canvasManager) {
        this.canvasManager = canvasManager;
        this.blinkState = true;
        this.lastBlinkTime = 0;
        this.BLINK_INTERVAL = 500; // milliseconds
    }

    updateBlink() {
        const currentTime = Date.now();
        if (currentTime - this.lastBlinkTime > this.BLINK_INTERVAL) {
            this.blinkState = !this.blinkState;
            this.lastBlinkTime = currentTime;
        }
    }

    draw(points, currentPointId, isTracking) {
        this.updateBlink();
        points.forEach(point => {
            const isActive = isTracking && point.id === currentPointId;
            this.drawPoint(point, isActive);
        });
    }

    drawPoint(point, isActive) {
        // Don't draw active point when it should be hidden during blink
        if (isActive && !this.blinkState) return;

        const ctx = this.canvasManager.getContext();
        const pos = this.canvasManager.worldToScreen(point.x, point.y);
        
        // Scale point size with zoom but keep it relatively small
        const radius = Math.max(6, 6 * this.canvasManager.zoomLevel);
        
        // Draw point with shadow for depth
        ctx.shadowColor = 'rgba(0, 0, 0, 0.5)';
        ctx.shadowBlur = radius / 2;
        ctx.beginPath();
        ctx.arc(pos.x, pos.y, radius, 0, Math.PI * 2);
        ctx.fillStyle = isActive ? '#00ff00' : point.color || '#4a9eff';
        ctx.fill();
        ctx.shadowColor = 'transparent';
        
        // Draw label
        const fontSize = Math.max(10, Math.floor(10 * this.canvasManager.zoomLevel));
        ctx.fillStyle = 'white';
        ctx.font = `${fontSize}px Arial`;
        ctx.textAlign = 'left';
        
        // Position text with proper spacing that scales with zoom
        const textOffset = radius + 4 * this.canvasManager.zoomLevel;
        ctx.fillText(point.name, pos.x + textOffset, pos.y + fontSize/3);
    }

    // Check if point coordinates are within visible range
    isPointVisible(point) {
        const pos = this.canvasManager.worldToScreen(point.x, point.y);
        const { width, height } = this.canvasManager.getDimensions();
        
        return pos.x >= 0 && pos.x <= width && pos.y >= 0 && pos.y <= height;
    }
}
