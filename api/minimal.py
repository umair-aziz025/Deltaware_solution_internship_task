from flask import Flask, jsonify, request
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
    
    def scan_worker(self, base_url, paths):
        self.status = "scanning"
        self.total_paths = len(paths)
        
        with requests.Session() as session:
            for i, path in enumerate(paths[:10]):  # Limit to 10 for testing
                if self.stop_event.is_set():
                    break
                    
                result = self.test_url(session, f"{base_url}/{path}")
                if result:
                    self.results.append(result)
                
                self.completed_paths = i + 1
                self.progress = (self.completed_paths / self.total_paths) * 100
                time.sleep(0.2)
        
        self.status = "completed" if not self.stop_event.is_set() else "stopped"

@app.route('/')
def index():
    return jsonify({
        'message': 'Web Directory Bruteforcer API',
        'status': 'working',
        'endpoints': ['/health', '/start_scan', '/scan_status/<id>', '/stop_scan/<id>'],
        'frontend': 'Visit the main HTML page for the web interface'
    })

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'environment': 'vercel' if os.environ.get('VERCEL') else 'local',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/start_scan', methods=['POST'])
def start_scan():
    try:
        data = request.get_json() or {}
        target_url = data.get('target_url', '').rstrip('/')
        wordlist_text = data.get('wordlist', '')
        
        if not target_url:
            return jsonify({'error': 'Target URL is required'}), 400
        
        if not wordlist_text:
            return jsonify({'error': 'Wordlist is required'}), 400
        
        paths = [line.strip() for line in wordlist_text.split('\n') 
                if line.strip() and not line.strip().startswith('#')]
        
        if not paths:
            return jsonify({'error': 'Wordlist is empty'}), 400
        
        session_id = str(uuid.uuid4())
        scanner = SimpleScanner(session_id)
        scan_sessions[session_id] = scanner
        
        threading.Thread(
            target=scanner.scan_worker,
            args=(target_url, paths),
            daemon=True
        ).start()
        
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
            'results': scanner.results[-5:]  # Last 5 results
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

if __name__ == '__main__':
    app.run(debug=True)
