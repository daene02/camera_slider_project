import { SLIDER_STEP_TO_MM } from '../constants.js';

export class MotorPositionHandler {
    constructor() {
        this.currentSliderPosition = 0; // in mm
        this.currentPanAngle = 0;
        this.currentTiltAngle = 0;
        this.updateCallback = null;
    }

    setUpdateCallback(callback) {
        this.updateCallback = callback;
    }

    async updatePositions() {
        try {
            const response = await fetch('/focus/motors/positions');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const positions = await response.json();
            
            if (positions[2]) { // Slider motor ID
                const sliderSteps = positions[2];
                this.currentSliderPosition = sliderSteps * SLIDER_STEP_TO_MM;
            }

            if (positions[3]) { // Pan motor ID
                const panSteps = positions[3];
                this.currentPanAngle = (panSteps / 4096) * 360;
            }

            if (positions[4]) { // Tilt motor ID
                const tiltSteps = positions[4];
                this.currentTiltAngle = (tiltSteps / 4096) * 360;
            }

            if (this.updateCallback) {
                this.updateCallback({
                    sliderPosition: this.currentSliderPosition,
                    panAngle: this.currentPanAngle,
                    tiltAngle: this.currentTiltAngle
                });
            }
        } catch (error) {
            console.error('Error updating motor positions:', error);
        }
    }

    startPolling(interval = 100) {
        this.stopPolling();
        this.pollInterval = setInterval(() => this.updatePositions(), interval);
    }

    stopPolling() {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
            this.pollInterval = null;
        }
    }

    getCurrentPositions() {
        return {
            sliderPosition: this.currentSliderPosition,
            panAngle: this.currentPanAngle,
            tiltAngle: this.currentTiltAngle
        };
    }
}
