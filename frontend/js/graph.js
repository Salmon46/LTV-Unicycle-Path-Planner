export class MotionGraph {
    constructor(canvasId) {
        this.ctx = document.getElementById(canvasId).getContext('2d');
        this.chart = new Chart(this.ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Velocity',
                        data: [],
                        borderColor: '#2daddf', // Secondary Blue
                        backgroundColor: 'rgba(45, 173, 223, 0.1)',
                        borderWidth: 2,
                        tension: 0.1,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Acceleration',
                        data: [],
                        borderColor: '#ff9045', // Orange
                        borderWidth: 1.5,
                        tension: 0.1,
                        hidden: true,
                        yAxisID: 'y1'
                    },
                    {
                        label: 'Jerk',
                        data: [],
                        borderColor: '#ff3366', // Pink
                        borderWidth: 1.5,
                        tension: 0.1,
                        hidden: true,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                scales: {
                    x: {
                        type: 'linear',
                        grid: { color: 'rgba(255,255,255,0.05)' },
                        ticks: { color: '#9494a0' }
                    },
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        grid: { color: 'rgba(255,255,255,0.05)' },
                        ticks: { color: '#9494a0' },
                        title: { display: true, text: 'Velocity' }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        grid: { drawOnChartArea: false },
                        ticks: { color: '#9494a0' },
                        title: { display: true, text: 'Accel / Jerk' }
                    }
                },
                plugins: {
                    legend: {
                        labels: { color: '#e6e6f0' }
                    }
                }
            }
        });
    }

    update(profilePoints) {
        if (!profilePoints || profilePoints.length === 0) return;

        // Downsample if too many points for performance
        const maxPoints = 200;
        const step = Math.ceil(profilePoints.length / maxPoints);

        const labels = [];
        const velData = [];
        const accelData = [];
        const jerkData = [];

        for (let i = 0; i < profilePoints.length; i += step) {
            const p = profilePoints[i];
            labels.push(p.time); // Use actual time for x-axis
            velData.push({ x: p.time, y: p.velocity });
            accelData.push({ x: p.time, y: p.acceleration });
            jerkData.push({ x: p.time, y: p.jerk });
        }

        this.chart.data.labels = labels;
        this.chart.data.datasets[0].data = velData;
        this.chart.data.datasets[1].data = accelData;
        this.chart.data.datasets[2].data = jerkData;

        this.chart.update();
    }

    toggleDataset(index, visible) {
        this.chart.getDatasetMeta(index).hidden = !visible;
        this.chart.update();
    }
}
