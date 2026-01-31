import { api } from './api.js';
import { FieldCanvas } from './canvas.js';
import { MotionGraph } from './graph.js';

class App {
    constructor() {
        this.field = new FieldCanvas('fieldCanvas', this.onPathUpdate.bind(this));
        this.graph = new MotionGraph('motionGraph');

        this.state = {
            trajectory: [],
            pathLength: 0,
            profile: [],
            isSimulating: false,
            simInterval: null,
            params: {
                kx: 1.5, ky: 3.0, ktheta: 2.0, startAngle: 0
            },
            profileConfig: {
                type: 'trapezoidal',
                maxVel: 60,
                maxAccel: 100,
                maxDecel: 100,
                maxJerk: 500
            }
        };

        this.bindControls();
    }

    bindControls() {
        // --- Path Controls ---
        document.getElementById('kxInput').addEventListener('change', (e) => this.state.params.kx = Number(e.target.value));
        document.getElementById('kyInput').addEventListener('change', (e) => this.state.params.ky = Number(e.target.value));
        document.getElementById('kthetaInput').addEventListener('change', (e) => this.state.params.ktheta = Number(e.target.value));
        document.getElementById('kthetaInput').addEventListener('change', (e) => this.state.params.ktheta = Number(e.target.value));
        document.getElementById('startAngleInput').addEventListener('change', (e) => this.state.params.startAngle = Number(e.target.value));

        // Lookahead Params
        // Add default values to state first if missing
        if (this.state.params.min_lookahead === undefined) {
            this.state.params.min_lookahead = 10.0;
            this.state.params.lookahead_gain = 0.1;
        }

        document.getElementById('minLookaheadInput').addEventListener('change', (e) => this.state.params.min_lookahead = Number(e.target.value));
        document.getElementById('lookaheadGainInput').addEventListener('change', (e) => this.state.params.lookahead_gain = Number(e.target.value));

        // new params for robot size
        // Function to update field size
        const updateRobotSize = () => {
            const w = Number(document.getElementById('robotWidthInput').value);
            const h = Number(document.getElementById('robotHeightInput').value);
            this.field.robotWidth = w;
            this.field.robotHeight = h;
            this.field.redraw();
        };

        document.getElementById('robotWidthInput').addEventListener('change', updateRobotSize);
        document.getElementById('robotHeightInput').addEventListener('change', updateRobotSize);
        document.getElementById('updateSizeBtn').addEventListener('click', updateRobotSize);

        // Point Editor
        const ptX = document.getElementById('ptX');
        const ptY = document.getElementById('ptY');

        const updatePoint = () => {
            if (this.field.selectedPoint !== -1) {
                const newX = Number(ptX.value);
                const newY = Number(ptY.value);
                this.field.controlPoints[this.field.selectedPoint] = { x: newX, y: newY };
                this.field.redraw();
                this.onPathUpdate();
            }
        };

        ptX.addEventListener('change', updatePoint);
        ptY.addEventListener('change', updatePoint);

        document.getElementById('clearPathBtn').addEventListener('click', () => {
            this.field.clear();
            this.onPathUpdate();
        });

        // --- Sim Controls ---
        document.getElementById('startSimBtn').addEventListener('click', () => this.startSimulation());
        document.getElementById('resetSimBtn').addEventListener('click', () => this.resetSimulation());

        // --- File Controls ---
        document.getElementById('savePathBtn').addEventListener('click', () => this.savePath());
        document.getElementById('loadPathBtn').addEventListener('click', () => document.getElementById('fileInput').click());
        document.getElementById('fileInput').addEventListener('change', (e) => this.loadPath(e));
        document.getElementById('uploadBgBtn').addEventListener('click', () => document.getElementById('bgInput').click());
        document.getElementById('bgInput').addEventListener('change', (e) => {
            if (e.target.files.length > 0) this.field.setBackground(e.target.files[0]);
        });

        // --- Motion Profile Controls ---
        document.querySelectorAll('input[name="profileType"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.state.profileConfig.type = e.target.value;
                document.querySelectorAll('.toggle-btn').forEach(btn => btn.classList.remove('active'));
                e.target.parentElement.classList.add('active');
                this.updateProfile();
            });
        });

        const bindSlider = (id, labelId, key) => {
            const slider = document.getElementById(id);
            const label = document.getElementById(labelId);
            slider.addEventListener('input', (e) => {
                label.innerText = Number(e.target.value).toFixed(1);
                this.state.profileConfig[key] = Number(e.target.value);
            });
            slider.addEventListener('change', () => this.updateProfile());
        };

        bindSlider('sliderMaxVel', 'valMaxVel', 'maxVel');
        bindSlider('sliderMaxAccel', 'valMaxAccel', 'maxAccel');
        bindSlider('sliderMaxDecel', 'valMaxDecel', 'maxDecel');
        bindSlider('sliderMaxJerk', 'valMaxJerk', 'maxJerk');

        document.getElementById('generateProfileBtn').addEventListener('click', () => this.updateProfile());

        this.initResizer();
    }

    initResizer() {
        const sidebar = document.querySelector('.sidebar');
        const resizer = document.getElementById('dragHandle');
        let isResizing = false;

        resizer.addEventListener('mousedown', (e) => {
            isResizing = true;
            resizer.classList.add('dragging');
            document.body.style.cursor = 'col-resize';
            e.preventDefault(); // Prevent text selection
        });

        document.addEventListener('mousemove', (e) => {
            if (!isResizing) return;

            // Limit width
            const newWidth = Math.max(250, Math.min(600, e.clientX));
            sidebar.style.width = `${newWidth}px`;

            // Update Canvas immediately for smoothness
            this.field.resize();
        });

        document.addEventListener('mouseup', () => {
            if (isResizing) {
                isResizing = false;
                resizer.classList.remove('dragging');
                document.body.style.cursor = '';
                // Final resize check
                this.field.resize();
            }
        });

        // Responsive Handler: Clear inline width on mobile to let CSS take over
        const checkResponsive = () => {
            if (window.innerWidth <= 768) {
                sidebar.style.width = '';
            }
        };

        window.addEventListener('resize', checkResponsive);
        checkResponsive(); // Run on init
    }
    async onPathUpdate() {
        if (this.field.controlPoints.length < 2) {
            this.field.setTrajectory([]);
            document.getElementById('pointCount').innerText = this.field.controlPoints.length;
            document.getElementById('pathLength').innerText = '0.0';
            return;
        }

        try {
            const data = await api.generatePath(this.field.controlPoints);
            this.state.trajectory = data.trajectory;
            this.state.pathLength = data.length;

            this.field.setTrajectory(data.trajectory);

            document.getElementById('pointCount').innerText = this.field.controlPoints.length;
            document.getElementById('pathLength').innerText = data.length.toFixed(1);

            // Update Point Editor UI
            const editorInfo = document.getElementById('pointEditor');
            const ptX = document.getElementById('ptX');
            const ptY = document.getElementById('ptY');

            if (this.field.selectedPoint !== -1 && this.field.controlPoints[this.field.selectedPoint]) {
                const pt = this.field.controlPoints[this.field.selectedPoint];
                ptX.value = pt.x.toFixed(1);
                ptY.value = pt.y.toFixed(1);
                editorInfo.style.opacity = '1';
                editorInfo.style.pointerEvents = 'all';
            } else {
                ptX.value = '';
                ptY.value = '';
                editorInfo.style.opacity = '0.3';
                editorInfo.style.pointerEvents = 'none';
            }

            this.updateProfile();
        } catch (e) {
            console.error("Failed to generate path", e);
        }
    }

    async updateProfile() {
        if (this.state.pathLength <= 0) return;

        try {
            const c = this.state.profileConfig;
            const data = await api.generateProfile(
                this.state.pathLength,
                c.type,
                c.maxVel,
                c.maxAccel,
                c.maxDecel,
                c.maxJerk
            );
            this.state.profile = data.profile;
            this.graph.update(data.profile);
        } catch (e) {
            console.error("Failed to generate profile", e);
        }
    }

    async startSimulation() {
        if (this.state.isSimulating) return; // Already running
        if (this.state.trajectory.length === 0) return;

        // Convert start angle to radians considering the LTV logic (0-deg=Up)
        // In the Python code, start_angle_deg was converted to radians directly.
        // We will pass [x, y, theta_rad] to the specialized startSim endpoint
        const startRad = this.state.params.startAngle * (Math.PI / 180.0);

        // Use the first point of the trajectory or control points?
        // Usually start at first control point.
        // But backend simulation.py expects robot_pose from start_pose arg.

        // NOTE: We should use the first control point.
        const startPt = this.field.controlPoints[0];
        const startPose = [startPt.x, startPt.y, startRad];

        try {
            await api.startSim(
                this.state.trajectory,
                this.state.profile,
                this.state.pathLength,
                this.state.params,
                startPose
            );

            this.field.reset();
            this.state.isSimulating = true;
            this.state.simInterval = setInterval(() => this.loop(), 1000 / 60); // 60 FPS

            document.getElementById('startSimBtn').innerHTML = '<span class="icon">⏸</span> Running...';
            document.getElementById('startSimBtn').classList.add('btn-success');
        } catch (e) {
            console.error("Failed to start sim", e);
        }
    }

    async loop() {
        if (!this.state.isSimulating) return;

        const data = await api.stepSim();
        if (!data.running) {
            this.stopSimulation();
            return;
        }

        const s = data.state;
        // s: {x, y, theta, velocity, acceleration, jerk, time}

        this.field.setRobotPose({ x: s.x, y: s.y, theta: s.theta });

        // Update Telemetry
        document.getElementById('telemV').innerText = s.velocity.toFixed(2);
        document.getElementById('telemA').innerText = s.acceleration.toFixed(2);
        document.getElementById('telemX').innerText = s.x.toFixed(1);
        document.getElementById('telemY').innerText = s.y.toFixed(1);
    }

    stopSimulation() {
        this.state.isSimulating = false;
        clearInterval(this.state.simInterval);
        document.getElementById('startSimBtn').innerHTML = '<span class="icon">▶</span> Start Sim';
        document.getElementById('startSimBtn').classList.remove('btn-success');
    }

    async resetSimulation() {
        this.stopSimulation();
        await api.resetSim();
        this.field.reset();

        // Reset robot to start
        if (this.field.controlPoints.length > 0) {
            const startPt = this.field.controlPoints[0];
            const startRad = this.state.params.startAngle * (Math.PI / 180.0);
            this.field.setRobotPose({ x: startPt.x, y: startPt.y, theta: startRad });
        }
    }

    async savePath() {
        const p = this.state.profileConfig;

        // Construct full legacy-compatible object
        const data = {
            metadata: {
                version: "1.2 (Web)",
                path_length: this.state.pathLength,
                profile_type: p.type
            },
            control_points: this.field.controlPoints,
            trajectory: this.state.trajectory, // Array of {x, y, theta, distance, velocity, curvature}
            motion_profile: {
                type: p.type,
                max_speed: p.maxVel,
                max_acceleration: p.maxAccel,
                max_deceleration: p.maxDecel,
                max_jerk: p.maxJerk,
                profile_points: this.state.profile // Array of {time, velocity, acceleration, jerk...}
            },
            params: this.state.params
        };

        const jsonStr = JSON.stringify(data, null, 2);

        try {
            // Check for 'Save As' support
            if (window.showSaveFilePicker) {
                const handle = await window.showSaveFilePicker({
                    suggestedName: 'path_data.json',
                    types: [{
                        description: 'JSON Files',
                        accept: { 'application/json': ['.json'] },
                    }],
                });
                const writable = await handle.createWritable();
                await writable.write(jsonStr);
                await writable.close();
            } else {
                // Fallback for browsers without File System Access API
                const blob = new Blob([jsonStr], { type: "application/json" });
                const link = document.createElement('a');
                link.href = URL.createObjectURL(blob);
                link.download = "path_data.json";
                link.click();
            }
        } catch (err) {
            // User cancelled or error
            if (err.name !== 'AbortError') {
                console.error('Save failed:', err);
            }
        }
    }

    loadPath(e) {
        const file = e.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (event) => {
            try {
                const data = JSON.parse(event.target.result);

                // Handle Legacy Format
                if (data.control_points) {
                    this.field.controlPoints = data.control_points;

                    if (data.motion_profile) {
                        const mp = data.motion_profile;
                        this.state.profileConfig = {
                            type: mp.type || 'trapezoidal',
                            maxVel: mp.max_speed || 60,
                            maxAccel: mp.max_acceleration || 100,
                            maxDecel: mp.max_deceleration || 100,
                            maxJerk: mp.max_jerk || 500
                        };
                    }
                    // Legacy doesn't store controller params, keep defaults or try to find them
                    console.log("Loaded legacy path format");
                }
                // Handle New Format
                else if (data.controlPoints) {
                    this.field.controlPoints = data.controlPoints;
                    this.state.params = data.params || this.state.params;
                    this.state.profileConfig = data.profileConfig || this.state.profileConfig;
                } else {
                    throw new Error("Unknown format");
                }

                // Update UI inputs
                document.getElementById('kxInput').value = this.state.params.kx;
                document.getElementById('kyInput').value = this.state.params.ky;
                document.getElementById('kthetaInput').value = this.state.params.ktheta;
                document.getElementById('startAngleInput').value = this.state.params.startAngle;

                // Update Profile UI
                const p = this.state.profileConfig;
                document.getElementById('sliderMaxVel').value = p.maxVel;
                document.getElementById('valMaxVel').innerText = p.maxVel.toFixed(1);

                document.getElementById('sliderMaxAccel').value = p.maxAccel;
                document.getElementById('valMaxAccel').innerText = p.maxAccel.toFixed(1);

                document.getElementById('sliderMaxDecel').value = p.maxDecel;
                document.getElementById('valMaxDecel').innerText = p.maxDecel.toFixed(1);

                document.getElementById('sliderMaxJerk').value = p.maxJerk;
                document.getElementById('valMaxJerk').innerText = p.maxJerk.toFixed(1);

                // Update Radio
                const radio = document.querySelector(`input[name="profileType"][value="${p.type}"]`);
                if (radio) {
                    radio.checked = true;
                    // Update visual toggle state
                    document.querySelectorAll('.toggle-btn').forEach(btn => btn.classList.remove('active'));
                    radio.parentElement.classList.add('active');
                }

                // Trigger updates
                this.field.redraw();
                this.onPathUpdate();

            } catch (err) {
                console.error("Load failed", err);
                alert("Invalid file format");
            }
        };
        reader.readAsText(file);
    }
}

// Init
window.addEventListener('DOMContentLoaded', () => {
    window.app = new App();
});
