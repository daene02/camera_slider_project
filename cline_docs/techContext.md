# Technical Context - Last Updated: 06/02/2025 4:54am

## Core Technologies

### Camera Integration
- **Library**: gphoto2
- **Camera Model**: Canon EOS R50
- **Features**:
  - Live view streaming
  - Photo capture
  - Video recording
  - Remote settings control
  - Focus control

### Motion Control
- **Hardware**: Dynamixel motors
- **Control Protocol**: DynamixelSDK
- **Movement Types**: 
  - Linear motion (slider)
  - Rotational motion (turntable)
  - Pan/tilt control
  - Focus/zoom control

### Web Interface
- **Framework**: Flask
- **Frontend**: HTML5, JavaScript
- **Communication**: HTTP/REST APIs
- **Real-time Updates**: AJAX polling

## Technical Constraints

### Camera System
- I/O operations can block (needs retry mechanisms)
- Live view requires stable connection
- Video recording needs careful state management
- Focus system needs precise motor control

### Motion Control
- Position verification uses polling
- Motor movements need acceleration control
- Pan/tilt operations require smooth coordination
- Focus tracking needs constant position updates

### Performance Limits
- Live view streaming bandwidth
- Motor position update frequency
- Camera connection stability
- Web interface responsiveness

## Development Environment
- Operating System: Linux 6.6
- Python Environment: Python 3
- Web Server: Flask Development Server
- Database: File-based (JSON)
- Version Control: Git

## Integration Points

### Camera to Motion Control
- Focus tracking system
- Position-based camera triggers
- Movement profile execution
- Emergency stop handling

### Web Interface to Hardware
- Camera control endpoints
- Motor control commands
- Profile management
- Status monitoring

## Security Considerations
- Local network operation only
- No authentication (internal use)
- No encryption for local traffic
- Physical access required

## Performance Requirements
- Live view latency < 500ms
- Motor position accuracy < 0.1 degree
- Camera response time < 100ms
- UI updates every 100ms
