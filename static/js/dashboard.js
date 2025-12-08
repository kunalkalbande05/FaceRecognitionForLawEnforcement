// dashboard.js - SIMPLIFIED WITH DUMMY DATA
let socket = null;

document.addEventListener('DOMContentLoaded', function() {
    console.log("🚀 Dashboard loaded");
    initializeApp();
});

function initializeApp() {
    socket = io();
    setupSocketEvents();
    setupEventListeners();
    loadDashboardData();
}

function setupSocketEvents() {
    socket.on('connect', function() {
        console.log("✅ Connected to server");
    });

    // FIXED: Listen for 'alert' event instead of 'real_match_detected'
    socket.on('alert', function(data) {
        console.log("🔔 ALERT RECEIVED:", data);
        showAlertNotification(data);
    });

    socket.on('scan_started', function(data) {
        showToast(data.message, 'success');
        updateScanStatus(true);
    });

    socket.on('scan_stopped', function(data) {
        showToast(data.message, 'info');
        updateScanStatus(false);
    });

    socket.on('scan_error', function(data) {
        showToast(data.message, 'error');
        updateScanStatus(false);
    });
}

function setupEventListeners() {
    // Navigation
    document.querySelectorAll('.sidebar-menu a[data-section]').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const sectionId = link.getAttribute('data-section');
            
            // Update active link
            document.querySelectorAll('.sidebar-menu a').forEach(l => l.classList.remove('active'));
            link.classList.add('active');
            
            // Show section
            document.querySelectorAll('.dashboard-section').forEach(section => {
                section.style.display = 'none';
            });
            document.getElementById(sectionId).style.display = 'block';
            
            // Update title
            document.getElementById('dashboardTitle').textContent = link.textContent;
        });
    });

    // Camera controls
    const startBtn = document.getElementById('startScanBtn');
    const stopBtn = document.getElementById('stopScanBtn');
    
    if (startBtn) {
        startBtn.addEventListener('click', function() {
            this.disabled = true;
            this.innerHTML = '<div class="spinner"></div> Starting...';
            socket.emit('start_scan', {});
        });
    }
    
    if (stopBtn) {
        stopBtn.addEventListener('click', function() {
            socket.emit('stop_scan');
        });
    }

    // Criminal form
    const criminalForm = document.getElementById('criminalForm');
    if (criminalForm) {
        criminalForm.addEventListener('submit', handleCriminalSubmit);
    }

    // File upload
    const fileInput = document.getElementById('criminalImage');
    const uploadArea = document.getElementById('uploadArea');
    
    if (fileInput && uploadArea) {
        uploadArea.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file && file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const preview = document.getElementById('previewImage');
                    const container = document.getElementById('imagePreview');
                    if (preview && container) {
                        preview.src = e.target.result;
                        container.style.display = 'block';
                    }
                };
                reader.readAsDataURL(file);
            }
        });
    }
}

function loadDashboardData() {
    console.log("📊 Loading dashboard data...");
    
    // Use dummy data for stats
    updateStatsDisplay({
        criminal_count: 3,
        matches_today: 1,
        pending_verifications: 0,
        system_accuracy: 85.0
    });
    
    // Load empty alerts and matches
    displayAlerts([]);
    displayMatches([]);
    
    console.log("✅ Dashboard data loaded successfully");
}

function updateStatsDisplay(stats) {
    document.getElementById('statCriminals').textContent = stats.criminal_count;
    document.getElementById('statMatchesToday').textContent = stats.matches_today;
    document.getElementById('statPending').textContent = stats.pending_verifications;
    document.getElementById('statAccuracy').textContent = stats.system_accuracy + '%';
}

function displayAlerts(alerts) {
    const containers = ['alertsContainer', 'alertsPageContainer'];
    
    containers.forEach(containerId => {
        const container = document.getElementById(containerId);
        if (!container) return;

        if (alerts.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-bell-slash"></i>
                    <h3>No Alerts</h3>
                    <p>No alerts at this time. Alerts will appear here when matches are detected.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = alerts.map(alert => `
            <div class="alert alert-warning">
                <i class="fas fa-bell alert-icon"></i>
                <div class="alert-content">
                    <strong>${alert.message}</strong>
                    <p style="margin: 5px 0 0 0; font-size: 0.9rem; color: #666;">
                        ${new Date(alert.created_at).toLocaleString()}
                    </p>
                </div>
            </div>
        `).join('');
    });
}

function displayMatches(matches) {
    const containers = ['matchesContainer', 'matchesHistoryContainer'];
    
    containers.forEach(containerId => {
        const container = document.getElementById(containerId);
        if (!container) return;

        if (matches.length === 0) {
            container.innerHTML = `
                <tr>
                    <td colspan="6" style="text-align: center; padding: 40px;">
                        <div class="empty-state">
                            <i class="fas fa-history"></i>
                            <h3>No Match History</h3>
                            <p>No facial recognition matches found yet.</p>
                        </div>
                    </td>
                </tr>
            `;
            return;
        }

        container.innerHTML = matches.map(match => `
            <tr>
                <td>${new Date(match.timestamp).toLocaleString()}</td>
                <td>${match.criminal_name || 'Unknown'}</td>
                <td>Camera</td>
                <td>${match.confidence}%</td>
                <td><span class="status-badge status-${match.status || 'pending'}">${match.status || 'pending'}</span></td>
                <td>System</td>
            </tr>
        `).join('');
    });
}

function showAlertNotification(alertData) {
    console.log("🔄 Showing alert notification:", alertData);
    
    // Show toast notification
    showToast(`🚨 ${alertData.criminal_name} detected - ${alertData.confidence}%`, 'warning');
    
    // Update alert badge
    const badgeCount = document.getElementById('badgeCount');
    if (badgeCount) {
        const currentCount = parseInt(badgeCount.textContent) || 0;
        badgeCount.textContent = currentCount + 1;
        badgeCount.style.display = 'flex';
        
        // Pulse animation
        const alertBadge = document.getElementById('alertBadge');
        if (alertBadge) {
            alertBadge.classList.add('pulse');
            setTimeout(() => alertBadge.classList.remove('pulse'), 2000);
        }
    }
    
    // Create a new alert in the UI
    const newAlert = {
        message: `🚨 ${alertData.criminal_name} detected - ${alertData.confidence}%`,
        created_at: new Date().toISOString()
    };
    
    // Add to alerts containers
    const containers = ['alertsContainer', 'alertsPageContainer'];
    containers.forEach(containerId => {
        const container = document.getElementById(containerId);
        if (container) {
            const emptyState = container.querySelector('.empty-state');
            if (emptyState) {
                emptyState.remove();
            }
            
            const alertHTML = `
                <div class="alert alert-warning">
                    <i class="fas fa-bell alert-icon"></i>
                    <div class="alert-content">
                        <strong>${newAlert.message}</strong>
                        <p style="margin: 5px 0 0 0; font-size: 0.9rem; color: #666;">
                            ${new Date(newAlert.created_at).toLocaleString()}
                        </p>
                    </div>
                </div>
            `;
            
            container.insertAdjacentHTML('afterbegin', alertHTML);
        }
    });
}

async function handleCriminalSubmit(e) {
    e.preventDefault();
    
    const formData = new FormData();
    const imageFile = document.getElementById('criminalImage').files[0];
    
    if (!imageFile) {
        showToast('Please select an image', 'error');
        return;
    }
    
    formData.append('image', imageFile);
    formData.append('criminal_id', document.getElementById('criminal_id').value);
    formData.append('name', document.getElementById('name').value);
    formData.append('offenses', document.getElementById('offenses').value);
    formData.append('risk_level', document.getElementById('risk_level').value);

    const submitBtn = document.getElementById('submitCriminalBtn');
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<div class="spinner"></div> Adding...';

    try {
        const response = await fetch('/api/criminals', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (result.success) {
            showToast(result.message, 'success');
            e.target.reset();
            document.getElementById('imagePreview').style.display = 'none';
            document.getElementById('criminalImage').value = '';
            
            // Update criminal count
            document.getElementById('statCriminals').textContent = 
                parseInt(document.getElementById('statCriminals').textContent) + 1;
                
        } else {
            showToast(result.message, 'error');
        }
    } catch (error) {
        showToast('Error adding criminal', 'error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="fas fa-save"></i> Add to Database';
    }
}

function updateScanStatus(scanning) {
    const startBtn = document.getElementById('startScanBtn');
    const stopBtn = document.getElementById('stopScanBtn');
    const status = document.getElementById('scanStatus');
    
    if (startBtn) {
        startBtn.disabled = scanning;
        startBtn.innerHTML = '<i class="fas fa-play"></i> Start Scanning';
    }
    if (stopBtn) stopBtn.disabled = !scanning;
    if (status) {
        status.textContent = scanning ? '🟢 Scanning active' : '🔴 Ready to start';
        status.className = `scan-status ${scanning ? 'status-active' : 'status-inactive'}`;
    }
}

function showToast(message, type = 'info') {
    // Create toast element
    const toast = document.createElement('div');
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'error' ? '#dc3545' : type === 'success' ? '#28a745' : type === 'warning' ? '#ffc107' : '#17a2b8'};
        color: white;
        padding: 12px 20px;
        border-radius: 5px;
        z-index: 10000;
        max-width: 400px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    `;
    toast.textContent = message;
    document.body.appendChild(toast);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (document.body.contains(toast)) {
            document.body.removeChild(toast);
        }
    }, 5000);
}

// Global functions
window.testAlertNotification = function() {
    showAlertNotification({
        criminal_name: 'Test Criminal',
        confidence: 85,
        timestamp: new Date().toLocaleTimeString()
    });
    showToast('Test alert triggered', 'info');
};