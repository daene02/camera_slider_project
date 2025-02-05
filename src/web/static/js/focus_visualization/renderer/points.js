export class PointsRenderer {
    constructor(canvasManager, motorHandler) {
        this.canvasManager = canvasManager;
        this.motorHandler = motorHandler;
        this.blinkState = true;
        this.lastBlinkTime = 0;
        this.BLINK_INTERVAL = 500; // milliseconds
        this.hoverPoint = null;
        this.trackingHandler = null;
        
        // Bind event handlers
        this.handleMouseMove = this.handleMouseMove.bind(this);
        this.handleClick = this.handleClick.bind(this);
        
        // Add event listeners
        this.canvasManager.canvas.addEventListener('mousemove', this.handleMouseMove);
        this.canvasManager.canvas.addEventListener('click', this.handleClick);

        // Start blink animation
        this.startBlinking();
    }

    setTrackingHandler(trackingHandler) {
        console.log("Setting tracking handler in PointsRenderer");
        this.trackingHandler = trackingHandler;
    }

    startBlinking() {
        setInterval(() => {
            const currentTime = Date.now();
            if (currentTime - this.lastBlinkTime > this.BLINK_INTERVAL) {
                this.blinkState = !this.blinkState;
                this.lastBlinkTime = currentTime;
                if (this.trackingHandler && this.trackingHandler.isTracking()) {
                    this.canvasManager.draw();
                }
            }
        }, 100);
    }

    handleMouseMove(event) {
        const rect = this.canvasManager.canvas.getBoundingClientRect();
        const mouseX = event.clientX - rect.left;
        const mouseY = event.clientY - rect.top;
        
        const points = this.canvasManager.points || [];
        this.hoverPoint = points.find(point => {
            const pointPos = this.canvasManager.worldToScreen(point.x, point.y);
            const distance = Math.sqrt(
                Math.pow(mouseX - pointPos.x, 2) + 
                Math.pow(mouseY - pointPos.y, 2)
            );
            return distance <= (12 * this.canvasManager.zoomLevel * 2);
        });
        
        if (this.hoverPoint) {
            this.canvasManager.canvas.style.cursor = 'pointer';
        } else {
            this.canvasManager.canvas.style.cursor = 'default';
        }
        
        this.canvasManager.draw();
    }

    handleClick(event) {
        const rect = this.canvasManager.canvas.getBoundingClientRect();
        const mouseX = event.clientX - rect.left;
        const mouseY = event.clientY - rect.top;
        
        const points = this.canvasManager.points || [];
        const clickedPoint = points.find(point => {
            const pointPos = this.canvasManager.worldToScreen(point.x, point.y);
            const distance = Math.sqrt(
                Math.pow(mouseX - pointPos.x, 2) + 
                Math.pow(mouseY - pointPos.y, 2)
            );
            return distance <= (12 * this.canvasManager.zoomLevel * 2);
        });
        
        if (clickedPoint && this.trackingHandler) {
            console.log("Point clicked:", clickedPoint);
            this.trackingHandler.selectPoint(clickedPoint)
                .then(success => {
                    if (success) {
                        console.log("Point selection successful");
                    } else {
                        console.error("Failed to select point");
                    }
                    this.canvasManager.draw();
                })
                .catch(error => {
                    console.error("Error selecting point:", error);
                });
        }
    }

    draw(points, currentPointId, isTracking) {
        if (!points || points.length === 0) return;

        // First draw all inactive points and their connectors
        points.forEach(point => {
            const isActive = isTracking && point.id === currentPointId;
            // Draw inactive points or active point during blink-on phase
            if (!isActive || this.blinkState) {
                this.drawPointConnector(point);
                this.drawHeightLine(point);
            }
        });
        
        // Draw tracking line if there's an active point
        if (isTracking && currentPointId !== null) {
            const currentPoint = points.find(p => p.id === currentPointId);
            if (currentPoint) {
                this.drawDashedLineToSlider(currentPoint);
            }
        }
        
        // Then draw all points on top
        points.forEach(point => {
            const isActive = isTracking && point.id === currentPointId;
            const isHovered = this.hoverPoint && this.hoverPoint.id === point.id;
            
            // Skip blinking point during off phase
            if (isActive && !this.blinkState) return;
            
            this.drawPoint(point, isActive, isHovered);
        });
    }

    drawDashedLineToSlider(currentPoint) {
        const ctx = this.canvasManager.getContext();
        const pointPos = this.canvasManager.worldToScreen(currentPoint.x, currentPoint.y);
        
        // Get current slider position
        const positions = this.motorHandler.getCurrentPositions();
        if (!positions || positions.sliderPosition === undefined) {
            console.log("No slider position available");
            return;
        }
        
        // Convert slider position to screen coordinates
        const sliderPos = this.canvasManager.worldToScreen(0, positions.sliderPosition);
        
        ctx.save();
        ctx.beginPath();
        ctx.setLineDash([10, 5]); // 10px dash, 5px gap
        ctx.moveTo(pointPos.x, pointPos.y);
        ctx.lineTo(sliderPos.x, sliderPos.y);
        ctx.strokeStyle = 'rgba(74, 158, 255, 0.8)';
        ctx.lineWidth = 2 * this.canvasManager.zoomLevel;
        ctx.stroke();
        ctx.restore();
    }

    drawPoint(point, isActive, isHovered) {
        const ctx = this.canvasManager.getContext();
        const pos = this.canvasManager.worldToScreen(point.x, point.y);
        
        // Base radius and hover/active scaling
        const baseRadius = 6;
        let scaleFactor = 1;
        if (isHovered) scaleFactor = 2;
        if (isActive) scaleFactor = 1.5;
        
        const radius = baseRadius * scaleFactor * this.canvasManager.zoomLevel;
        
        ctx.save();
        
        // Draw glow effect
        const pointColor = isActive ? '#00ff00' : point.color || '#4a9eff';
        ctx.shadowColor = pointColor;
        ctx.shadowBlur = radius * 2;
        
        // Outer glow
        ctx.beginPath();
        ctx.arc(pos.x, pos.y, radius * 1.2, 0, Math.PI * 2);
        ctx.fillStyle = pointColor;
        ctx.globalAlpha = 0.3;
        ctx.fill();
        
        // Inner glow
        ctx.beginPath();
        ctx.arc(pos.x, pos.y, radius, 0, Math.PI * 2);
        ctx.globalAlpha = 0.7;
        ctx.fill();
        
        // Draw labels
        ctx.shadowColor = 'transparent';
        ctx.fillStyle = 'white';
        ctx.textAlign = 'center';
        
        // Point name
        const fontSize = Math.max(12, Math.floor(12 * this.canvasManager.zoomLevel));
        ctx.font = `bold ${fontSize}px Arial`;
        ctx.fillText(point.name, pos.x, pos.y - radius - 5);
        
        // Coordinates (if zoomed in enough)
        if (this.canvasManager.zoomLevel > 0.8) {
            ctx.font = `${fontSize - 2}px Arial`;
            ctx.fillText(
                `(${point.x.toFixed(0)}, ${point.y.toFixed(0)}, ${point.z.toFixed(0)})`,
                pos.x,
                pos.y + radius + fontSize
            );
        }
        
        ctx.restore();
    }

    drawPointConnector(point) {
        const ctx = this.canvasManager.getContext();
        const pos = this.canvasManager.worldToScreen(point.x, point.y);
        const centerX = this.canvasManager.worldToScreen(0, point.y).x;
        
        ctx.save();
        ctx.beginPath();
        ctx.moveTo(pos.x, pos.y);
        ctx.lineTo(centerX, pos.y);
        ctx.strokeStyle = point.color || '#4a9eff';
        ctx.globalAlpha = 0.3;
        ctx.lineWidth = Math.max(1, this.canvasManager.zoomLevel);
        ctx.stroke();
        ctx.restore();
    }

    drawHeightLine(point) {
        const ctx = this.canvasManager.getContext();
        const topPos = this.canvasManager.worldToScreen(point.x, point.y + 50);
        const bottomPos = this.canvasManager.worldToScreen(point.x, point.y - 50);
        
        ctx.save();
        ctx.beginPath();
        ctx.moveTo(topPos.x, topPos.y);
        ctx.lineTo(bottomPos.x, bottomPos.y);
        ctx.setLineDash([5, 5]);
        ctx.strokeStyle = point.color || '#4a9eff';
        ctx.globalAlpha = 0.2;
        ctx.lineWidth = Math.max(1, this.canvasManager.zoomLevel);
        ctx.stroke();
        ctx.restore();
    }
}
