from flask import Flask, jsonify
import os
import sys

app = Flask(__name__)

@app.route('/')
def hello():
    return jsonify({
        'message': 'Hello from Vercel!',
        'status': 'working',
        'python_version': sys.version,
        'environment': dict(os.environ)
    })

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

# Vercel handler
def handler(request):
    return app(request.environ, lambda status, headers: None)

if __name__ == '__main__':
    app.run(debug=True)
else:
    application = app
