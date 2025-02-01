# Profile Configuration

This document describes the structure of motion profiles used by the camera slider system.

## Profile Format

```json
{
  "name": "Profile Name",
  "points": [...],
  "settings": {...}
}
```

### Points

Each point in the sequence contains:

1. `positions`: Motor positions in steps
   - 1: Turntable (0-4096 steps = 0-360°)
   - 2: Slider (0-4096 steps = 0-64mm)
   - 3: Pan (760-3900 steps)
   - 4: Tilt (1360-2800 steps)
   - 5: Zoom (0-4096 steps)
   - 6: Focus (0-4096 steps)

2. `focus`: Focus configuration
   - Mode: "point" or "direct"
   - For "point" mode:
     ```json
     "focus": {
       "mode": "point",
       "point": {
         "index": 0,         // Reference to saved focus point
         "x": 400,          // Fallback direct coordinates
         "y": 600,
         "z": -300
       }
     }
     ```
   - For "direct" mode:
     ```json
     "focus": {
       "mode": "direct",
       "values": {
         "pan": 45,         // Degrees
         "tilt": 30,        // Degrees
         "focus": 2048      // Steps
       }
     }
     ```

### Settings

Global settings for profile execution:

- `velocity`: Movement speed (steps/second)
- `acceleration`: Acceleration profile (steps/second²)
- `duration`: Total movement duration (seconds)
- `continuous_focus`: Enable continuous focus tracking during movement
- `focus_update_rate`: Focus tracking update interval (milliseconds)

## Conversion Factors

- Slider: 64mm per 4096 steps (1 rotation)
- Pan/Tilt/Focus: 360° per 4096 steps (1 rotation)

## Notes

- Focus tracking will continuously adjust pan, tilt, and focus to maintain focus on the target point as the slider moves
- When using point mode, the system will first try to use a saved focus point by index, falling back to the provided coordinates if not found
- Direct mode allows manual specification of exact motor angles, useful for precise control or when focus tracking is not needed
