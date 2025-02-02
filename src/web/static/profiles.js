let currentProfile = {
    name: '',
    points: [],
    acceleration: 1800
};

function createProfile() {
    const name = document.getElementById('profileName').value.trim();
    if (!name) {
        alert('Please enter a profile name');
        return;
    }
    currentProfile = {
        name: name,
        points: [],
        acceleration: parseInt(document.getElementById('playbackAcceleration').value) || 1800
    };
    updatePointsList();
    saveToLocalStorage();
}

function saveProfile() {
    if (!currentProfile.name) {
        alert('Please create or load a profile first');
        return;
    }
    
    fetch('/profile/save', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(currentProfile)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Profile saved successfully');
            // Refresh the page to update the profile list
            location.reload();
        } else {
            throw new Error(data.error || 'Failed to save profile');
        }
    })
    .catch(error => {
        console.error('Error saving profile:', error);
        alert('Failed to save profile');
    });
}

function loadProfile() {
    const select = document.getElementById('profileSelect');
    const profileName = select.value;
    
    if (!profileName) {
        alert('Please select a profile');
        return;
    }
    
    console.log('Loading profile:', profileName); // Debug log
    
    fetch(`/profile/${profileName}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Profile data received:', data); // Debug log
            currentProfile = data;
            document.getElementById('profileName').value = data.name;
            updatePointsList();
            saveToLocalStorage();
        })
        .catch(error => {
            console.error('Error loading profile:', error);
            alert('Failed to load profile: ' + error.message);
        });
}

async function capturePoint() {
    if (!currentProfile.name) {
        alert('Please create or load a profile first');
        return;
    }
    
    try {
        const response = await fetch('/motors/positions');
        if (!response.ok) throw new Error('Failed to get motor positions');
        
        const allPositions = await response.json();
        
        // Filter out pan/tilt motors (IDs 3 and 4)
        const positions = {};
        Object.entries(allPositions).forEach(([id, value]) => {
            if (!['3', '4'].includes(id)) {
                positions[id] = value;
            }
        });

        const point = {
            positions: positions,
            velocity: 1000,  // Default velocity
            timestamp: Date.now()
        };
        
        currentProfile.points.push(point);
        updatePointsList();
        saveToLocalStorage();
    } catch (error) {
        console.error('Error capturing point:', error);
        alert('Failed to capture point');
    }
}

function updatePointsList() {
    const list = document.getElementById('pointsList');
    list.innerHTML = '';
    
    // Only show motors we want to save in profiles (no pan/tilt)
    const motorNames = {
        "1": "Turntable",
        "2": "Slider",
        "5": "Zoom",
        "6": "Focus"
    };

    currentProfile.points.forEach((point, index) => {
        const div = document.createElement('div');
        div.className = 'point-item';
        
        let positionsHtml = '';
        for (const [motorId, name] of Object.entries(motorNames)) {
            const value = point.positions[motorId] || 0;
            positionsHtml += `
                <div class="position-row">
                    <label>${name}:</label>
                    <input type="number" 
                           value="${value}"
                           onchange="updatePointPosition(${index}, '${motorId}', this.value)"
                           class="position-input">
                    <span class="unit">steps</span>
                </div>
            `;
        }

        div.innerHTML = `
            <div class="point-header">
                <strong>Point ${index + 1}</strong>
                <div class="point-controls">
                    ${index > 0 ? `<button onclick="movePoint(${index}, ${index-1})" title="Move Up">↑</button>` : ''}
                    ${index < currentProfile.points.length-1 ? `<button onclick="movePoint(${index}, ${index+1})" title="Move Down">↓</button>` : ''}
                    <button onclick="removePoint(${index})" class="remove-btn" title="Remove Point">×</button>
                </div>
            </div>
            <div class="point-content">
                <div class="motor-positions">
                    ${positionsHtml}
                </div>
                <div class="velocity-control">
                    <label>Velocity:</label>
                    <input type="number" 
                           value="${point.velocity}"
                           min="0" 
                           max="1023" 
                           onchange="updatePointVelocity(${index}, this.value)"
                           class="velocity-input">
                </div>
            </div>
        `;
        list.appendChild(div);
    });
}

function updatePointPosition(index, motorId, value) {
    currentProfile.points[index].positions[motorId] = parseInt(value);
    saveToLocalStorage();
}

function updatePointVelocity(index, value) {
    currentProfile.points[index].velocity = parseInt(value);
    saveToLocalStorage();
}

function movePoint(fromIndex, toIndex) {
    const point = currentProfile.points.splice(fromIndex, 1)[0];
    currentProfile.points.splice(toIndex, 0, point);
    updatePointsList();
    saveToLocalStorage();
}

function removePoint(index) {
    currentProfile.points.splice(index, 1);
    updatePointsList();
    saveToLocalStorage();
}

function startPlayback() {
    if (!currentProfile.name || currentProfile.points.length === 0) {
        alert('Please load a profile with points first');
        return;
    }
    
    // Update global acceleration from input
    currentProfile.acceleration = parseInt(document.getElementById('playbackAcceleration').value);
    
    const settings = {}; // No settings needed, acceleration is in profile
    
    fetch('/profile/play', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            profile: currentProfile,
            settings: settings
        })
    })
    .then(response => response.json())
    .then(data => {
        if (!data.success) {
            throw new Error(data.error || 'Failed to start playback');
        }
    })
    .catch(error => {
        console.error('Error starting playback:', error);
        alert('Failed to start playback');
    });
}

function stopPlayback() {
    fetch('/profile/stop', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (!data.success) {
            throw new Error(data.error || 'Failed to stop playback');
        }
    })
    .catch(error => {
        console.error('Error stopping playback:', error);
        alert('Failed to stop playback');
    });
}

// Local storage functions
function saveToLocalStorage() {
    localStorage.setItem('currentProfile', JSON.stringify(currentProfile));
    localStorage.setItem('lastProfileName', currentProfile.name);
}

function loadFromLocalStorage() {
    const savedProfile = localStorage.getItem('currentProfile');
    if (savedProfile) {
        currentProfile = JSON.parse(savedProfile);
        document.getElementById('profileName').value = currentProfile.name;
        document.getElementById('playbackAcceleration').value = currentProfile.acceleration || 1800;
        updatePointsList();
    }

    // Load last profile name
    const lastProfileName = localStorage.getItem('lastProfileName');
    if (lastProfileName) {
        const select = document.getElementById('profileSelect');
        select.value = lastProfileName;
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('Profiles page loaded');
    loadFromLocalStorage();
});

// Add auto-save to acceleration changes
document.getElementById('playbackAcceleration').addEventListener('change', (e) => {
    currentProfile.acceleration = parseInt(e.target.value);
    saveToLocalStorage();
});
