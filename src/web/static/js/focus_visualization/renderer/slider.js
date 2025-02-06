export class SliderRenderer {
    constructor(canvasManager) {
        this.canvasManager = canvasManager;
    }

    draw(position, panAngle, tiltAngle) {
        const ctx = this.canvasManager.getContext();
        const pos = this.canvasManager.worldToScreen(0, position);
        
        // Scale dot size proportionally with zoom
        const dotRadius = Math.max(20, 20 * this.canvasManager.zoomLevel);
        
        // Draw slider dot
        ctx.beginPath();
        ctx.arc(pos.x, pos.y, dotRadius, 0, Math.PI * 2);
        ctx.fillStyle = 'red';
        ctx.fill();
        
        // Draw tilt value
        const fontSize = Math.max(16, Math.floor(12 * this.canvasManager.zoomLevel));
        ctx.fillStyle = 'white';
        ctx.font = `${fontSize}px Arial`;
        ctx.textAlign = 'center';
        ctx.fillText(`${(tiltAngle - 180).toFixed(1)}°`, pos.x, pos.y + fontSize/3);
        
        // Draw pan direction arrow with gradient
        this.drawPanArrow(ctx, pos, panAngle, dotRadius);
    }

    drawPanArrow(ctx, pos, panAngle, dotRadius) {
        // Scale arrow length with zoom, but keep base length shorter
        const arrowLength = Math.max(60, 60 * this.canvasManager.zoomLevel);
        const angle = (-panAngle * Math.PI) / 180 + Math.PI/2; // Invert pan direction and rotate 90 degrees
        
        // Start from edge of red dot
        const startX = pos.x + dotRadius * Math.cos(angle);
        const startY = pos.y + dotRadius * Math.sin(angle);
        const endX = pos.x + (dotRadius + arrowLength) * Math.cos(angle);
        const endY = pos.y + (dotRadius + arrowLength) * Math.sin(angle);
        
        // Create gradient for arrow
        const gradient = ctx.createLinearGradient(startX, startY, endX, endY);
        gradient.addColorStop(0, 'red');
        gradient.addColorStop(1, 'yellow');
        
        // Draw arrow line with gradient
        ctx.beginPath();
        ctx.moveTo(startX, startY);
        ctx.lineTo(endX, endY);
        ctx.strokeStyle = gradient;
        ctx.lineWidth = Math.max(4, 4 * this.canvasManager.zoomLevel);
        ctx.stroke();
        
        // Draw arrow head with yellow color
        const headLength = Math.max(25, 25 * this.canvasManager.zoomLevel);
        const headAngle = Math.PI / 6;
        
        ctx.beginPath();
        ctx.moveTo(endX, endY);
        ctx.lineTo(
            endX - headLength * Math.cos(angle - headAngle),
            endY - headLength * Math.sin(angle - headAngle)
        );
        ctx.moveTo(endX, endY);
        ctx.lineTo(
            endX - headLength * Math.cos(angle + headAngle),
            endY - headLength * Math.sin(angle + headAngle)
        );
        ctx.strokeStyle = 'yellow';
        ctx.stroke();
    }
}
