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
    if (!currentProfile.name || currentProfile.points.length === 0) {
        alert('Please create a profile and add points first');
        return;
    }
    
    fetch('/profile/save', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(currentProfile)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Profile saved successfully');
            location.reload(); // Refresh to update profile list
        } else {
            alert('Error saving profile');
        }
    })
    .catch(error => console.error('Error:', error));
}

function loadProfile() {
    const select = document.getElementById('profileSelect');
    const profileName = select.value;
    if (!profileName) {
        alert('Please select a profile');
        return;
    }

    fetch(`/profile/${encodeURIComponent(profileName)}`)
        .then(response => response.json())
        .then(data => {
            currentProfile = data;
            updatePointsList();
        })
        .catch(error => console.error('Error:', error));
}

function capturePoint() {
    fetch('/motors/positions')
        .then(response => response.json())
        .then(data => {
            const point = {
                positions: data,
                timestamp: Date.now()
            };
            currentProfile.points.push(point);
            updatePointsList();
        })
        .catch(error => console.error('Error:', error));
}

function updatePointsList() {
    const container = document.getElementById('pointsList');
    container.innerHTML = '';

    currentProfile.points.forEach((point, index) => {
        const div = document.createElement('div');
        div.className = 'point-item';
        
        let positionsText = '';
        Object.entries(point.positions).forEach(([motorId, position]) => {
            positionsText += `Motor ${motorId}: ${position}, `;
        });
        positionsText = positionsText.slice(0, -2); // Remove last comma and space

        div.innerHTML = `
            <strong>Point ${index + 1}</strong>
            <div>${positionsText}</div>
            <button onclick="removePoint(${index})">Remove</button>
        `;
        container.appendChild(div);
    });
}

function removePoint(index) {
    currentProfile.points.splice(index, 1);
    updatePointsList();
}

let isPlaying = false;

function startPlayback() {
    if (isPlaying) {
        alert('Playback already in progress');
        return;
    }
    
    if (currentProfile.points.length === 0) {
        alert('No points to play');
        return;
    }

    const velocity = parseInt(document.getElementById('playbackVelocity').value);
    const acceleration = parseInt(document.getElementById('playbackAcceleration').value);
    const focusMode = document.getElementById('focusMode').checked;

    isPlaying = true;
    document.querySelector('button[onclick="startPlayback()"]').style.backgroundColor = 'rgba(0,255,0,0.2)';
    
    fetch('/profile/play', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            profile: currentProfile,
            settings: {
                velocity: velocity,
                acceleration: acceleration,
                focusMode: focusMode
            }
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        if (!data.success) {
            throw new Error('Server returned error status');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error starting playback: ' + error.message);
        isPlaying = false;
        document.querySelector('button[onclick="startPlayback()"]').style.backgroundColor = '';
    });
}

function stopPlayback() {
    if (!isPlaying) {
        return;
    }

    fetch('/profile/stop', {
        method: 'POST'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        if (!data.success) {
            throw new Error('Server returned error status');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error stopping playback: ' + error.message);
    })
    .finally(() => {
        isPlaying = false;
        document.querySelector('button[onclick="startPlayback()"]').style.backgroundColor = '';
    });
}
