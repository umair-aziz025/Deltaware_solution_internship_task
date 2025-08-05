from flask import Flask, render_template, request, jsonify
import requests
import threading
from queue import Queue
import time
import os
import tempfile
from datetime import datetime
import uuid
import sys
from werkzeug.utils import secure_filename

# Configure Flask app for Vercel with proper template path
template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'templates')
app = Flask(__name__, template_folder=template_dir)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

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
    
    def scan_worker(self, base_url, paths, extensions, num_threads=10):
        self.status = "scanning"
        self.total_paths = len(paths)
        
        # Create a queue for paths to scan
        path_queue = Queue()
        for path in paths:
            path_queue.put(path)
        
        # Worker function for threading
        def worker():
            with requests.Session() as session:
                while not path_queue.empty() and not self.stop_event.is_set():
                    try:
                        path = path_queue.get_nowait()
                    except:
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
                    
                    self.completed_paths += 1
                    self.progress = (self.completed_paths / self.total_paths) * 100
                    path_queue.task_done()
        
        # Start worker threads
        threads = []
        for _ in range(min(num_threads, len(paths))):
            t = threading.Thread(target=worker, daemon=True)
            t.start()
            threads.append(t)
        
        # Wait for all threads to complete
        for t in threads:
            t.join()
        
        self.status = "completed" if not self.stop_event.is_set() else "stopped"

@app.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        return jsonify({
            'error': f'Template error: {str(e)}',
            'template_dir': app.template_folder,
            'debug': f'Looking for templates in: {template_dir}'
        }), 500

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'environment': os.environ.get('VERCEL_ENV', 'local')
    })

@app.route('/start_scan', methods=['POST'])
def start_scan():
    try:
        target_url = request.form.get('target_url', '').rstrip('/')
        wordlist_text = request.form.get('wordlist', '')
        extensions_text = request.form.get('extensions', '')
        wordlist_file = request.files.get('wordlist_file')
        num_threads = int(request.form.get('threads', 10))  # Default 10 threads
        
        if not target_url:
            return jsonify({'error': 'Target URL is required'}), 400
        
        # Handle wordlist from either text input or file upload
        paths = []
        
        if wordlist_file and wordlist_file.filename:
            # Process uploaded file
            try:
                filename = secure_filename(wordlist_file.filename)
                if filename.endswith(('.txt', '.list', '.wordlist')):
                    file_content = wordlist_file.read().decode('utf-8', errors='ignore')
                    paths = [line.strip() for line in file_content.split('\n') 
                            if line.strip() and not line.strip().startswith('#')]
                else:
                    return jsonify({'error': 'Invalid file type. Please upload .txt, .list, or .wordlist files'}), 400
            except Exception as e:
                return jsonify({'error': f'Error reading file: {str(e)}'}), 400
        elif wordlist_text:
            # Process text input
            paths = [line.strip() for line in wordlist_text.split('\n') 
                    if line.strip() and not line.strip().startswith('#')]
        else:
            return jsonify({'error': 'Wordlist (text or file) is required'}), 400
        
        if not paths:
            return jsonify({'error': 'Wordlist is empty or invalid'}), 400
        
        # Limit threads to reasonable range
        num_threads = max(1, min(num_threads, 50))
        
        extensions = [ext.strip() for ext in extensions_text.split(',') 
                      if ext.strip()] if extensions_text else []
        
        session_id = str(uuid.uuid4())
        scanner = WebScanner(session_id)
        scan_sessions[session_id] = scanner
        
        scan_thread = threading.Thread(
            target=scanner.scan_worker,
            args=(target_url, paths, extensions, num_threads),
            daemon=True
        )
        scan_thread.start()
        
        return jsonify({
            'session_id': session_id,
            'message': 'Scan started successfully',
            'total_paths': len(paths),
            'threads': num_threads,
            'wordlist_source': 'file' if wordlist_file and wordlist_file.filename else 'text'
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
            'results': scanner.results[-5:]
        })
    except Exception as e:
        return jsonify({'error': f'Status error: {str(e)}'}), 500

@app.route('/stop_scan/<session_id>', methods=['POST'])
def stop_scan(session_id):
    try:
        scanner = scan_sessions.get(session_id)
        if not scanner:
            return jsonify({'error': 'Session not found'}), 404
        
        scanner.stop_event.set()
        return jsonify({'message': 'Scan stopped'})
    except Exception as e:
        return jsonify({'error': f'Stop error: {str(e)}'}), 500

# For Vercel - expose the app as 'app'
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
