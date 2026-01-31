import math

def trapezoidal_profile(distance, v_max, accel, decel):
    """
    Generate a trapezoidal velocity profile based on TARGET DISTANCE.
    """
    if distance <= 0:
        return {'v_peak': 0, 't_accel': 0, 't_cruise': 0, 't_decel': 0, 'total_time': 0}

    # 1. Calculate distance to reach v_max and stop
    d_accel_limit = (v_max**2) / (2 * accel)
    d_decel_limit = (v_max**2) / (2 * decel)
    
    if d_accel_limit + d_decel_limit > distance:
        # Triangle Profile (Short move)
        # Solve d = v^2/2a + v^2/2d for v
        v_peak = math.sqrt(distance * 2 * accel * decel / (accel + decel))
        t_accel = v_peak / accel
        t_decel = v_peak / decel
        t_cruise = 0
    else:
        # Full Trapezoid (Cruise phase)
        v_peak = v_max
        t_accel = v_max / accel
        t_decel = v_max / decel
        d_cruise = distance - d_accel_limit - d_decel_limit
        t_cruise = d_cruise / v_peak
    
    return {
        'v_peak': v_peak,
        't_accel': t_accel,
        't_cruise': t_cruise,
        't_decel': t_decel,
        'total_time': t_accel + t_cruise + t_decel
    }

def _calculate_scurve_min_dist(v_target, max_accel, max_jerk):
    """
    Helper: Calculates the minimum distance required to reach v_target
    and come back to stop using an S-Curve profile.
    Returns: (total_distance, t_jerk, t_accel_total)
    """
    # 1. Check if we are Jerk Limited (can't reach max_accel)
    # Velocity reached by ramping accel up to max and immediately down: v = a_max^2 / jerk
    v_at_max_accel = (max_accel**2) / max_jerk
    
    if v_target < v_at_max_accel:
        # Jerk Limited: We don't reach max_accel
        # shape is triangular acceleration
        t_j = math.sqrt(v_target / max_jerk)
        t_a_total = 2 * t_j
        # Distance = 2 * distance_of_accel_phase (assuming symm decel for min dist calculation)
        # Actually, let's just compute the accel phase distance
        # d_accel = v_target * t_a_total / 2 (approx? No, exact integral is complex)
        # Accurate calculation:
        # d_accel = v_target * t_a_total - (conditions...)
        # Simpler: d_accel = integral of velocity. 
        # For Jerk Limited, d_accel = v_target * t_a_total / 2 is incorrect.
        # Let's use the known result for S-curve accel distance:
        d_accel = v_target * t_a_total / 2 # This holds for symmetric jerk up/down
    else:
        # Accel Limited: We saturate at max_accel
        t_j = max_accel / max_jerk
        t_ramp = (v_target / max_accel) - t_j # Time spent at constant max accel (middle part of accel phase)
        t_a_total = 2 * t_j + t_ramp
        
        d_accel = (v_target * t_a_total) / 2 # S-curve accel distance is still v*t/2 IF starting from 0?
        # No, for trapezoidal accel profile:
        # d = (v0 + v1)/2 * t is only for constant accel.
        # Correct dist = v_target * (t_total_accel / 2) + ...?
        # Let's trust the integration: d_accel = (v_target / 2) * (t_ramp + 2*t_j) = (v * t_total) / 2
        # Yes, purely due to symmetry of the acceleration profile, average velocity is v_final/2.
        d_accel = v_target * t_a_total / 2

    return d_accel * 2, t_j, t_a_total # mult by 2 for decel phase

def scurve_profile(distance, v_max, max_accel, max_decel, max_jerk):
    """
    Generate S-Curve profile based on TARGET DISTANCE.
    Uses binary search for short moves.
    Assuming symmetric Max Accel and Max Decel for simplicity in S-Curve fitting.
    """
    if distance <= 0:
        return {'v_peak': 0, 't_j': 0, 't_accel': 0, 't_cruise': 0, 't_decel': 0, 'total_time': 0}
        
    # Use the stricter limit for symmetry
    limit_a = min(abs(max_accel), abs(max_decel))
    
    # 1. Can we reach v_max?
    min_dist_for_vmax, t_j_vmax, t_a_vmax = _calculate_scurve_min_dist(v_max, limit_a, max_jerk)
    
    if min_dist_for_vmax <= distance:
        # Long Move: We cruise at v_max
        v_peak = v_max
        t_j = t_j_vmax
        t_accel = t_a_vmax
        t_decel = t_a_vmax
        
        dist_cruise = distance - min_dist_for_vmax
        t_cruise = dist_cruise / v_peak
    else:
        # Short Move: We need to solve for v_peak < v_max
        # Binary Search for v_peak such that _calculate_min_dist(v_peak) ~= distance
        low = 0.0
        high = v_max
        for _ in range(20): # 20 iters is ~1e-6 precision
            mid = (low + high) / 2
            d, _, _ = _calculate_scurve_min_dist(mid, limit_a, max_jerk)
            if d > distance:
                high = mid
            else:
                low = mid
        
        v_peak = low
        _, t_j, t_accel = _calculate_scurve_min_dist(v_peak, limit_a, max_jerk)
        t_decel = t_accel
        t_cruise = 0

    return {
        'v_peak': v_peak,
        't_j': t_j,
        't_accel': t_accel,
        't_cruise': t_cruise,
        't_decel': t_decel,
        'total_time': t_accel + t_cruise + t_decel
    }

def generate_profile_points(profile_type, target_distance, max_speed, max_accel, max_decel, max_jerk, num_points=200):
    generated_profile = []
    
    if profile_type == 'trapezoidal':
        profile = trapezoidal_profile(target_distance, max_speed, max_accel, max_decel)
        
        for i in range(num_points):
            t = (profile['total_time'] / (num_points - 1)) * i if num_points > 1 else 0
            
            if t < profile['t_accel']:
                # Ramp up
                v = (max_accel * t) if profile['t_accel'] > 0 else 0
                v = min(v, profile['v_peak']) # Clamp
                a = max_accel
                j = 0
            elif t < profile['t_accel'] + profile['t_cruise']:
                # Cruise
                v = profile['v_peak']
                a = 0
                j = 0
            elif t <= profile['total_time'] + 0.001:
                # Ramp down
                t_dec_elapsed = t - profile['t_accel'] - profile['t_cruise']
                v = profile['v_peak'] - (max_decel * t_dec_elapsed)
                a = -max_decel
                j = 0
            else:
                v = 0
                a = 0
                j = 0
            
            generated_profile.append({
                'time': t,
                'velocity': max(0, v),
                'acceleration': a,
                'jerk': j
            })
            
    elif profile_type == 's-curve':
        # S-Curve Generation
        profile = scurve_profile(target_distance, max_speed, max_accel, max_decel, max_jerk)
        
        # Unpack times for easier reading
        t_j = profile['t_j']
        t_a = profile['t_accel']
        t_c = profile['t_cruise']
        t_d = profile['t_decel']
        v_peak = profile['v_peak']
        
        # Calculated acceleration to use (might be lower than max if jerk limited)
        # Re-derive actual peak accel from t_j and t_a
        # if t_a == 2*t_j, we are jerk limited. a_peak = t_j * jerk
        # if t_a > 2*t_j, we are accel limited. a_peak = max_accel
        if t_a > 2 * t_j + 0.0001:
             actual_a_max = max_accel # (Or limit_a)
        else:
             actual_a_max = t_j * max_jerk

        for i in range(num_points):
            t = (profile['total_time'] / (num_points - 1)) * i if num_points > 1 else 0
            
            j = 0
            a = 0
            v = 0
            
            # 1. Acceleration Phase
            if t < t_a:
                if t < t_j:
                    # Ramp Jerk Up
                    j = max_jerk
                    a = max_jerk * t
                    v = (1/6) * max_jerk * t**3 # No? v = integral(a) = 0.5 * J * t^2
                    v = 0.5 * max_jerk * t**2
                elif t < t_a - t_j:
                    # Constant Accel
                    j = 0
                    a = actual_a_max
                    dt = t - t_j
                    v_prev = 0.5 * max_jerk * t_j**2
                    v = v_prev + actual_a_max * dt
                else:
                    # Ramp Jerk Down
                    j = -max_jerk
                    t_from_end = t_a - t
                    # Mirror of ramp up, subtracted from peak
                    # Easier: Integrate backwards from v_peak? 
                    # Or: a = a_max - J * (t - (t_a - t_j))
                    dt = t - (t_a - t_j)
                    a = actual_a_max - max_jerk * dt
                    # Velocity is harder here. 
                    # Let's use the symmetry property: v(t) = v_peak - v(t_decel_counterpart)
                    # but we are in accel phase.
                    # Let's just integrate a: v = v_start_of_segment + a_prev*dt - 0.5*J*dt^2
                    v_start = 0.5 * max_jerk * t_j**2 + actual_a_max * (t_a - 2*t_j)
                    v = v_start + actual_a_max * dt - 0.5 * max_jerk * dt**2
                    
            # 2. Cruise Phase
            elif t < t_a + t_c:
                j = 0
                a = 0
                v = v_peak
                
            # 3. Deceleration Phase
            elif t <= profile['total_time'] + 0.001:
                t_curr = t - t_a - t_c
                # Symmetric to Accel phase, but velocity goes down
                # We can calculate "velocity removed" using the same logic as "velocity added"
                
                # Logic: Calculate v_profile(t_curr) as if we were accelerating, then subtract from v_peak
                if t_curr < t_j:
                    # Ramp Jerk (Negative)
                    j = -max_jerk
                    a = -max_jerk * t_curr
                    v_loss = 0.5 * max_jerk * t_curr**2
                elif t_curr < t_d - t_j:
                    # Constant Decel
                    j = 0
                    a = -actual_a_max
                    dt = t_curr - t_j
                    v_loss = 0.5 * max_jerk * t_j**2 + actual_a_max * dt
                else:
                    # Ramp Jerk (Positive) to 0
                    j = max_jerk
                    dt = t_curr - (t_d - t_j)
                    a = -actual_a_max + max_jerk * dt
                    v_start_loss = 0.5 * max_jerk * t_j**2 + actual_a_max * (t_d - 2*t_j)
                    v_loss = v_start_loss + actual_a_max * dt - 0.5 * max_jerk * dt**2
                    
                v = v_peak - v_loss
                
            generated_profile.append({
                'time': t,
                'velocity': max(0, min(max_speed, v)),
                'acceleration': a,
                'jerk': j
            })
            
    return generated_profile

def get_velocity_at_distance(distance, path_length, total_time, generated_profile):
    """Get velocity at a given distance along the path"""
    if not generated_profile or path_length <= 0:
        return 0
    
    # Map distance to time using the generated profile?
    # Since the profile is now generated based on exact distance, 
    # we can't just use ratio. We need to find the time t where integrated dist(t) = distance.
    # HOWEVER, for the simulation loop, we often pass "distance_traveled".
    
    # Simplification for simulation lookup:
    # Since we corrected the profile generation to match path_length exactly,
    # we can iterate through the profile to find the accumulated distance.
    
    # For O(1) lookup in simulation, it might be better to interpolate based on distance 
    # if we pre-calculated distance at every profile point.
    
    # For now, let's stick to the Time-Based lookup provided in the original code,
    # but we must ensure total_time is correct (which it now is).
    # But wait: "get_velocity_at_distance" uses Linear Interpolation on Time.
    # This assumes the robot tracks the trajectory perfectly in time.
    # A better approach for the controller is to find the profile point 
    # that corresponds to the current DISTANCE.
    
    current_dist = 0
    dt = generated_profile[1]['time'] - generated_profile[0]['time'] if len(generated_profile) > 1 else 0
    
    # Simple integration to find which time step matches 'distance'
    for i in range(len(generated_profile)):
        v = generated_profile[i]['velocity']
        current_dist += v * dt # Rectangle approximation
        if current_dist >= distance:
            return v
            
    return 0