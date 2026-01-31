export class FieldCanvas {
    constructor(canvasId, onUpdate) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.onUpdate = onUpdate;

        // Field Properties
        this.fieldMin = -72;
        this.fieldMax = 72;
        this.fieldSize = 144;

        // State
        this.controlPoints = [];
        this.trajectory = [];
        this.robotPose = { x: 0, y: 0, theta: 0 };
        this.robotTrace = [];
        this.robotWidth = 15;
        this.robotHeight = 15;

        // Interaction
        this.selectedPoint = -1;
        this.isDragging = false;

        this.bgImage = null;

        // Bind events
        this.resize();
        window.addEventListener('resize', () => this.resize());

        this.canvas.addEventListener('mousedown', this.onMouseDown.bind(this));
        this.canvas.addEventListener('mousemove', this.onMouseMove.bind(this));
        this.canvas.addEventListener('mouseup', this.onMouseUp.bind(this));
        this.canvas.addEventListener('contextmenu', (e) => e.preventDefault()); // Prevent menu
    }

    resize() {
        const parent = this.canvas.parentElement;
        const size = Math.min(parent.clientWidth, parent.clientHeight);
        this.canvas.width = size;
        this.canvas.height = size;
        this.redraw();
    }

    // Coordinate Transforms
    fieldToPixel(fx, fy) {
        const size = this.canvas.width; // Square canvas
        // (fx - min) / size * pixelSize
        const normX = (fx - this.fieldMin) / this.fieldSize;
        const normY = (fy - this.fieldMin) / this.fieldSize;

        // Flip Y for standard coordinates if needed? 
        // Original Kivy code: field_min at bottom-left? 
        // Validated against Kivy code: 
        // norm_y = (py - self.y) / size -> py is from bottom up in Kivy.
        // In HTML Canvas, Y is top-down. 
        // So we need to INVERT normY for rendering.

        const px = normX * size;
        const py = size - (normY * size);
        return { x: px, y: py };
    }

    pixelToField(px, py) {
        const size = this.canvas.width;
        const normX = px / size;
        const normY = (size - py) / size; // Invert back

        const fx = this.fieldMin + normX * this.fieldSize;
        const fy = this.fieldMin + normY * this.fieldSize;
        return { x: fx, y: fy };
    }

    // Drawing
    redraw() {
        const w = this.canvas.width;
        const h = this.canvas.height;
        this.ctx.clearRect(0, 0, w, h);

        this.drawBackground();
        this.drawGrid();
        this.drawRobotTrace();
        this.drawTrajectory();
        this.drawControlPoints();
        this.drawRobot();
    }

    drawBackground() {
        if (this.bgImage) {
            this.ctx.drawImage(this.bgImage, 0, 0, this.canvas.width, this.canvas.height);
        }
    }

    drawGrid() {
        const ctx = this.ctx;
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
        ctx.lineWidth = 1;

        const gridSpacing = 24; // 24 units (inches?)
        // fieldMin = -72, fieldMax = 72

        for (let i = -3; i <= 3; i++) {
            const coord = i * gridSpacing;

            // Vertical lines
            let p1 = this.fieldToPixel(coord, this.fieldMin);
            let p2 = this.fieldToPixel(coord, this.fieldMax);
            ctx.beginPath();
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.stroke();

            // Horizontal lines
            p1 = this.fieldToPixel(this.fieldMin, coord);
            p2 = this.fieldToPixel(this.fieldMax, coord);
            ctx.beginPath();
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.stroke();
        }

        // Axes
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
        ctx.lineWidth = 2;

        // X-Axis
        let p1 = this.fieldToPixel(0, this.fieldMin);
        let p2 = this.fieldToPixel(0, this.fieldMax);
        ctx.beginPath();
        ctx.moveTo(p1.x, p1.y);
        ctx.lineTo(p2.x, p2.y);
        ctx.stroke();

        // Y-Axis
        p1 = this.fieldToPixel(this.fieldMin, 0);
        p2 = this.fieldToPixel(this.fieldMax, 0);
        ctx.beginPath();
        ctx.moveTo(p1.x, p1.y);
        ctx.lineTo(p2.x, p2.y);
        ctx.stroke();
    }

    drawControlPoints() {
        const ctx = this.ctx;

        // Draw lines between handles and anchors
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
        ctx.lineWidth = 1;
        ctx.setLineDash([5, 5]);

        for (let i = 0; i < this.controlPoints.length - 1; i++) {
            // Only draw handle lines (Anchor -> Handle)
            if (i % 3 === 0 && (i + 1) < this.controlPoints.length) {
                const p1 = this.fieldToPixel(this.controlPoints[i].x, this.controlPoints[i].y);
                const p2 = this.fieldToPixel(this.controlPoints[i + 1].x, this.controlPoints[i + 1].y);
                ctx.beginPath();
                ctx.moveTo(p1.x, p1.y);
                ctx.lineTo(p2.x, p2.y);
                ctx.stroke();
            }
            if (i % 3 === 1 && (i + 1) < this.controlPoints.length) {
                // p1 is handle, p2 is anchor? No. 
                // 0(A) - 1(H) ... 2(H) - 3(A)
            }
            // Draw all connections slightly
            const p1 = this.fieldToPixel(this.controlPoints[i].x, this.controlPoints[i].y);
            const p2 = this.fieldToPixel(this.controlPoints[i + 1].x, this.controlPoints[i + 1].y);
            ctx.beginPath();
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.stroke();
        }

        ctx.setLineDash([]);

        // Points
        this.controlPoints.forEach((pt, i) => {
            const p = this.fieldToPixel(pt.x, pt.y);
            ctx.beginPath();

            if (i % 3 === 0) {
                // Anchor
                ctx.fillStyle = '#8052ff';
                ctx.arc(p.x, p.y, 6, 0, Math.PI * 2);
            } else {
                // Handle
                ctx.fillStyle = '#6642cc';
                ctx.arc(p.x, p.y, 4, 0, Math.PI * 2);
            }
            ctx.fill();

            if (i === this.selectedPoint) {
                ctx.strokeStyle = 'white';
                ctx.lineWidth = 2;
                ctx.stroke();
            }
        });
    }

    drawTrajectory() {
        if (!this.trajectory || this.trajectory.length < 2) return;

        const ctx = this.ctx;
        ctx.strokeStyle = '#2daddf';
        ctx.lineWidth = 3;
        ctx.beginPath();

        const start = this.fieldToPixel(this.trajectory[0].x, this.trajectory[0].y);
        ctx.moveTo(start.x, start.y);

        for (let i = 1; i < this.trajectory.length; i++) {
            const p = this.fieldToPixel(this.trajectory[i].x, this.trajectory[i].y);
            ctx.lineTo(p.x, p.y);
        }
        ctx.stroke();
    }

    drawRobotTrace() {
        if (this.robotTrace.length < 2) return;
        const ctx = this.ctx;
        ctx.strokeStyle = 'rgba(255, 100, 50, 0.6)';
        ctx.lineWidth = 2;
        ctx.beginPath();
        const start = this.fieldToPixel(this.robotTrace[0].x, this.robotTrace[0].y);
        ctx.moveTo(start.x, start.y);
        for (let pt of this.robotTrace) {
            const p = this.fieldToPixel(pt.x, pt.y);
            ctx.lineTo(p.x, p.y);
        }
        ctx.stroke();
    }

    drawRobot() {
        const ctx = this.ctx;
        const p = this.fieldToPixel(this.robotPose.x, this.robotPose.y);

        // Robot Dimensions
        const scalar = this.canvas.width / this.fieldSize;
        const pxW = this.robotWidth * scalar;
        const pxH = this.robotHeight * scalar;

        const theta = this.robotPose.theta;

        ctx.save();
        ctx.translate(p.x, p.y);
        ctx.rotate(theta);

        // Body
        ctx.fillStyle = '#ff3366';
        ctx.strokeStyle = '#ff0044';
        ctx.lineWidth = 2;

        // Draw centered rectangle
        ctx.beginPath();
        ctx.rect(-pxW / 2, -pxH / 2, pxW, pxH);
        ctx.fill();
        ctx.stroke();

        // Heading Line (Front Indicator)
        ctx.strokeStyle = '#00ffaa';
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.lineTo(0, -pxH / 2);
        ctx.stroke();

        ctx.restore();
    }

    // Input Handling
    onMouseDown(e) {
        const rect = this.canvas.getBoundingClientRect();
        const mouseX = e.clientX - rect.left;
        const mouseY = e.clientY - rect.top;

        // Hit Test
        let clickedIndex = -1;
        for (let i = 0; i < this.controlPoints.length; i++) {
            const p = this.fieldToPixel(this.controlPoints[i].x, this.controlPoints[i].y);
            const dist = Math.hypot(p.x - mouseX, p.y - mouseY);
            if (dist < 10) {
                clickedIndex = i;
                break;
            }
        }

        if (e.button === 2) { // Right Click - Delete
            if (clickedIndex !== -1) {
                this.controlPoints.splice(clickedIndex, 1);
                this.selectedPoint = -1;
                this.onUpdate();
                this.redraw();
            }
            return;
        }

        if (clickedIndex !== -1) {
            this.selectedPoint = clickedIndex;
            this.isDragging = true;
            this.onUpdate();
        } else {
            // Add Point
            const fieldPt = this.pixelToField(mouseX, mouseY);
            // Clamp
            fieldPt.x = Math.max(this.fieldMin, Math.min(this.fieldMax, fieldPt.x));
            fieldPt.y = Math.max(this.fieldMin, Math.min(this.fieldMax, fieldPt.y));

            this.controlPoints.push(fieldPt);
            this.selectedPoint = this.controlPoints.length - 1;
            this.onUpdate();
        }
        this.redraw();
    }

    onMouseMove(e) {
        if (!this.isDragging || this.selectedPoint === -1) return;

        const rect = this.canvas.getBoundingClientRect();
        const mouseX = e.clientX - rect.left;
        const mouseY = e.clientY - rect.top;

        const fieldPt = this.pixelToField(mouseX, mouseY);
        // Clamp
        fieldPt.x = Math.max(this.fieldMin, Math.min(this.fieldMax, fieldPt.x));
        fieldPt.y = Math.max(this.fieldMin, Math.min(this.fieldMax, fieldPt.y));

        this.controlPoints[this.selectedPoint] = fieldPt;
        this.redraw();
        // Debounce update? For now direct call
        this.onUpdate();
    }

    onMouseUp() {
        this.isDragging = false;
    }

    setTrajectory(traj) {
        this.trajectory = traj;
        this.redraw();
    }

    setRobotPose(pose) {
        this.robotPose = pose;
        this.robotTrace.push({ x: pose.x, y: pose.y });
        this.redraw();
    }

    reset() {
        this.robotTrace = [];
        this.redraw();
    }

    clear() {
        this.controlPoints = [];
        this.trajectory = [];
        this.robotTrace = [];
        this.redraw();
    }

    setBackground(file) {
        const img = new Image();
        img.onload = () => {
            this.bgImage = img;
            this.redraw();
        };
        img.src = URL.createObjectURL(file);
    }
}
