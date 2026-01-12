// AI-Firewall Dashboard JavaScript
// WebSocket connection + Chart.js visualisaties

// Dynamic API URL based on current hostname
const API_HOST = window.location.hostname;
const API_PORT = '8000';
const API_URL = `http://${API_HOST}:${API_PORT}`;
const WS_URL = `ws://${API_HOST}:${API_PORT}/ws`;

let ws = null;
let charts = {};
let stats = {
    total: 0,
    benign: 0,
    malicious: 0,
    alerts: []
};

// Data voor time series
let timelineData = {
    labels: [],
    benign: [],
    malicious: []
};

let maxTimelinePoints = 50;

// Initialize charts
function initCharts() {
    // Flow Classification Pie Chart
    const flowCtx = document.getElementById('flowChart').getContext('2d');
    charts.flow = new Chart(flowCtx, {
        type: 'doughnut',
        data: {
            labels: ['Benign', 'Malicious'],
            datasets: [{
                data: [0, 0],
                backgroundColor: [
                    'rgba(0, 255, 136, 0.8)',
                    'rgba(255, 71, 87, 0.8)'
                ],
                borderColor: [
                    'rgba(0, 255, 136, 1)',
                    'rgba(255, 71, 87, 1)'
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    labels: {
                        color: '#fff',
                        font: {
                            size: 14
                        }
                    }
                }
            }
        }
    });
    
    // Timeline Chart
    const timelineCtx = document.getElementById('timelineChart').getContext('2d');
    charts.timeline = new Chart(timelineCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Benign',
                    data: [],
                    borderColor: 'rgba(0, 255, 136, 1)',
                    backgroundColor: 'rgba(0, 255, 136, 0.1)',
                    tension: 0.4,
                    fill: true
                },
                {
                    label: 'Malicious',
                    data: [],
                    borderColor: 'rgba(255, 71, 87, 1)',
                    backgroundColor: 'rgba(255, 71, 87, 0.1)',
                    tension: 0.4,
                    fill: true
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                x: {
                    ticks: { color: '#fff' },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' }
                },
                y: {
                    ticks: { color: '#fff' },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' },
                    beginAtZero: true
                }
            },
            plugins: {
                legend: {
                    labels: {
                        color: '#fff',
                        font: { size: 12 }
                    }
                }
            }
        }
    });
    
    // Risk Score Distribution
    const riskCtx = document.getElementById('riskChart').getContext('2d');
    charts.risk = new Chart(riskCtx, {
        type: 'bar',
        data: {
            labels: ['Low (0-0.3)', 'Medium (0.3-0.7)', 'High (0.7-1.0)'],
            datasets: [{
                label: 'Flow Count',
                data: [0, 0, 0],
                backgroundColor: [
                    'rgba(0, 255, 136, 0.6)',
                    'rgba(255, 193, 7, 0.6)',
                    'rgba(255, 71, 87, 0.6)'
                ],
                borderColor: [
                    'rgba(0, 255, 136, 1)',
                    'rgba(255, 193, 7, 1)',
                    'rgba(255, 71, 87, 1)'
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                x: {
                    ticks: { color: '#fff' },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' }
                },
                y: {
                    ticks: { color: '#fff' },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' },
                    beginAtZero: true
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
    
    // Protocol Distribution
    const protocolCtx = document.getElementById('protocolChart').getContext('2d');
    charts.protocol = new Chart(protocolCtx, {
        type: 'pie',
        data: {
            labels: ['TCP', 'UDP', 'ICMP', 'Other'],
            datasets: [{
                data: [0, 0, 0, 0],
                backgroundColor: [
                    'rgba(0, 212, 255, 0.8)',
                    'rgba(255, 193, 7, 0.8)',
                    'rgba(156, 39, 176, 0.8)',
                    'rgba(158, 158, 158, 0.8)'
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    labels: {
                        color: '#fff',
                        font: { size: 12 }
                    }
                }
            }
        }
    });
}

// Update stats display
function updateStatsDisplay() {
    document.getElementById('totalFlows').textContent = stats.total.toLocaleString();
    document.getElementById('benignCount').textContent = stats.benign.toLocaleString();
    document.getElementById('maliciousCount').textContent = stats.malicious.toLocaleString();
    
    const benignPct = stats.total > 0 ? (stats.benign / stats.total * 100).toFixed(1) : 0;
    const maliciousPct = stats.total > 0 ? (stats.malicious / stats.total * 100).toFixed(1) : 0;
    
    document.getElementById('benignPct').textContent = benignPct;
    document.getElementById('maliciousPct').textContent = maliciousPct;
    
    document.getElementById('lastUpdate').textContent = new Date().toLocaleTimeString();
    
    // Update flow chart
    charts.flow.data.datasets[0].data = [stats.benign, stats.malicious];
    charts.flow.update();
}

// Add data point to timeline
function addTimelinePoint(benignCount, maliciousCount) {
    const time = new Date().toLocaleTimeString();
    
    timelineData.labels.push(time);
    timelineData.benign.push(benignCount);
    timelineData.malicious.push(maliciousCount);
    
    // Keep only last N points
    if (timelineData.labels.length > maxTimelinePoints) {
        timelineData.labels.shift();
        timelineData.benign.shift();
        timelineData.malicious.shift();
    }
    
    charts.timeline.data.labels = timelineData.labels;
    charts.timeline.data.datasets[0].data = timelineData.benign;
    charts.timeline.data.datasets[1].data = timelineData.malicious;
    charts.timeline.update();
}

// Update risk chart
function updateRiskChart(score) {
    let index;
    if (score < 0.3) index = 0; // Low
    else if (score < 0.7) index = 1; // Medium
    else index = 2; // High
    
    charts.risk.data.datasets[0].data[index]++;
    charts.risk.update();
}

// Add alert
function addAlert(message, severity = 'high') {
    const alert = {
        time: new Date().toLocaleTimeString(),
        message: message,
        severity: severity
    };
    
    stats.alerts.unshift(alert);
    
    // Keep only last 50 alerts
    if (stats.alerts.length > 50) {
        stats.alerts.pop();
    }
    
    updateAlertsList();
}

// Update alerts list
function updateAlertsList() {
    const alertsList = document.getElementById('alertsList');
    
    if (stats.alerts.length === 0) {
        alertsList.innerHTML = '<p style="color: #888; text-align: center; padding: 20px;">Geen alerts op dit moment</p>';
        return;
    }
    
    alertsList.innerHTML = stats.alerts.map(alert => `
        <div class="alert-item">
            <div class="alert-time">${alert.time}</div>
            <div class="alert-message">${alert.message}</div>
        </div>
    `).join('');
}

// WebSocket connection
function connectWebSocket() {
    try {
        ws = new WebSocket(WS_URL);
        
        ws.onopen = () => {
            console.log('✅ WebSocket connected');
            document.getElementById('statusIndicator').classList.add('online');
            document.getElementById('statusIndicator').classList.remove('offline');
        };
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            handlePrediction(data);
        };
        
        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
        
        ws.onclose = () => {
            console.log('❌ WebSocket disconnected');
            document.getElementById('statusIndicator').classList.add('offline');
            document.getElementById('statusIndicator').classList.remove('online');
            
            // Reconnect after 5 seconds
            setTimeout(connectWebSocket, 5000);
        };
        
    } catch (error) {
        console.error('WebSocket connection failed:', error);
    }
}

// Handle prediction from WebSocket
function handlePrediction(data) {
    stats.total++;
    
    if (data.prediction === 'MALICIOUS') {
        stats.malicious++;
        addAlert(
            `🚨 Malicious flow detected! Score: ${data.ensemble_score.toFixed(3)} | Time: ${data.timestamp}`,
            'high'
        );
    } else {
        stats.benign++;
    }
    
    updateStatsDisplay();
    updateRiskChart(data.ensemble_score);
    
    // Update timeline every 10 flows
    if (stats.total % 10 === 0) {
        addTimelinePoint(stats.benign, stats.malicious);
    }
}

// Simulate demo data (voor testing zonder WebSocket)
function simulateDemoData() {
    setInterval(() => {
        const isMalicious = Math.random() < 0.05; // 5% malicious
        const score = isMalicious ? 0.7 + Math.random() * 0.3 : Math.random() * 0.3;
        
        handlePrediction({
            prediction: isMalicious ? 'MALICIOUS' : 'BENIGN',
            ensemble_score: score,
            timestamp: new Date().toISOString()
        });
    }, 1000); // Elke seconde een flow
}

// Control functions
function startMonitoring() {
    console.log('▶️ Starting monitoring...');
    connectWebSocket();
}

function stopMonitoring() {
    console.log('⏸️ Stopping monitoring...');
    if (ws) {
        ws.close();
    }
}

function resetStats() {
    if (confirm('Reset alle statistieken?')) {
        stats = { total: 0, benign: 0, malicious: 0, alerts: [] };
        timelineData = { labels: [], benign: [], malicious: [] };
        
        updateStatsDisplay();
        updateAlertsList();
        
        charts.risk.data.datasets[0].data = [0, 0, 0];
        charts.risk.update();
        
        console.log('🔄 Stats reset');
    }
}

function exportData() {
    const data = {
        stats: stats,
        timeline: timelineData,
        timestamp: new Date().toISOString()
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ai-firewall-export-${Date.now()}.json`;
    a.click();
    
    console.log('📊 Data exported');
}

// Check API health
async function checkApiHealth() {
    try {
        const response = await axios.get(`${API_URL}/health`);
        console.log('API Health:', response.data);
        return response.data.status === 'healthy';
    } catch (error) {
        console.error('API health check failed:', error);
        return false;
    }
}

// Initialize dashboard
async function init() {
    console.log('🚀 Initializing AI-Firewall Dashboard...');
    
    // Initialize charts
    initCharts();
    
    // Check API
    const apiHealthy = await checkApiHealth();
    
    if (apiHealthy) {
        console.log('✅ API is healthy - connecting WebSocket');
        // Probeer WebSocket te connecten
        connectWebSocket();
    } else {
        console.log('⚠️ API not available - using demo mode');
        // Only start demo mode when API is not available
        simulateDemoData();
    }
    
    console.log('✅ Dashboard initialized');
}

// Start when page loads
document.addEventListener('DOMContentLoaded', init);
