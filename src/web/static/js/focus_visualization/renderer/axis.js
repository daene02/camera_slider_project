import { SLIDER_MAX_MM } from '../constants.js';

export class AxisRenderer {
    constructor(canvasManager) {
        this.canvasManager = canvasManager;
    }

    draw() {
        const ctx = this.canvasManager.getContext();
        const start = this.canvasManager.worldToScreen(0, 0);
        const end = this.canvasManager.worldToScreen(0, SLIDER_MAX_MM);
        
        // Draw background for axis - width scales with zoom
        const axisWidth = Math.max(20, 20 * this.canvasManager.zoomLevel);
        ctx.beginPath();
        ctx.rect(start.x - axisWidth/2, end.y, axisWidth, start.y - end.y);
        ctx.fillStyle = '#000000';
        ctx.fill();

        // Draw ruler ticks and measurements
        // Use step size based on zoom level
        const step = this.canvasManager.zoomLevel >= 1.5 ? 50 : 
                    this.canvasManager.zoomLevel >= 1.0 ? 100 :
                    200;
        
        // Draw ticks from 0 to SLIDER_MAX_MM
        for (let mm = 0; mm <= SLIDER_MAX_MM; mm += step) {
            const pos = this.canvasManager.worldToScreen(0, mm);
            
            // Scale tick size with zoom
            const tickSize = Math.max(5, 5 * this.canvasManager.zoomLevel);
            
            // Left tick
            ctx.beginPath();
            ctx.moveTo(pos.x - tickSize - axisWidth/2, pos.y);
            ctx.lineTo(pos.x - axisWidth/2, pos.y);
            ctx.strokeStyle = 'white';
            ctx.lineWidth = Math.max(1, Math.floor(this.canvasManager.zoomLevel));
            ctx.stroke();
            
            // Right tick
            ctx.beginPath();
            ctx.moveTo(pos.x + axisWidth/2, pos.y);
            ctx.lineTo(pos.x + axisWidth/2 + tickSize, pos.y);
            ctx.stroke();
            
            // mm labels - scale font with zoom
            const fontSize = Math.max(12, Math.floor(12 * this.canvasManager.zoomLevel));
            ctx.fillStyle = 'white';
            ctx.font = `${fontSize}px Arial`;
            ctx.textAlign = 'right';
            ctx.fillText(`${mm}mm`, pos.x - axisWidth/2 - tickSize - 5, pos.y + fontSize/3);
            ctx.textAlign = 'left';
            ctx.fillText(`${mm}mm`, pos.x + axisWidth/2 + tickSize + 5, pos.y + fontSize/3);
        }
    }
}
