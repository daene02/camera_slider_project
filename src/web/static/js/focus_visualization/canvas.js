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
        
        // Event handlers
        window.addEventListener('resize', () => this.setupCanvas());
        this.canvas.addEventListener('wheel', (e) => this.handleZoom(e));
        this.canvas.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        this.canvas.addEventListener('click', (e) => this.handleClick(e));

        // Enable animation
        requestAnimationFrame(() => this.animate());
        this.lastFrameTime = performance.now();
        this.targetZoom = this.zoomLevel;
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

    isClickInPointsList(x, y) {
        const padding = 20;
        const listWidth = 300;
        const listX = this.canvas.width - listWidth + 10 - padding;
        const listY = padding;
        const headerHeight = 40;
        const itemHeight = 70;
        const spacing = 10;
        const totalContentHeight = headerHeight + (this.points.length * (itemHeight + spacing));
        const listHeight = Math.min(
            this.canvas.height - (padding * 2),
            totalContentHeight
        );

        return (x >= listX - 150 && x <= listX + listWidth &&
                y >= listY && y <= listY + listHeight);
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
        if (this.isClickInPointsList(x, y) || this.isClickOnPoint(x, y)) {
            return; // Let other handlers process the click
        }

        // If click was in empty space and tracking is active, stop tracking
        if (this.trackingHandler && this.trackingHandler.isTracking()) {
            console.log("Click in empty space, stopping tracking");
            this.trackingHandler.stopTracking();
            this.draw(); // Force redraw to update UI
        }
    }

    handleZoom(event) {
        event.preventDefault();
        const zoomFactor = 0.1;
        if (event.deltaY < 0) {
            this.targetZoom = Math.min(this.targetZoom + zoomFactor, 2.0);
        } else {
            this.targetZoom = Math.max(this.targetZoom - zoomFactor, 0.3);
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
        const centerOffsetY = -this.currentSliderY-200;
        const scale = 0.5 * this.zoomLevel;
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

    drawPointsList(points, currentPointId) {
        if (!points || points.length === 0) {
            return;
        }

        const padding = 20;
        const listWidth = 300;
        const listX = this.canvas.width - listWidth+10- padding;
        const listY = padding;
        const width = listWidth;
        const headerHeight = 40;
        const itemHeight = 70;
        const spacing = 10;
        
        const totalContentHeight = headerHeight + (points.length * (itemHeight + spacing));
        const listHeight = Math.min(
            this.canvas.height - (padding * 2),
            totalContentHeight
        );
        
        this.ctx.save();
        this.ctx.beginPath();
        this.ctx.roundRect(listX-150, listY, width, listHeight, 10);
        this.ctx.fillStyle = 'rgba(0, 0, 0, 0.5)';
        this.ctx.fill();
        
        this.ctx.fillStyle = 'white';
        this.ctx.font = 'bold 16px Arial';
        this.ctx.fillText('Focus Points', listX , listY + 25);
        
        let y = listY + headerHeight;
        points.forEach(point => {
            if (y + itemHeight > listY + listHeight) return;
            
            const isSelected = point.id === currentPointId;
            
            if (isSelected) {
                this.ctx.beginPath();
                this.ctx.roundRect(listX + 5, y, width - 10, itemHeight - spacing, 5);
                this.ctx.fillStyle = 'rgba(255, 255, 255, 0.15)';
                this.ctx.fill();
            }
            
            this.ctx.fillStyle = point.color || '#4a9eff';
            this.ctx.font = 'bold 14px Arial';
            this.ctx.fillText(point.name, listX + 15, y + 20);
            
            this.ctx.fillStyle = 'white';
            this.ctx.font = '12px Arial';
            this.ctx.fillText(
                `X: ${point.x.toFixed(0)}mm  Y: ${point.y.toFixed(0)}mm  Z: ${point.z.toFixed(0)}mm`,
                listX + 15,
                y + 40
            );
            
            const dx = point.x;
            const dz = point.z;
            const dy = point.y;
            const panAngle = Math.atan2(dx, Math.abs(dz)) * (180/Math.PI);
            const horizontalDist = Math.sqrt(dx*dx + dz*dz);
            const tiltAngle = Math.atan2(dy, horizontalDist) * (180/Math.PI);
            
            this.ctx.fillText(
                `Pan: ${panAngle.toFixed(1)}°  Tilt: ${tiltAngle.toFixed(1)}°`,
                listX + 15,
                y + 60
            );
            
            y += itemHeight;
        });
        
        this.ctx.restore();
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
            const x = (this.canvas.width - width) / 2;
            const y = (this.canvas.height - height) / 2;
            
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
