// AI-Firewall Dashboard with Blocking Management
// Real-time monitoring and IP management

const API_BASE = window.location.hostname === 'localhost' 
    ? 'http://localhost:8000' 
    : '/api';

let ws = null;
let charts = {};
let stats = {
    totalFlows: 0,
    benignFlows: 0,
    maliciousFlows: 0,
    blockedCount: 0
};

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    initCharts();
    connectWebSocket();
    loadBlockedIPs();
    loadFirewallStats();
    
    // Auto-refresh every 30 seconds
    setInterval(() => {
        if (document.getElementById('blocked-tab').classList.contains('active')) {
            loadBlockedIPs();
        }
    }, 30000);
});

// Tab Management
function showTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab
    document.getElementById(`${tabName}-tab`).classList.add('active');
    event.target.classList.add('active');
    
    // Load data for specific tabs
    if (tabName === 'blocked') {
        loadBlockedIPs();
    } else if (tabName === 'logs') {
        loadLogs();
    } else if (tabName === 'settings') {
        loadSettings();
    }
}

// Initialize Charts
function initCharts() {
    // Classification Pie Chart
    const classCtx = document.getElementById('classificationChart').getContext('2d');
    charts.classification = new Chart(classCtx, {
        type: 'doughnut',
        data: {
            labels: ['Benign', 'Malicious'],
            datasets: [{
                data: [0, 0],
                backgroundColor: ['#10b981', '#ef4444']
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });

    // Timeline Chart
    const timeCtx = document.getElementById('timelineChart').getContext('2d');
    charts.timeline = new Chart(timeCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Benign',
                    data: [],
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    fill: true
                },
                {
                    label: 'Malicious',
                    data: [],
                    borderColor: '#ef4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    fill: true
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// WebSocket Connection
function connectWebSocket() {
    const wsUrl = `ws://${window.location.hostname}:8000/ws`;
    
    ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
        console.log('WebSocket connected');
        updateStatus('connected');
    };
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handlePrediction(data);
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        updateStatus('error');
    };
    
    ws.onclose = () => {
        console.log('WebSocket closed');
        updateStatus('disconnected');
        
        // Reconnect after 5 seconds
        setTimeout(connectWebSocket, 5000);
    };
}

// Update Status Badge
function updateStatus(status) {
    const badge = document.getElementById('statusBadge');
    const text = document.getElementById('statusText');
    
    badge.className = 'status-badge ' + status;
    
    const statusTexts = {
        'connected': 'Connected',
        'disconnected': 'Disconnected',
        'error': 'Error'
    };
    
    text.textContent = statusTexts[status] || status;
}

// Handle Prediction
function handlePrediction(data) {
    stats.totalFlows++;
    
    if (data.prediction === 'benign') {
        stats.benignFlows++;
    } else {
        stats.maliciousFlows++;
        
        // Show alert for malicious
        showAlert(data);
    }
    
    // Update UI
    updateStats();
    updateCharts();
}

// Update Stats
function updateStats() {
    document.getElementById('totalFlows').textContent = stats.totalFlows;
    document.getElementById('benignFlows').textContent = stats.benignFlows;
    document.getElementById('maliciousFlows').textContent = stats.maliciousFlows;
}

// Update Charts
function updateCharts() {
    // Update pie chart
    charts.classification.data.datasets[0].data = [
        stats.benignFlows,
        stats.maliciousFlows
    ];
    charts.classification.update();
    
    // Update timeline
    const now = new Date().toLocaleTimeString();
    charts.timeline.data.labels.push(now);
    charts.timeline.data.datasets[0].data.push(stats.benignFlows);
    charts.timeline.data.datasets[1].data.push(stats.maliciousFlows);
    
    // Keep last 20 points
    if (charts.timeline.data.labels.length > 20) {
        charts.timeline.data.labels.shift();
        charts.timeline.data.datasets[0].data.shift();
        charts.timeline.data.datasets[1].data.shift();
    }
    
    charts.timeline.update();
}

// Load Blocked IPs
async function loadBlockedIPs() {
    try {
        const response = await fetch(`${API_BASE}/blocked-ips`);
        const data = await response.json();
        
        if (data.status === 'success') {
            displayBlockedIPs(data.blocked_ips);
            updateBlockedStats(data);
        }
    } catch (error) {
        console.error('Error loading blocked IPs:', error);
    }
}

// Display Blocked IPs Table
function displayBlockedIPs(blockedIPs) {
    const tbody = document.getElementById('blockedTableBody');
    
    if (blockedIPs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="no-data">No blocked IPs</td></tr>';
        return;
    }
    
    tbody.innerHTML = blockedIPs.map(item => {
        const blockedTime = new Date(item.blocked_at);
        const expiresAt = new Date(blockedTime.getTime() + item.duration_hours * 60 * 60 * 1000);
        const timeLeft = Math.max(0, Math.floor((expiresAt - new Date()) / (1000 * 60 * 60)));
        
        return `
            <tr>
                <td><code>${item.ip}</code></td>
                <td>${blockedTime.toLocaleString()}</td>
                <td>${item.reason}</td>
                <td><span class="method-badge ${item.method}">${item.method}</span></td>
                <td>${timeLeft}h</td>
                <td>
                    <button class="unblock-btn" onclick="unblockIP('${item.ip}')">🔓 Unblock</button>
                </td>
            </tr>
        `;
    }).join('');
}

// Update Blocked Stats
function updateBlockedStats(data) {
    document.getElementById('totalBlocked').textContent = data.total;
    document.getElementById('blockedCount').textContent = data.total;
    document.getElementById('autoBlockStatus').textContent = 
        data.auto_block_enabled ? 'Enabled' : 'Disabled';
    document.getElementById('blockThreshold').textContent = data.threshold;
    
    stats.blockedCount = data.total;
}

// Refresh Blocked IPs
function refreshBlockedIPs() {
    loadBlockedIPs();
    showNotification('Blocked IPs refreshed', 'success');
}

// Unblock IP
async function unblockIP(ip) {
    if (!confirm(`Unblock IP ${ip}?`)) return;
    
    try {
        const response = await fetch(`${API_BASE}/unblock/${ip}`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            showNotification(`IP ${ip} unblocked successfully`, 'success');
            loadBlockedIPs();
        } else {
            showNotification(`Failed to unblock IP ${ip}`, 'error');
        }
    } catch (error) {
        console.error('Error unblocking IP:', error);
        showNotification('Error unblocking IP', 'error');
    }
}

// Load Firewall Stats
async function loadFirewallStats() {
    try {
        const response = await fetch(`${API_BASE}/firewall/stats`);
        const data = await response.json();
        
        if (data.status === 'success') {
            stats.blockedCount = data.stats.total_blocked;
            document.getElementById('blockedCount').textContent = data.stats.total_blocked;
        }
    } catch (error) {
        console.error('Error loading firewall stats:', error);
    }
}

// Load Logs
async function loadLogs() {
    try {
        const response = await fetch(`${API_BASE}/logs/blocked?limit=100`);
        const data = await response.json();
        
        if (data.status === 'success') {
            displayLogs(data.logs);
        }
    } catch (error) {
        console.error('Error loading logs:', error);
    }
}

// Display Logs
function displayLogs(logs) {
    const container = document.getElementById('logsContainer');
    
    if (logs.length === 0) {
        container.innerHTML = '<div class="log-entry">No blocking history available</div>';
        return;
    }
    
    container.innerHTML = logs.map(log => {
        const timestamp = new Date(log.timestamp).toLocaleString();
        return `
            <div class="log-entry">
                <div class="log-time">${timestamp}</div>
                <div class="log-ip"><code>${log.ip}</code></div>
                <div class="log-reason">${log.reason}</div>
                <div class="log-method"><span class="method-badge ${log.method}">${log.method}</span></div>
            </div>
        `;
    }).join('');
}

// Refresh Logs
function refreshLogs() {
    loadLogs();
    showNotification('Logs refreshed', 'success');
}

// Load Settings
function loadSettings() {
    // Load from API or localStorage
    const autoBlock = localStorage.getItem('autoBlock') === 'true';
    const threshold = parseFloat(localStorage.getItem('threshold') || '0.7');
    const duration = parseInt(localStorage.getItem('blockDuration') || '24');
    
    document.getElementById('autoBlockToggle').checked = autoBlock;
    document.getElementById('thresholdSlider').value = threshold;
    document.getElementById('thresholdValue').textContent = threshold;
    document.getElementById('blockDuration').value = duration;
}

// Toggle Auto-Block
function toggleAutoBlock() {
    const enabled = document.getElementById('autoBlockToggle').checked;
    localStorage.setItem('autoBlock', enabled);
    showNotification(`Auto-block ${enabled ? 'enabled' : 'disabled'}`, 'success');
}

// Update Threshold
function updateThreshold(value) {
    document.getElementById('thresholdValue').textContent = value;
    localStorage.setItem('threshold', value);
}

// Update Block Duration
function updateBlockDuration(value) {
    localStorage.setItem('blockDuration', value);
    showNotification(`Block duration updated to ${value} hours`, 'success');
}

// Save Whitelist
function saveWhitelist() {
    const whitelist = document.getElementById('whitelistIPs').value;
    localStorage.setItem('whitelist', whitelist);
    showNotification('Whitelist saved', 'success');
}

// Show Alert
function showAlert(data) {
    const alert = document.createElement('div');
    alert.className = 'alert alert-danger';
    alert.innerHTML = `
        <strong>🚨 Threat Detected!</strong><br>
        Score: ${(data.ensemble_score * 100).toFixed(1)}%<br>
        ${data.was_blocked ? '🚫 IP Blocked' : 'ℹ️ Monitoring Only'}
    `;
    
    const container = document.getElementById('alertsContainer');
    container.appendChild(alert);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        alert.remove();
    }, 5000);
}

// Show Notification
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add('show');
    }, 100);
    
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}
