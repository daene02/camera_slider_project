import { CANVAS_SCALE_FACTOR, SLIDER_MAX_MM } from './constants.js';

export class CanvasManager {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.zoomLevel = 1;
        this.currentSliderX = 0;
        this.currentSliderY = 0;
        this.points = [];
        this.setupCanvas();
        this.loadBackground();
        
        // Initialize renderers and handlers
        this.axisRenderer = null;
        this.trackingHandler = null;
        this.pointsRenderer = null;
        this.lastDrawTime = 0;
        this.REDRAW_INTERVAL = 100; // ms
        
        // Event handlers
        window.addEventListener('resize', () => this.setupCanvas());
        this.canvas.addEventListener('wheel', (e) => this.handleZoom(e));
        this.canvas.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        this.canvas.addEventListener('click', (e) => this.handleClick(e));

        // Enable animation
        requestAnimationFrame(() => this.animate());
        this.lastFrameTime = performance.now();
        this.targetZoom = this.zoomLevel;

        // Set up periodic redraw for tracking updates
        setInterval(() => {
            if (this.trackingHandler && this.trackingHandler.isTracking()) {
                const now = performance.now();
                if (now - this.lastDrawTime >= this.REDRAW_INTERVAL) {
                    this.draw();
                    this.lastDrawTime = now;
                }
            }
        }, this.REDRAW_INTERVAL);
    }

    loadBackground() {
        this.background = new Image();
        this.background.src = '/static/images/backgrounds/slider.jpg';
    }

    setTrackingHandler(handler) {
        this.trackingHandler = handler;
    }

    setPointsRenderer(renderer) {
        this.pointsRenderer = renderer;
        if (this.trackingHandler) {
            this.pointsRenderer.setTrackingHandler(this.trackingHandler);
        }
    }

    handleMouseMove(event) {
        const rect = this.canvas.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;

        let needsRedraw = false;
        // Check if mouse is over axis numbers
        if (this.axisRenderer) {
            needsRedraw = this.axisRenderer.handleMouseMove(x, y);
        }
        
        if (needsRedraw) {
            this.draw();
        }
    }

    setAxisRenderer(renderer) {
        this.axisRenderer = renderer;
    }

    isClickOnPoint(x, y) {
        if (!this.pointsRenderer) return false;
        
        const points = this.points || [];
        return points.some(point => {
            const pointPos = this.worldToScreen(point.x, point.y);
            const distance = Math.sqrt(
                Math.pow(x - pointPos.x, 2) + 
                Math.pow(y - pointPos.y, 2)
            );
            return distance <= (12 * this.zoomLevel * 2);
        });
    }

    handleClick(event) {
        const rect = this.canvas.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;

        // First check if we clicked on axis numbers
        if (this.axisRenderer) {
            const mmValue = this.axisRenderer.handleClick(x, y);
            if (mmValue !== null) {
                // Convert mm to motor steps and send position update
                const position = Math.round(mmValue * 64);
                fetch('/motor/2/position', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ position })
                });
                this.draw(); // Redraw to update axis highlights
                return;
            }
        }

        // Then check other UI areas
        if (this.isClickOnPoint(x, y)) {
            return; // Let other handlers process the click
        }

        // If click was in empty space and tracking is active, stop tracking
       // if (this.trackingHandler && this.trackingHandler.isTracking()) {
         //   console.log("Click in empty space, stopping tracking");
          //  this.trackingHandler.stopTracking();
            //this.draw(); // Force redraw to update UI
       // }
    }

    handleZoom(event) {
        event.preventDefault();
        const zoomFactor = 0.5;
        if (event.deltaY < 0) {
            this.targetZoom = Math.min(this.targetZoom + zoomFactor, 5);
        } else {
            this.targetZoom = Math.max(this.targetZoom - zoomFactor, 0.2);
        }
    }

    animate() {
        const currentTime = performance.now();
        const deltaTime = (currentTime - this.lastFrameTime) / 1000;
        this.lastFrameTime = currentTime;

        const zoomDiff = this.targetZoom - this.zoomLevel;
        if (Math.abs(zoomDiff) > 0.001) {
            this.zoomLevel += zoomDiff * Math.min(deltaTime * 10, 1);
            this.draw();
        }

        requestAnimationFrame(() => this.animate());
    }

    setupCanvas() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
    }

    setCurrentPosition(x, y) {
        this.currentSliderX = x;
        this.currentSliderY = y;
    }

    setPoints(points) {
        this.points = points;
    }

    worldToScreen(x, y) {
        const centerOffsetX = -this.currentSliderX;
        const centerOffsetY = -this.currentSliderY-100;
        const scale = 0.8 * this.zoomLevel;
        const screenY = (this.canvas.height/2) - ((y + centerOffsetY) * scale);
        const screenX = (this.canvas.width/2) + ((x + centerOffsetX) * scale);
        return { x: screenX, y: screenY };
    }

    draw() {
        this.clear();
        if (this.onDraw) {
            this.onDraw();
        }
    }

    clear() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        if (this.background && this.background.complete) {
            const scale = Math.max(
                this.canvas.width / this.background.width,
                this.canvas.height / this.background.height
            );
            
            const width = this.background.width * scale;
            const height = this.background.height * scale;
            const x = (this.canvas.width - width) / 1;
            const y = (this.canvas.height - height) / 1;
            
            this.ctx.globalAlpha = 0.3;
            this.ctx.drawImage(this.background, x, y, width, height);
            this.ctx.globalAlpha = 1.0;
        }
    }

    getContext() {
        return this.ctx;
    }

    getDimensions() {
        return {
            width: this.canvas.width,
            height: this.canvas.height
        };
    }
}
