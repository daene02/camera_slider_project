export class ProfileManager {
    constructor() {
        this.profilesPanel = document.getElementById('profiles-panel');
        this.pointsPanel = document.getElementById('points-panel');
        this.progressOverlay = document.querySelector('.progress-overlay');
        this.currentProfile = null;
        this.isPlaying = false;
        this.trackingHandler = null;
        
        // Bind methods
        this.updateProfiles = this.updateProfiles.bind(this);
        this.updatePoints = this.updatePoints.bind(this);
        this.playProfile = this.playProfile.bind(this);
        this.stopProfile = this.stopProfile.bind(this);
        
        // Initial load
        this.loadProfiles();
        
        // Start polling for progress updates during playback
        setInterval(() => {
            if (this.isPlaying) {
                this.updateProgress();
            }
        }, 100);
    }
    
    async loadProfiles() {
        try {
            const response = await fetch('/profile/list');
            const profiles = await response.json();
            this.updateProfiles(profiles);
        } catch (error) {
            console.error('Error loading profiles:', error);
        }
    }
    
    updateProfiles(profiles) {
        const content = this.profilesPanel.querySelector('.panel-content');
        content.innerHTML = '';
        
        profiles.forEach(profileName => {
            const item = document.createElement('div');
            item.className = 'profile-item';
            
            const nameDiv = document.createElement('div');
            nameDiv.className = 'profile-name';
            nameDiv.textContent = profileName;
            
            const actions = document.createElement('div');
            actions.className = 'profile-actions';
            
            const playButton = document.createElement('button');
            playButton.className = 'profile-button';
            playButton.innerHTML = '<i class="fas fa-play"></i> Play';
            playButton.onclick = () => this.playProfile(profileName);
            
            actions.appendChild(playButton);
            item.appendChild(nameDiv);
            item.appendChild(actions);
            content.appendChild(item);
        });
    }
    
    setTrackingHandler(handler) {
        this.trackingHandler = handler;
        // Update tracking callback to refresh points display
        if (handler) {
            handler.setUpdateCallback(isTracking => {
                const points = document.querySelectorAll('.point-item');
                points.forEach(point => {
                    const pointId = point.dataset.id;
                    if (pointId === handler.getCurrentPointId()) {
                        point.classList.add('active');
                    } else {
                        point.classList.remove('active');
                    }
                });
            });
        }
    }

    updatePoints(points) {
        if (!points) return;
        
        const content = this.pointsPanel.querySelector('.panel-content');
        const currentPointId = this.trackingHandler?.getCurrentPointId();
        content.innerHTML = '';
        
        points.forEach(point => {
            const item = document.createElement('div');
            item.className = 'point-item';
            if (currentPointId === point.id) {
                item.classList.add('active');
            }
            
            const nameDiv = document.createElement('div');
            nameDiv.className = 'point-name';
            nameDiv.textContent = point.name;
            
            const coords = document.createElement('div');
            coords.className = 'point-coords';
            coords.textContent = `X: ${point.x.toFixed(0)}  Y: ${point.y.toFixed(0)}  Z: ${point.z.toFixed(0)}`;
            
            const angles = document.createElement('div');
            angles.className = 'point-angles';
            
            // Calculate angles
            const dx = point.x;
            const dy = point.y;
            const dz = point.z;
            const panAngle = Math.atan2(dx, Math.abs(dz)) * (180/Math.PI);
            const horizontalDist = Math.sqrt(dx*dx + dz*dz);
            const tiltAngle = Math.atan2(dy, horizontalDist) * (180/Math.PI);
            
            angles.textContent = `Pan: ${panAngle.toFixed(1)}°  Tilt: ${tiltAngle.toFixed(1)}°`;
            
            item.appendChild(nameDiv);
            item.appendChild(coords);
            item.appendChild(angles);
            
            // Add click handler to select point
            item.addEventListener('click', () => {
                if (this.trackingHandler) {
                    this.trackingHandler.selectPoint(point);
                }
            });
            
            // Store point ID for tracking
            item.dataset.id = point.id;
            content.appendChild(item);
        });
    }
    
    async playProfile(profileName) {
        try {
            // Load profile data
            const response = await fetch(`/profile/${profileName}`);
            const profile = await response.json();
            
            // Start playback
            const playResponse = await fetch('/profile/play', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    profile: profile,
                    settings: {}
                })
            });
            
            if (playResponse.ok) {
                this.currentProfile = profile;
                this.isPlaying = true;
                this.updateProgressOverlay(profile.name, 0, profile.points.length);
                this.progressOverlay.classList.add('active');
                
                // Update play button to stop
                const playButton = this.profilesPanel.querySelector(`button`);
                if (playButton) {
                    playButton.innerHTML = '<i class="fas fa-stop"></i> Stop';
                    playButton.onclick = () => this.stopProfile();
                }
            }
        } catch (error) {
            console.error('Error playing profile:', error);
        }
    }
    
    async stopProfile() {
        try {
            await fetch('/profile/stop', { method: 'POST' });
            this.isPlaying = false;
            this.currentProfile = null;
            this.progressOverlay.classList.remove('active');
            
            // Reset play button
            const playButton = this.profilesPanel.querySelector(`button`);
            if (playButton) {
                playButton.innerHTML = '<i class="fas fa-play"></i> Play';
                playButton.onclick = () => this.playProfile(profile.name);
            }
        } catch (error) {
            console.error('Error stopping profile:', error);
        }
    }
    
    async updateProgress() {
        try {
            const response = await fetch('/focus/status');
            const status = await response.json();
            
            if (!status.tracking_active) {
                // Profile finished playing
                this.isPlaying = false;
                this.currentProfile = null;
                this.progressOverlay.classList.remove('active');
                return;
            }
            
            if (this.currentProfile) {
                // Find current point index
                const currentPointIndex = this.currentProfile.points.findIndex(
                    point => point.focus_point_id === status.current_point_id
                );
                
                if (currentPointIndex !== -1) {
                    this.updateProgressOverlay(
                        this.currentProfile.name,
                        currentPointIndex + 1,
                        this.currentProfile.points.length
                    );
                }
            }
        } catch (error) {
            console.error('Error updating progress:', error);
        }
    }
    
    updateProgressOverlay(profileName, current, total) {
        const nameEl = this.progressOverlay.querySelector('.profile-name');
        const statusEl = this.progressOverlay.querySelector('.progress-status');
        const fillEl = this.progressOverlay.querySelector('.progress-bar-fill');
        
        nameEl.textContent = profileName;
        statusEl.textContent = `Point ${current}/${total}`;
        fillEl.style.width = `${(current / total) * 100}%`;
    }
}
