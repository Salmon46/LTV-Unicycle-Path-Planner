import math
import numpy as np
from .controller import LTVUnicycleController
from .motion import get_velocity_at_distance

class Simulation:
    def __init__(self):
        self.reset()
        
    def reset(self):
        self.robot_pose = np.array([0.0, 0.0, 0.0])
        self.velocity = 0.0
        self.acceleration = 0.0
        self.jerk = 0.0
        self.prev_velocity = 0.0
        self.prev_acceleration = 0.0
        
        self.time = 0.0
        self.distance_traveled = 0.0
        
        self.is_running = False
        self.controller = None
        self.trajectory = []
        self.path_length = 0.0
        self.total_time = 0.0
        self.generated_profile = []
        
        self.params = {
            'max_vel': 60.0,
            'max_accel': 100.0,
            'max_angular_vel': 3.0,
            'field_min': -72,
            'field_max': 72,
            'robot_radius': 8
        }
        
    def start(self, trajectory, profile, path_length, params, start_pose):
        self.reset()
        self.trajectory = trajectory
        self.generated_profile = profile
        self.path_length = path_length
        if profile:
            self.total_time = profile[-1]['time']
            
        self.params.update(params)
        
        # Initialize controller
        self.controller = LTVUnicycleController(
            kx=params.get('kx', 1.5), 
            ky=params.get('ky', 3.0),
            ktheta=params.get('ktheta', 2.0)
        )
        
        self.robot_pose = np.array(start_pose)
        self.is_running = True
        
    def step(self, dt=0.01):
        if not self.is_running or not self.trajectory:
            return None
        
        # 1. Target Velocity
        target_velocity = get_velocity_at_distance(self.distance_traveled, self.path_length, self.total_time, self.generated_profile)
        
        # 2. Find Closest Point
        min_dist = float('inf')
        closest_idx = 0
        for i, pt in enumerate(self.trajectory):
            dist = math.hypot(pt['x'] - self.robot_pose[0], pt['y'] - self.robot_pose[1])
            if dist < min_dist:
                min_dist = dist
                closest_idx = i
                
        # 3. Lookahead
        # Define a fixed lookahead distance (e.g., 15 units or dynamic based on velocity)
        # A common heuristic: lookahead = min_lookahead + k * velocity
        min_lookahead = self.params.get('min_lookahead', 10.0)
        lookahead_gain = self.params.get('lookahead_gain', 0.1)
        lookahead_distance = min_lookahead + (lookahead_gain * target_velocity)
        
        current_lookahead = 0.0
        target_idx = closest_idx
        
        # Iterate forward until we accumulate enough distance
        while target_idx < len(self.trajectory) - 1:
            if current_lookahead >= lookahead_distance:
                break
                
            # Distance between current target point and next point
            curr_pt = self.trajectory[target_idx]
            next_pt = self.trajectory[target_idx + 1]
            segment_dist = math.hypot(next_pt['x'] - curr_pt['x'], next_pt['y'] - curr_pt['y'])
            
            current_lookahead += segment_dist
            target_idx += 1
        
        ref_point = self.trajectory[target_idx]
        
        # 4. Reference Angular Velocity
        if target_idx < len(self.trajectory) - 1:
            next_point = self.trajectory[min(target_idx + 1, len(self.trajectory) - 1)]
            angle_diff = (next_point['theta'] - ref_point['theta'] + math.pi) % (2 * math.pi) - math.pi
            dist = math.hypot(next_point['x'] - ref_point['x'], next_point['y'] - ref_point['y'])
            referenceW = (angle_diff / dist) * target_velocity
        else:
            referenceW = 0
        
        max_w = self.params['max_angular_vel']
        referenceW = np.clip(referenceW, -max_w, max_w)
        
        # 5. Controller Output
        v, w = self.controller.calculateControl(
            self.robot_pose,
            [ref_point['x'], ref_point['y'], ref_point['theta']],
            target_velocity,
            referenceW
        )
        
        # 6. Dynamics (Acceleration Limit)
        max_accel = self.params['max_accel']
        desired_velocity = v
        velocity_error = desired_velocity - self.velocity
        max_accel_step = max_accel * dt
        
        if velocity_error > max_accel_step:
            velocity_error = max_accel_step
        elif velocity_error < -max_accel_step:
            velocity_error = -max_accel_step
            
        self.velocity += velocity_error
        self.velocity = np.clip(self.velocity, 0, self.params['max_vel'])
        
        # 7. Kinematics Update
        # 0-deg=Up System
        deltaX = self.velocity * math.sin(self.robot_pose[2]) * dt
        deltaY = self.velocity * math.cos(self.robot_pose[2]) * dt
        
        w = np.clip(w, -max_w, max_w)
        
        self.robot_pose[0] += deltaX
        self.robot_pose[1] += deltaY
        self.robot_pose[2] = (self.robot_pose[2] + (w * dt)) % (2 * math.pi)
        
        # Clamp to field
        rmin = self.params['field_min'] + self.params['robot_radius']
        rmax = self.params['field_max'] - self.params['robot_radius']
        self.robot_pose[0] = np.clip(self.robot_pose[0], rmin, rmax)
        self.robot_pose[1] = np.clip(self.robot_pose[1], rmin, rmax)
        
        # 8. Update State
        new_acceleration = (self.velocity - self.prev_velocity) / dt if dt > 0 else 0
        self.jerk = (new_acceleration - self.prev_acceleration) / dt if dt > 0 else 0
        self.acceleration = new_acceleration
        
        self.prev_velocity = self.velocity
        self.prev_acceleration = self.acceleration
        
        self.time += dt
        self.distance_traveled += self.velocity * dt
        
        # Check completion
        final_point = self.trajectory[-1]
        distance_to_end = math.hypot(final_point['x'] - self.robot_pose[0], final_point['y'] - self.robot_pose[1])
        
        path_completion = self.distance_traveled / self.path_length if self.path_length > 0 else 0
        
        if (path_completion >= 0.95 and distance_to_end < 8.0 and abs(self.velocity) < 2.0) or \
           (self.distance_traveled > self.path_length * 1.1):
            self.is_running = False
            
        return {
            'x': self.robot_pose[0],
            'y': self.robot_pose[1],
            'theta': self.robot_pose[2],
            'velocity': self.velocity,
            'acceleration': self.acceleration,
            'jerk': self.jerk,
            'time': self.time,
            'finished': not self.is_running
        }
