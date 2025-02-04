import { CANVAS_SCALE_FACTOR, SLIDER_MAX_MM } from './constants.js';

// Canvas setup and utility functions
export class CanvasManager {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.zoomLevel = 1;
        this.setupCanvas();
        this.loadBackground();
        
        window.addEventListener('resize', () => this.setupCanvas());
        this.canvas.addEventListener('wheel', (e) => this.handleZoom(e));
    }

    loadBackground() {
        this.background = new Image();
        this.background.src = '/static/images/backgrounds/slider.jpg';
    }

    handleZoom(event) {
        event.preventDefault();
        const zoomFactor = 0.1;
        if (event.deltaY < 0) {
            // Zoom in
            this.zoomLevel = Math.min(this.zoomLevel + zoomFactor, 2.0);
        } else {
            // Zoom out
            this.zoomLevel = Math.max(this.zoomLevel - zoomFactor, 0.2);
        }
    }

    setupCanvas() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
    }

    // Convert world coordinates (mm) to screen coordinates
    worldToScreen(x, y) {
        const centerX = this.canvas.width / 2;
        
        // Consistent 0.5 pixels per mm scaling
        const scale = 1 * this.zoomLevel;
        
        // Use exact mm scaling for both X and Y
        const screenY = this.canvas.height * 0.9 - (y * scale);
        const screenX = centerX + (x * scale);
        
        return { x: screenX, y: screenY };
    }

    // Clear and draw background
    clear() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Draw background if loaded
        if (this.background && this.background.complete) {
            const scale = Math.max(
                this.canvas.width / this.background.width,
                this.canvas.height / this.background.height
            );
            
            const width = this.background.width * scale;
            const height = this.background.height * scale;
            const x = (this.canvas.width - width) / 2;
            const y = (this.canvas.height - height) / 2;
            
            this.ctx.globalAlpha = 0.3; // Make background semi-transparent
            this.ctx.drawImage(this.background, x, y, width, height);
            this.ctx.globalAlpha = 1.0;
        }
    }

    // Get canvas context for drawing
    getContext() {
        return this.ctx;
    }

    // Get canvas dimensions
    getDimensions() {
        return {
            width: this.canvas.width,
            height: this.canvas.height
        };
    }
}
