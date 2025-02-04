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
        
        // Initialize renderers
        this.axisRenderer = null;
        
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

    handleMouseMove(event) {
        const rect = this.canvas.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;

        // Check if mouse is over axis numbers
        let needsRedraw = false;
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

    handleClick(event) {
        const rect = this.canvas.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;

        // Check if an axis number was clicked
        if (this.axisRenderer) {
            const mmValue = this.axisRenderer.handleClick(x, y);
            if (mmValue !== null) {
                // Convert mm to motor steps (64/4096 mm per step)
                // steps = mm * (4096/64) = mm * 64
                const position = Math.round(mmValue * 64);
                
                // Send motor position update
                fetch('/motor/2/position', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ position })
                });
            }
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
        const deltaTime = (currentTime - this.lastFrameTime) / 1000; // Convert to seconds
        this.lastFrameTime = currentTime;

        // Smooth zoom animation
        const zoomDiff = this.targetZoom - this.zoomLevel;
        if (Math.abs(zoomDiff) > 0.001) {
            this.zoomLevel += zoomDiff * Math.min(deltaTime * 10, 1); // Adjust speed with the multiplier
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
        console.log("\n=== Drawing Points List ===");
        console.log("Points array:", points);
        console.log("Current point ID:", currentPointId);
        
        if (!points || points.length === 0) {
            console.log("No points to display");
            return;
        }

        const padding = 20;
        const listWidth = 300;  // Increased width for better readability
        const listX = this.canvas.width - listWidth+10- padding;
        const listY = padding;
        const width = listWidth;
        const headerHeight = 40;
        const itemHeight = 70;  // Increased height for better spacing
        const spacing = 10;     // Space between items
        
        // Calculate total height needed
        const totalContentHeight = headerHeight + (points.length * (itemHeight + spacing));
        const listHeight = Math.min(
            this.canvas.height - (padding * 2),  // Maximum available height
            totalContentHeight                   // Required height for all content
        );
        
        console.log("List dimensions:", {
            x: listX,
            y: listY,
            width: width,
            height: listHeight,
            totalItems: points.length
        });
        
        // Draw semi-transparent background
        this.ctx.save();
        this.ctx.beginPath();
        this.ctx.roundRect(listX-150, listY, width, listHeight, 10);
        this.ctx.fillStyle = 'rgba(0, 0, 0, 0.5)';
        this.ctx.fill();
        
        // Draw title
        this.ctx.fillStyle = 'white';
        this.ctx.font = 'bold 16px Arial';
        this.ctx.fillText('Focus Points', listX , listY + 25);
        
        // Draw points
        let y = listY + headerHeight;
        points.forEach(point => {
            // Skip if would render outside visible area
            if (y + itemHeight > listY + listHeight) {
                return;
            }
            
            const isSelected = point.id === currentPointId;
            
            // Draw selection background
            if (isSelected) {
                this.ctx.beginPath();
                this.ctx.roundRect(listX + 5, y, width - 10, itemHeight - spacing, 5);
                this.ctx.fillStyle = 'rgba(255, 255, 255, 0.15)';
                this.ctx.fill();
            }
            
            // Draw point details
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
            
            // Calculate angles
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
