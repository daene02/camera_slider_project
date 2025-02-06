export class ProfileManager {
    constructor() {
        // Initialize panels
        this.profilesPanel = document.getElementById('profiles-panel');
        this.pointsPanel = document.getElementById('points-panel');
        
        // Create progress overlay if it doesn't exist
        this.progressOverlay = document.querySelector('.progress-overlay');
        if (!this.progressOverlay) {
            this.progressOverlay = document.createElement('div');
            this.progressOverlay.className = 'progress-overlay';
            this.progressOverlay.innerHTML = `
                <div class="progress-content">
                    <div class="profile-name"></div>
                    <div class="progress-bar">
                        <div class="progress-bar-fill"></div>
                    </div>
                    <div class="progress-status"></div>
                </div>
            `;
            document.body.appendChild(this.progressOverlay);
        }
        
        // Initialize state
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
            if (this.isPlaying || this.progressOverlay.classList.contains('active')) {
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
            item.dataset.profileName = profileName;
            
            const nameDiv = document.createElement('div');
            nameDiv.className = 'profile-name';
            nameDiv.textContent = profileName;
            
            const actions = document.createElement('div');
            actions.className = 'profile-actions';
            
            const playButton = document.createElement('button');
            playButton.className = 'profile-button';
            playButton.dataset.profileName = profileName;
            playButton.innerHTML = '<i class="fas fa-play"></i> Play';
            playButton.onclick = (e) => {
                e.stopPropagation();
                if (this.isPlaying && this.currentProfile?.name === profileName) {
                    this.stopProfile();
                } else {
                    this.playProfile(profileName);
                }
            };
            
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
            if (this.isPlaying) {
                console.log('Already playing a profile');
                return;
            }

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
                
                // Update button states
                const buttons = this.profilesPanel.querySelectorAll('.profile-button');
                buttons.forEach(button => {
                    const isCurrentProfile = button.closest('.profile-item').dataset.profileName === profileName;
                    if (isCurrentProfile) {
                        button.innerHTML = '<i class="fas fa-stop"></i> Stop';
                        button.classList.add('active');
                    } else {
                        button.disabled = true;
                    }
                });
            }
        } catch (error) {
            console.error('Error playing profile:', error);
            this.resetProfileButtons();
        }
    }
    
    async stopProfile() {
        try {
            if (!this.isPlaying) {
                console.log('No profile is currently playing');
                return;
            }

            const stopResponse = await fetch('/profile/stop', { method: 'POST' });
            if (stopResponse.ok) {
                this.isPlaying = false;
                this.currentProfile = null;
                this.progressOverlay.classList.remove('active');
                this.resetProfileButtons();
            }
        } catch (error) {
            console.error('Error stopping profile:', error);
        }
    }

    resetProfileButtons() {
        const buttons = this.profilesPanel.querySelectorAll('.profile-button');
        buttons.forEach(button => {
            button.innerHTML = '<i class="fas fa-play"></i> Play';
            button.classList.remove('active');
            button.disabled = false;
        });
    }
    
    async updateProgress() {
        try {
            const response = await fetch('/focus/status');
            const status = await response.json();
            
            if (this.currentProfile) {
                // Show the overlay while profile is active
                if (!this.progressOverlay.classList.contains('active')) {
                    this.progressOverlay.classList.remove('hidden');
                    this.progressOverlay.classList.add('active');
                }
                
                // Find current point index, accounting for the camera position
                const currentPointIndex = this.currentProfile.points.findIndex(
                    point => point.focus_point_id === status.current_point_id
                );
                
                // Always update progress even if point hasn't changed
                this.updateProgressOverlay(
                    this.currentProfile.name,
                    currentPointIndex >= 0 ? currentPointIndex + 1 : 1,
                    this.currentProfile.points.length
                );
                
                // Hide overlay if profile completes
                if (!status.tracking_active && currentPointIndex === this.currentProfile.points.length - 1) {
                    this.isPlaying = false;
                    this.currentProfile = null;
                    this.progressOverlay.classList.add('hidden');
                    setTimeout(() => {
                        this.progressOverlay.classList.remove('active');
                    }, 300); // Match CSS transition duration
                }
            } else {
                // No active profile
                this.progressOverlay.classList.add('hidden');
                setTimeout(() => {
                    if (!this.currentProfile) {
                        this.progressOverlay.classList.remove('active');
                    }
                }, 300);
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
