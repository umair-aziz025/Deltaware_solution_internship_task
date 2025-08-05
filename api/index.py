from flask import Flask, render_template, request, jsonify, send_file
import requests
import threading
from queue import Queue
import time
import os
import tempfile
from datetime import datetime
import uuid
from werkzeug.utils import secure_filename
import sys
import json

# Check if running on Vercel
IS_VERCEL = os.environ.get('VERCEL') or os.environ.get('VERCEL_ENV')

# Configure Flask app for Vercel
template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates')
app = Flask(__name__, template_folder=template_dir)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Adjust upload folder based on environment
if IS_VERCEL:
    app.config['UPLOAD_FOLDER'] = '/tmp'
else:
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'uploads')

# Create uploads directory if it doesn't exist and not on Vercel
if not IS_VERCEL:
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Global storage for scan sessions
scan_sessions = {}

@app.after_request
def after_request(response):
    """Add CORS headers to all responses"""
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

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
    try:
        return render_template('index.html')
    except Exception as e:
        # Fallback if template loading fails
        return jsonify({
            'error': 'Template loading failed',
            'message': str(e),
            'template_dir': app.template_folder,
            'is_vercel': IS_VERCEL
        }), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    try:
        return jsonify({
            'status': 'healthy',
            'environment': 'vercel' if IS_VERCEL else 'local',
            'timestamp': datetime.now().isoformat(),
            'python_version': sys.version,
            'template_folder': app.template_folder,
            'upload_folder': app.config.get('UPLOAD_FOLDER')
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/start_scan', methods=['POST'])
def start_scan():
    try:
        target_url = request.form.get('target_url', '').rstrip('/')
        wordlist_text = request.form.get('wordlist', '')
        extensions_text = request.form.get('extensions', '')
        wordlist_file = request.files.get('wordlist_file')
        
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
        
        # Parse extensions
        extensions = [ext.strip() for ext in extensions_text.split(',') 
                      if ext.strip()] if extensions_text else []
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        
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
            'total_paths': len(paths),
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
            'results': scanner.results[-10:]  # Last 10 results for live updates
        })
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/scan_results/<session_id>')
def scan_results(session_id):
    try:
        scanner = scan_sessions.get(session_id)
        if not scanner:
            return jsonify({'error': 'Session not found'}), 404
        
        return jsonify({
            'results': scanner.results,
            'status': scanner.status,
            'total_found': len(scanner.results)
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

@app.route('/download_results/<session_id>')
def download_results(session_id):
    try:
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
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

# For Vercel deployment - WSGI application
app.wsgi_app = app.wsgi_app

# Export for Vercel
application = app

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
