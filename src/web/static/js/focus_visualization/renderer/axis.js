import { SLIDER_MAX_MM } from '../constants.js';

export class AxisRenderer {
    constructor(canvasManager) {
        this.canvasManager = canvasManager;
        this.clickableAreas = [];
        this.hoveredValue = null;
        this.selectedValue = null;
    }

    draw() {
        const ctx = this.canvasManager.getContext();
        const start = this.canvasManager.worldToScreen(0, 0);
        const end = this.canvasManager.worldToScreen(0, SLIDER_MAX_MM);
        
        // Reset clickable areas
        this.clickableAreas = [];
        
        // Draw background for axis - width scales with zoom
        const axisWidth = Math.max(15, 20 * this.canvasManager.zoomLevel);
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
            
            // Scale font size based on hover/zoom
            let fontSize = Math.max(12, Math.floor(12 * this.canvasManager.zoomLevel));
            if (mm === this.hoveredValue) {
                fontSize = Math.floor(fontSize * 1.5); // 50% larger on hover
            }
            
            ctx.font = `${fontSize}px Arial`;
            const text = `${mm}`;
            const metrics = ctx.measureText(text);
            
            // Store clickable area
            this.clickableAreas.push({
                x: pos.x + axisWidth/2 + tickSize + 15,
                y: pos.y - fontSize/2,
                width: metrics.width,
                height: fontSize,
                value: mm
            });
            
            // Set up text style
            ctx.textAlign = 'left';
            
            // Add glow effect for selected value
            if (mm === this.selectedValue) {
                ctx.save();
                ctx.shadowColor = '#00ff00';
                ctx.shadowBlur = 15;
                ctx.fillStyle = '#00ff00';
            } else {
                ctx.fillStyle = 'white';
            }
            
            ctx.fillText(text, pos.x + axisWidth/2 + tickSize + 15, pos.y + fontSize/3);
            
            if (mm === this.selectedValue) {
                ctx.restore();
            }
        }
    }

    handleMouseMove(x, y) {
        let found = false;
        for (const area of this.clickableAreas) {
            if (x >= area.x && x <= area.x + area.width &&
                y >= area.y && y <= area.y + area.height) {
                this.hoveredValue = area.value;
                found = true;
                break;
            }
        }
        if (!found && this.hoveredValue !== null) {
            this.hoveredValue = null;
            return true; // Changed state
        }
        return found; // Return true if hovering over a number
    }

    handleClick(x, y) {
        for (const area of this.clickableAreas) {
            if (x >= area.x && x <= area.x + area.width &&
                y >= area.y && y <= area.y + area.height) {
                this.selectedValue = area.value;
                return area.value;
            }
        }
        return null;
    }
}
