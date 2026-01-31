from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import numpy as np
import math
import os

from core.geometry import cubic_bezier, cubic_bezier_derivative
from core.motion import generate_profile_points
from core.simulation import Simulation

app = FastAPI()

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simulation State (Single Instance for now)
sim_instance = Simulation()

# --- Data Models ---
class Point(BaseModel):
    x: float
    y: float

class PathRequest(BaseModel):
    control_points: List[Point]

class ProfileRequest(BaseModel):
    path_length: float
    type: str # 'trapezoidal' or 's-curve'
    max_vel: float
    max_accel: float
    max_decel: float
    max_jerk: float

class SimStartRequest(BaseModel):
    trajectory: List[Dict] # List of waypoint dicts
    profile: List[Dict]    # List of profile points
    path_length: float
    params: Dict           # kx, ky, ktheta, etc.
    start_pose: List[float] # [x, y, theta]

# --- Endpoints ---

@app.post("/api/path/generate")
async def generate_path(req: PathRequest):
    control_points = [[p.x, p.y] for p in req.control_points]
    if len(control_points) < 2:
        return {"trajectory": [], "length": 0}
    
    trajectory = []
    cumulative_distance = 0
    path_length = 0
    
    # Re-implementing generateTrajectory logic
    for i in range(0, len(control_points) - 1, 3):
        if i + 3 < len(control_points):
            p0 = np.array(control_points[i])
            p1 = np.array(control_points[i + 1])
            p2 = np.array(control_points[i + 2])
            p3 = np.array(control_points[i + 3])
            
            prev_pt = p0
            for t in np.linspace(0.025, 1, 120): # 40 pt density to 120 pt density
                pt = cubic_bezier(t, p0, p1, p2, p3)
                derivative = cubic_bezier_derivative(t, p0, p1, p2, p3)
                
                # 0-deg=Up Angle
                angle = math.atan2(derivative[0], derivative[1])
                
                seg_dist = np.linalg.norm(pt - prev_pt)
                cumulative_distance += seg_dist
                
                trajectory.append({
                    'x': float(pt[0]), 'y': float(pt[1]), 'theta': float(angle),
                    'distance': float(cumulative_distance), 'curvature': 0.0
                })
                prev_pt = pt
                
        elif i + 1 < len(control_points):
            p0 = np.array(control_points[i])
            p1 = np.array(control_points[i + 1])
            direction = p1 - p0
            angle = math.atan2(direction[0], direction[1]) if np.linalg.norm(direction) > 0 else 0
            
            prev_pt = p0
            for t in np.linspace(0.05, 1, 20):
                pt = p0 + (p1 - p0) * t
                seg_dist = np.linalg.norm(pt - prev_pt)
                cumulative_distance += seg_dist
                
                trajectory.append({
                    'x': float(pt[0]), 'y': float(pt[1]), 'theta': float(angle),
                    'distance': float(cumulative_distance), 'curvature': 0.0
                })
                prev_pt = pt
                
    path_length = cumulative_distance
    
    # Calculate curvature
    for i in range(1, len(trajectory) - 1):
        prev_angle = trajectory[i - 1]['theta']
        next_angle = trajectory[i + 1]['theta']
        delta_angle = (next_angle - prev_angle + math.pi) % (2 * math.pi) - math.pi
        delta_dist = trajectory[i + 1]['distance'] - trajectory[i - 1]['distance']
        if delta_dist > 0.01:
            trajectory[i]['curvature'] = delta_angle / delta_dist
            
    return {"trajectory": trajectory, "length": path_length}

@app.post("/api/motion/profile")
async def generate_profile(req: ProfileRequest):
    # REMOVED: avg_speed = req.max_vel * 0.5 ...
    # REMOVED: total_time = max(3.0, req.path_length / avg_speed)
    
    # Pass path_length directly as the second argument
    profile = generate_profile_points(
        req.type, 
        req.path_length,  # <--- Changed from total_time to path_length
        req.max_vel, 
        req.max_accel, 
        req.max_decel, 
        req.max_jerk
    )
    return {"profile": profile}

@app.post("/api/sim/start")
async def start_sim(req: SimStartRequest):
    sim_instance.start(req.trajectory, req.profile, req.path_length, req.params, req.start_pose)
    return {"status": "started"}

@app.post("/api/sim/step")
async def step_sim():
    state = sim_instance.step(dt=0.01) # 10ms step
    if state is None:
        return {"running": False}
    return {"running": True, "state": state}

@app.post("/api/sim/reset")
async def reset_sim():
    sim_instance.reset()
    return {"status": "reset"}

# Serve Frontend
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../frontend"))
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
