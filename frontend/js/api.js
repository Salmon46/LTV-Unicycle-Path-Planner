const API_BASE = '/api';

export const api = {
    async generatePath(controlPoints) {
        const response = await fetch(`${API_BASE}/path/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ control_points: controlPoints })
        });
        return await response.json();
    },

    async generateProfile(pathLength, type, maxVel, maxAccel, maxDecel, maxJerk) {
        const response = await fetch(`${API_BASE}/motion/profile`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                path_length: pathLength,
                type: type,
                max_vel: Number(maxVel),
                max_accel: Number(maxAccel),
                max_decel: Number(maxDecel),
                max_jerk: Number(maxJerk)
            })
        });
        return await response.json();
    },

    async startSim(trajectory, profile, pathLength, params, startPose) {
        const response = await fetch(`${API_BASE}/sim/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                trajectory: trajectory,
                profile: profile,
                path_length: pathLength,
                params: params,
                start_pose: startPose
            })
        });
        return await response.json();
    },

    async stepSim() {
        try {
            const response = await fetch(`${API_BASE}/sim/step`, {
                method: 'POST',
            });
            return await response.json();
        } catch (e) {
            console.error("Sim step failed", e);
            return { running: false };
        }
    },

    async resetSim() {
        await fetch(`${API_BASE}/sim/reset`, { method: 'POST' });
    }
};
