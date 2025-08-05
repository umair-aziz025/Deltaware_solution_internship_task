from flask import Flask, render_template, request, jsonify, send_file
import requests
import threading
from queue import Queue
import time
import os
import tempfile
from datetime import datetime
import uuid

app = Flask(__name__)

# Global storage for scan sessions
scan_sessions = {}

class WebScanner:
    def __init__(self, session_id):
        self.session_id = session_id
        self.results = []
        self.progress = 0
        self.status = "idle"
        self.total_paths = 0
        self.completed_paths = 0
        self.stop_event = threading.Event()
        
    def test_url(self, session, url):
        """Tests a single URL and returns result if found."""
        try:
            response = session.head(url, timeout=5, allow_redirects=True, 
                                  headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
            
            if response.status_code != 404:
                if response.status_code == 405:  # Method not allowed, try GET
                    response = session.get(url, timeout=5, allow_redirects=True,
                                         headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
                
                if response.status_code != 404:
                    return {
                        'url': url,
                        'status_code': response.status_code,
                        'found_at': datetime.now().strftime('%H:%M:%S')
                    }
        except requests.exceptions.RequestException:
            pass
        return None
    
    def scan_worker(self, base_url, paths, extensions):
        """Worker function for scanning."""
        self.status = "scanning"
        self.total_paths = len(paths)
        
        with requests.Session() as session:
            for i, path in enumerate(paths):
                if self.stop_event.is_set():
                    break
                    
                # Test path as is
                result = self.test_url(session, f"{base_url}/{path}")
                if result:
                    self.results.append(result)
                
                # Test with extensions
                if extensions and not self.stop_event.is_set():
                    for ext in extensions:
                        if not path.endswith(ext):
                            result = self.test_url(session, f"{base_url}/{path}{ext}")
                            if result:
                                self.results.append(result)
                
                self.completed_paths = i + 1
                self.progress = (self.completed_paths / self.total_paths) * 100
                
                # Small delay to prevent overwhelming the server
                time.sleep(0.1)
        
        self.status = "completed" if not self.stop_event.is_set() else "stopped"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_scan', methods=['POST'])
def start_scan():
    data = request.json
    target_url = data.get('target_url', '').rstrip('/')
    wordlist_text = data.get('wordlist', '')
    extensions_text = data.get('extensions', '')
    
    if not target_url or not wordlist_text:
        return jsonify({'error': 'Target URL and wordlist are required'}), 400
    
    # Generate session ID
    session_id = str(uuid.uuid4())
    
    # Parse wordlist
    paths = [line.strip() for line in wordlist_text.split('\n') 
             if line.strip() and not line.strip().startswith('#')]
    
    if not paths:
        return jsonify({'error': 'Wordlist is empty or invalid'}), 400
    
    # Parse extensions
    extensions = [ext.strip() for ext in extensions_text.split(',') 
                  if ext.strip()] if extensions_text else []
    
    # Create scanner instance
    scanner = WebScanner(session_id)
    scan_sessions[session_id] = scanner
    
    # Start scanning in background thread
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

@app.route('/scan_status/<session_id>')
def scan_status(session_id):
    scanner = scan_sessions.get(session_id)
    if not scanner:
        return jsonify({'error': 'Session not found'}), 404
    
    return jsonify({
        'status': scanner.status,
        'progress': scanner.progress,
        'completed_paths': scanner.completed_paths,
        'total_paths': scanner.total_paths,
        'results_count': len(scanner.results),
        'results': scanner.results[-10:]  # Last 10 results for live updates
    })

@app.route('/scan_results/<session_id>')
def scan_results(session_id):
    scanner = scan_sessions.get(session_id)
    if not scanner:
        return jsonify({'error': 'Session not found'}), 404
    
    return jsonify({
        'results': scanner.results,
        'status': scanner.status,
        'total_found': len(scanner.results)
    })

@app.route('/stop_scan/<session_id>', methods=['POST'])
def stop_scan(session_id):
    scanner = scan_sessions.get(session_id)
    if not scanner:
        return jsonify({'error': 'Session not found'}), 404
    
    scanner.stop_event.set()
    return jsonify({'message': 'Scan stopped'})

@app.route('/download_results/<session_id>')
def download_results(session_id):
    scanner = scan_sessions.get(session_id)
    if not scanner:
        return jsonify({'error': 'Session not found'}), 404
    
    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
    
    # Write results to file
    temp_file.write(f"Directory Bruteforcer Results\n")
    temp_file.write(f"Generated: {datetime.now()}\n")
    temp_file.write(f"Total Found: {len(scanner.results)}\n")
    temp_file.write("-" * 50 + "\n\n")
    
    for result in scanner.results:
        temp_file.write(f"[+] Found: {result['url']} [Status: {result['status_code']}] [Time: {result['found_at']}]\n")
    
    temp_file.close()
    
    return send_file(temp_file.name, as_attachment=True, download_name=f'scan_results_{session_id[:8]}.txt')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
