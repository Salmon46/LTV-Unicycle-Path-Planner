# API Reference

The backend exposes a RESTful API for path planning and simulation control. All endpoints expect and return JSON.

## Base URL

`http://localhost:8001` (default)

## Endpoints

### Path Generation

#### `POST /api/path/generate`

Generates a discretized trajectory from a list of control points using Cubic Bezier curves.

**Request Body**

```json
{
  "control_points": [
    { "x": 0.0, "y": 0.0 },
    { "x": 1.0, "y": 2.0 },
    ...
  ]
}
```

**Response**

```json
{
  "trajectory": [
    {
      "x": 0.0,
      "y": 0.0,
      "theta": 0.5,
      "distance": 0.0,
      "curvature": 0.0
    },
    ...
  ],
  "length": 15.4
}
```

---

### Motion Profiling

#### `POST /api/motion/profile`

Calculates a motion profile (velocity over time/distance) for a given path length and constraints.

**Request Body**

```json
{
  "path_length": 15.4,
  "type": "trapezoidal",  // or "s-curve"
  "max_vel": 2.0,
  "max_accel": 1.5,
  "max_decel": 1.5,
  "max_jerk": 5.0
}
```

**Response**

```json
{
  "profile": [
    { "t": 0.0, "v": 0.0, "x": 0.0, "a": 1.5 },
    ...
  ]
}
```

---

### Simulation

#### `POST /api/sim/start`

Initializes the simulation with a specific trajectory and profile.

**Request Body**

```json
{
  "trajectory": [...],
  "profile": [...],
  "path_length": 15.4,
  "params": { ... },
  "start_pose": [0.0, 0.0, 0.0]
}
```

#### `POST /api/sim/step`

Advances the simulation by one time step (default 10ms).

**Response**

```json
{
  "running": true,
  "state": {
    "x": 0.1,
    "y": 0.05,
    "theta": 0.1,
    "linear_vel": 0.5,
    "angular_vel": 0.1
  }
}
```

#### `POST /api/sim/reset`

Resets the simulation to the initial state.
