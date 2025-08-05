from flask import Flask, jsonify, request, Response
import requests
import threading
from queue import Queue
import time
import os
from datetime import datetime
import uuid

app = Flask(__name__)

# Simple in-memory storage for scan sessions
scan_sessions = {}

class SimpleScanner:
    def __init__(self, session_id):
        self.session_id = session_id
        self.results = []
        self.progress = 0
        self.status = "idle"
        self.total_paths = 0
        self.completed_paths = 0
        self.stop_event = threading.Event()
        
    def test_url(self, session, url):
        try:
            response = session.head(url, timeout=3, allow_redirects=True, 
                                  headers={'User-Agent': 'Mozilla/5.0'})
            if response.status_code != 404:
                if response.status_code == 405:
                    response = session.get(url, timeout=3, allow_redirects=True,
                                         headers={'User-Agent': 'Mozilla/5.0'})
                if response.status_code != 404:
                    return {
                        'url': url,
                        'status_code': response.status_code,
                        'found_at': datetime.now().strftime('%H:%M:%S')
                    }
        except:
            pass
        return None
    
    def scan_worker(self, base_url, paths, extensions):
        self.status = "scanning"
        self.total_paths = len(paths)
        
        with requests.Session() as session:
            for i, path in enumerate(paths):
                if self.stop_event.is_set():
                    break
                    
                result = self.test_url(session, f"{base_url}/{path}")
                if result:
                    self.results.append(result)
                
                if extensions and not self.stop_event.is_set():
                    for ext in extensions:
                        if not path.endswith(ext):
                            result = self.test_url(session, f"{base_url}/{path}{ext}")
                            if result:
                                self.results.append(result)
                
                self.completed_paths = i + 1
                self.progress = (self.completed_paths / self.total_paths) * 100
                time.sleep(0.05)
        
        self.status = "completed" if not self.stop_event.is_set() else "stopped"

# HTML template embedded in Python
HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Web Directory Bruteforcer</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: #fff; min-height: 100vh; padding: 20px;
        }
        .container {
            max-width: 1000px; margin: 0 auto;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px); border-radius: 15px;
            padding: 30px; box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }
        .header { text-align: center; margin-bottom: 30px; }
        .header h1 {
            font-size: 2.5em; margin-bottom: 10px;
            background: linear-gradient(45deg, #00ff88, #00b4ff);
            background-clip: text; -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .form-group { margin-bottom: 20px; }
        .form-group label { display: block; margin-bottom: 8px; font-weight: 600; }
        .form-group input, .form-group textarea {
            width: 100%; padding: 12px; border: none; border-radius: 8px;
            background: rgba(255, 255, 255, 0.1); color: #fff;
            font-size: 16px; backdrop-filter: blur(5px);
        }
        .form-group input::placeholder, .form-group textarea::placeholder {
            color: rgba(255, 255, 255, 0.6);
        }
        .form-group textarea { resize: vertical; min-height: 120px; }
        .btn {
            background: linear-gradient(45deg, #00ff88, #00b4ff);
            color: #fff; border: none; padding: 12px 24px;
            border-radius: 8px; cursor: pointer; font-size: 16px;
            font-weight: 600; margin-right: 10px; margin-bottom: 10px;
            transition: transform 0.2s;
        }
        .btn:hover { transform: translateY(-2px); }
        .btn:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
        .btn-danger { background: linear-gradient(45deg, #ff4757, #ff3838); }
        .progress-container { margin: 20px 0; display: none; }
        .progress-bar {
            width: 100%; height: 8px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 4px; overflow: hidden;
        }
        .progress-fill {
            height: 100%; background: linear-gradient(45deg, #00ff88, #00b4ff);
            width: 0%; transition: width 0.3s ease;
        }
        .status { margin-top: 10px; font-weight: 600; }
        .results-container { margin-top: 30px; }
        .results-box {
            background: rgba(0, 0, 0, 0.3); border-radius: 8px;
            padding: 20px; min-height: 300px; max-height: 400px;
            overflow-y: auto; font-family: 'Courier New', monospace;
        }
        .result-item { padding: 8px 0; border-bottom: 1px solid rgba(255, 255, 255, 0.1); }
        .result-item:last-child { border-bottom: none; }
        .result-url { color: #00ff88; font-weight: 600; }
        .result-status { color: #00b4ff; }
        .alert {
            padding: 12px; border-radius: 8px; margin-bottom: 20px;
        }
        .alert-error { background: rgba(255, 71, 87, 0.2); border: 1px solid #ff4757; }
        .alert-success { background: rgba(0, 255, 136, 0.2); border: 1px solid #00ff88; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        @media (max-width: 768px) {
            .grid { grid-template-columns: 1fr; }
            .container { padding: 20px; }
            .header h1 { font-size: 2em; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Web Directory Bruteforcer</h1>
            <p>Discover hidden directories and files on web servers</p>
        </div>

        <div id="alert-container"></div>

        <form id="scanForm">
            <div class="grid">
                <div class="form-group">
                    <label for="targetUrl">Target URL:</label>
                    <input type="url" id="targetUrl" placeholder="https://example.com" required>
                </div>
                <div class="form-group">
                    <label for="extensions">Extensions (optional):</label>
                    <input type="text" id="extensions" placeholder=".php, .html, .asp">
                </div>
            </div>

            <div class="form-group">
                <label for="wordlist">Wordlist (one path per line):</label>
                <textarea id="wordlist" placeholder="admin\\nlogin\\nbackup\\nconfig\\nuploads">admin
login
backup
config
uploads
test
dashboard
panel
files
images
css
js
api
docs
help
support</textarea>
            </div>

            <button type="submit" class="btn" id="startBtn">Start Scan</button>
            <button type="button" class="btn btn-danger" id="stopBtn" style="display: none;">Stop Scan</button>
        </form>

        <div class="progress-container" id="progressContainer">
            <div class="progress-bar">
                <div class="progress-fill" id="progressFill"></div>
            </div>
            <div class="status" id="statusText">Status: Idle</div>
        </div>

        <div class="results-container">
            <div class="results-header">
                <h3>Scan Results</h3>
            </div>
            <div class="results-box" id="resultsBox">
                <div style="color: rgba(255, 255, 255, 0.6); text-align: center; padding: 50px;">
                    No scan results yet. Start a scan to see discovered directories and files.
                </div>
            </div>
        </div>

        <div style="text-align: center; margin-top: 30px; opacity: 0.7; font-style: italic;">
            <p>Copyright © Made by Umair Aziz | Deltaware Internship Project</p>
            <p>⚠️ For authorized testing only. Use responsibly and ethically.</p>
        </div>
    </div>

    <script>
        let currentSessionId = null;
        let statusInterval = null;

        function showAlert(message, type = 'error') {
            const alertContainer = document.getElementById('alert-container');
            const alertDiv = document.createElement('div');
            alertDiv.className = `alert alert-${type}`;
            alertDiv.textContent = message;
            alertContainer.innerHTML = '';
            alertContainer.appendChild(alertDiv);
            setTimeout(() => alertDiv.remove(), 5000);
        }

        function updateProgress(progress, status, completed, total) {
            document.getElementById('progressFill').style.width = progress + '%';
            document.getElementById('statusText').textContent = 
                `Status: ${status} | Progress: ${completed}/${total} (${Math.round(progress)}%)`;
        }

        function clearResults() {
            document.getElementById('resultsBox').innerHTML = 
                '<div style="color: rgba(255, 255, 255, 0.6); text-align: center; padding: 50px;">Scanning in progress...</div>';
        }

        function checkScanStatus() {
            if (!currentSessionId) return;

            fetch(`/scan_status/${currentSessionId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        showAlert('Status error: ' + data.error);
                        clearInterval(statusInterval);
                        return;
                    }
                    
                    updateProgress(data.progress, data.status, data.completed_paths, data.total_paths);
                    
                    if (data.results && data.results.length > 0) {
                        data.results.forEach(result => {
                            if (!document.querySelector(`[data-url="${result.url}"]`)) {
                                const resultDiv = document.createElement('div');
                                resultDiv.className = 'result-item';
                                resultDiv.setAttribute('data-url', result.url);
                                resultDiv.innerHTML = `
                                    <div class="result-url">[+] Found: ${result.url}</div>
                                    <div class="result-status">Status: ${result.status_code} | Time: ${result.found_at}</div>
                                `;
                                document.getElementById('resultsBox').appendChild(resultDiv);
                                document.getElementById('resultsBox').scrollTop = document.getElementById('resultsBox').scrollHeight;
                            }
                        });
                    }
                    
                    if (data.status === 'completed' || data.status === 'stopped') {
                        clearInterval(statusInterval);
                        document.getElementById('startBtn').style.display = 'inline-block';
                        document.getElementById('stopBtn').style.display = 'none';
                        
                        if (data.results_count === 0) {
                            document.getElementById('resultsBox').innerHTML = 
                                '<div style="color: rgba(255, 255, 255, 0.6); text-align: center; padding: 50px;">No directories or files found.</div>';
                        }
                        
                        showAlert(`Scan ${data.status}! Found ${data.results_count} items.`, 'success');
                    }
                })
                .catch(error => console.error('Status check error:', error));
        }

        document.getElementById('scanForm').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData();
            formData.append('target_url', document.getElementById('targetUrl').value);
            formData.append('extensions', document.getElementById('extensions').value);
            formData.append('wordlist', document.getElementById('wordlist').value);
            
            fetch('/start_scan', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    showAlert(data.error);
                } else {
                    currentSessionId = data.session_id;
                    document.getElementById('startBtn').style.display = 'none';
                    document.getElementById('stopBtn').style.display = 'inline-block';
                    document.getElementById('progressContainer').style.display = 'block';
                    
                    clearResults();
                    showAlert(`Scan started! Testing ${data.total_paths} paths.`, 'success');
                    statusInterval = setInterval(checkScanStatus, 1000);
                }
            })
            .catch(error => showAlert('Error starting scan: ' + error.message));
        });

        document.getElementById('stopBtn').addEventListener('click', function() {
            if (currentSessionId) {
                fetch(`/stop_scan/${currentSessionId}`, { method: 'POST' })
                    .then(response => response.json())
                    .then(data => showAlert('Scan stopped by user.', 'success'));
            }
        });
    </script>
</body>
</html>'''

@app.route('/')
def index():
    return Response(HTML_TEMPLATE, mimetype='text/html')

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'message': 'Web Directory Bruteforcer API',
        'endpoints': ['/health', '/', '/start_scan', '/scan_status/<id>', '/stop_scan/<id>']
    })

@app.route('/start_scan', methods=['POST'])
def start_scan():
    try:
        target_url = request.form.get('target_url', '').rstrip('/')
        wordlist_text = request.form.get('wordlist', '')
        extensions_text = request.form.get('extensions', '')
        
        if not target_url:
            return jsonify({'error': 'Target URL is required'}), 400
        
        if not wordlist_text.strip():
            return jsonify({'error': 'Wordlist is required'}), 400
        
        paths = [line.strip() for line in wordlist_text.split('\n') 
                if line.strip() and not line.strip().startswith('#')]
        
        if not paths:
            return jsonify({'error': 'Wordlist is empty or invalid'}), 400
        
        extensions = [ext.strip() for ext in extensions_text.split(',') 
                      if ext.strip()] if extensions_text else []
        
        session_id = str(uuid.uuid4())
        scanner = SimpleScanner(session_id)
        scan_sessions[session_id] = scanner
        
        scan_thread = threading.Thread(
            target=scanner.scan_worker,
            args=(target_url, paths, extensions),
            daemon=True
        )
        scan_thread.start()
        
        return jsonify({
            'session_id': session_id,
            'message': 'Scan started successfully',
            'total_paths': len(paths)
        })
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/scan_status/<session_id>')
def scan_status(session_id):
    try:
        scanner = scan_sessions.get(session_id)
        if not scanner:
            return jsonify({'error': 'Session not found'}), 404
        
        return jsonify({
            'status': scanner.status,
            'progress': scanner.progress,
            'completed_paths': scanner.completed_paths,
            'total_paths': scanner.total_paths,
            'results_count': len(scanner.results),
            'results': scanner.results[-10:]
        })
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/stop_scan/<session_id>', methods=['POST'])
def stop_scan(session_id):
    try:
        scanner = scan_sessions.get(session_id)
        if not scanner:
            return jsonify({'error': 'Session not found'}), 404
        
        scanner.stop_event.set()
        return jsonify({'message': 'Scan stopped'})
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

# Vercel handler
def handler(request):
    return app(request.environ, lambda status, headers: None)

if __name__ == '__main__':
    app.run(debug=True)
else:
    application = app
