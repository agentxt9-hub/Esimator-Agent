"""
Real-Time Test Monitoring Dashboard
Streams test results as they happen with live updates
"""

import json
import threading
import time
from flask import Flask, render_template_string, Response
from queue import Queue

app = Flask(__name__)

# Global test event queue
test_events = Queue()

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Estimator AgentX - Live Test Monitor</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #0a1628;
            color: #e2e8f0;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        .header {
            background: linear-gradient(135deg, #1e3a8a 0%, #991b1b 100%);
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .header h1 {
            font-size: 28px;
        }
        .live-indicator {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 14px;
        }
        .pulse {
            width: 12px;
            height: 12px;
            background: #10b981;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        .stat-card {
            background: #1e293b;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #3b82f6;
        }
        .stat-card.passed { border-left-color: #10b981; }
        .stat-card.failed { border-left-color: #ef4444; }
        .stat-card .label {
            font-size: 12px;
            text-transform: uppercase;
            opacity: 0.7;
            margin-bottom: 5px;
        }
        .stat-card .value {
            font-size: 32px;
            font-weight: bold;
        }
        .test-feed {
            background: #1e293b;
            border-radius: 8px;
            max-height: 600px;
            overflow-y: auto;
        }
        .test-event {
            padding: 15px 20px;
            border-bottom: 1px solid #334155;
            display: flex;
            align-items: flex-start;
            gap: 15px;
            animation: slideIn 0.3s ease-out;
        }
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateX(-20px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
        .test-event.running { background: rgba(59, 130, 246, 0.1); }
        .test-event.passed { background: rgba(16, 185, 129, 0.1); }
        .test-event.failed { background: rgba(239, 68, 68, 0.1); }
        .event-icon {
            font-size: 24px;
            flex-shrink: 0;
        }
        .event-content {
            flex-grow: 1;
        }
        .event-title {
            font-weight: 600;
            margin-bottom: 5px;
        }
        .event-category {
            font-size: 12px;
            opacity: 0.7;
            margin-bottom: 5px;
        }
        .event-time {
            font-size: 11px;
            opacity: 0.5;
        }
        .event-details {
            margin-top: 8px;
            font-size: 13px;
            opacity: 0.8;
        }
        .progress-bar {
            background: #0f172a;
            height: 6px;
            border-radius: 3px;
            overflow: hidden;
            margin-top: 10px;
        }
        .progress-fill {
            background: linear-gradient(90deg, #3b82f6, #10b981);
            height: 100%;
            transition: width 0.3s ease;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 Live Test Monitor</h1>
            <div class="live-indicator">
                <div class="pulse"></div>
                <span>LIVE</span>
            </div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="label">Total Tests</div>
                <div class="value" id="total-tests">0</div>
            </div>
            <div class="stat-card passed">
                <div class="label">Passed</div>
                <div class="value" id="passed-tests">0</div>
            </div>
            <div class="stat-card failed">
                <div class="label">Failed</div>
                <div class="value" id="failed-tests">0</div>
            </div>
            <div class="stat-card">
                <div class="label">Running</div>
                <div class="value" id="running-tests">0</div>
            </div>
        </div>
        
        <div class="progress-bar">
            <div class="progress-fill" id="progress-fill" style="width: 0%"></div>
        </div>
        
        <div class="test-feed" id="test-feed">
            <div style="padding: 40px; text-align: center; opacity: 0.5;">
                Waiting for tests to start...
            </div>
        </div>
    </div>

    <script>
        const eventSource = new EventSource('/stream');
        const testFeed = document.getElementById('test-feed');
        
        let totalTests = 0;
        let passedTests = 0;
        let failedTests = 0;
        let runningTests = 0;
        
        eventSource.onmessage = function(event) {
            const data = JSON.parse(event.data);
            
            // Clear placeholder
            if (testFeed.querySelector('div[style*="text-align: center"]')) {
                testFeed.innerHTML = '';
            }
            
            // Update stats
            if (data.status === 'started') {
                totalTests++;
                runningTests++;
            } else if (data.status === 'passed') {
                passedTests++;
                runningTests--;
            } else if (data.status === 'failed') {
                failedTests++;
                runningTests--;
            }
            
            document.getElementById('total-tests').textContent = totalTests;
            document.getElementById('passed-tests').textContent = passedTests;
            document.getElementById('failed-tests').textContent = failedTests;
            document.getElementById('running-tests').textContent = runningTests;
            
            // Update progress
            const completed = passedTests + failedTests;
            const progress = totalTests > 0 ? (completed / totalTests) * 100 : 0;
            document.getElementById('progress-fill').style.width = progress + '%';
            
            // Add event to feed
            const eventDiv = document.createElement('div');
            eventDiv.className = 'test-event ' + data.status;
            
            let icon = '⏳';
            if (data.status === 'passed') icon = '✅';
            if (data.status === 'failed') icon = '❌';
            
            let detailsHtml = '';
            if (data.message) {
                detailsHtml = `<div class="event-details">${data.message}</div>`;
            }
            
            eventDiv.innerHTML = `
                <div class="event-icon">${icon}</div>
                <div class="event-content">
                    <div class="event-title">${data.test_name}</div>
                    <div class="event-category">${data.category}</div>
                    ${detailsHtml}
                    <div class="event-time">${new Date().toLocaleTimeString()}</div>
                </div>
            `;
            
            testFeed.insertBefore(eventDiv, testFeed.firstChild);
        };
        
        eventSource.onerror = function() {
            console.error('EventSource error');
        };
    </script>
</body>
</html>
"""

@app.route('/')
def dashboard():
    return render_template_string(DASHBOARD_HTML)

@app.route('/stream')
def stream():
    def event_stream():
        while True:
            if not test_events.empty():
                event = test_events.get()
                yield f"data: {json.dumps(event)}\n\n"
            time.sleep(0.1)
    
    return Response(event_stream(), mimetype='text/event-stream')

def publish_test_event(test_name, category, status, message=None):
    """Publish test event to dashboard"""
    event = {
        'test_name': test_name,
        'category': category,
        'status': status,  # started, passed, failed
        'message': message,
        'timestamp': time.time()
    }
    test_events.put(event)

def start_dashboard_server():
    """Start dashboard in background thread"""
    thread = threading.Thread(target=lambda: app.run(port=5001, debug=False, use_reloader=False))
    thread.daemon = True
    thread.start()
    print("📊 Live dashboard running at http://localhost:5001")
    return thread

if __name__ == '__main__':
    # Start dashboard
    start_dashboard_server()
    
    # Keep alive
    print("Dashboard is live. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down dashboard...")
