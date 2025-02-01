let currentProfile = {
    name: '',
    points: []
};

function createProfile() {
    const name = document.getElementById('profileName').value.trim();
    if (!name) {
        alert('Please enter a profile name');
        return;
    }
    currentProfile = {
        name: name,
        points: []
    };
    updatePointsList();
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
        
        const positions = await response.json();
        const point = {
            positions: positions,
            timestamp: Date.now()
        };
        
        currentProfile.points.push(point);
        updatePointsList();
    } catch (error) {
        console.error('Error capturing point:', error);
        alert('Failed to capture point');
    }
}

function updatePointsList() {
    const list = document.getElementById('pointsList');
    list.innerHTML = '';
    
    currentProfile.points.forEach((point, index) => {
        const div = document.createElement('div');
        div.className = 'point-item';
        div.innerHTML = `
            <strong>Point ${index + 1}</strong>
            <button onclick="removePoint(${index})" style="float: right;">Remove</button>
            <pre>${JSON.stringify(point.positions, null, 2)}</pre>
        `;
        list.appendChild(div);
    });
}

function removePoint(index) {
    currentProfile.points.splice(index, 1);
    updatePointsList();
}

function startPlayback() {
    if (!currentProfile.name || currentProfile.points.length === 0) {
        alert('Please load a profile with points first');
        return;
    }
    
    const settings = {
        velocity: parseInt(document.getElementById('playbackVelocity').value),
        acceleration: parseInt(document.getElementById('playbackAcceleration').value),
        continuous_focus: document.getElementById('focusMode').checked,
        focus_update_rate: 50  // Default 50ms update rate
    };
    
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

// Debug: Log profile loading on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('Profiles page loaded');
    const select = document.getElementById('profileSelect');
    console.log('Available profiles:', Array.from(select.options).map(opt => opt.value));
});
