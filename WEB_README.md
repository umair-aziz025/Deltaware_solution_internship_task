# Web Directory Bruteforcer - Deployment Version

A web-based version of the Directory Bruteforcer tool, designed for deployment on cloud platforms like Render.

## Live Demo

**Deployment URL**: [Your Render URL will go here]

## Features

### Web Interface
- **Modern Responsive Design**: Clean, professional UI that works on desktop and mobile
- **Real-time Updates**: Live progress tracking and result display
- **Interactive Controls**: Start, stop, and download scan results
- **Session Management**: Multiple concurrent scans supported

### Core Functionality
- **HTTP Directory Discovery**: Tests common directory and file paths
- **Custom Wordlists**: User-provided wordlist input
- **Extension Testing**: Automatic testing with file extensions
- **Status Code Analysis**: Identifies accessible resources
- **Result Export**: Download results as text files

### Technical Implementation
- **Flask Backend**: Lightweight Python web framework
- **Asynchronous Scanning**: Non-blocking background tasks
- **Session Persistence**: Temporary result storage
- **RESTful API**: Clean endpoint structure for frontend communication

## Quick Start

### Local Development
```bash
git clone https://github.com/umair-aziz025/Deltaware_solution_internship_task.git
cd "gemini cli"
pip install -r requirements.txt
python app.py
```

### Usage
1. Enter target URL (e.g., `https://example.com`)
2. Provide wordlist (one path per line)
3. Optionally specify file extensions
4. Click "Start Scan" to begin
5. Monitor real-time progress and results
6. Download results when complete

### Sample Wordlist
```
admin
login
backup
config
uploads
test
dashboard
panel
```

## Deployment on Render

### Step 1: Prepare Repository
Ensure these files are in your repository:
- `app.py` (Flask application)
- `templates/index.html` (Frontend)
- `requirements.txt` (Dependencies)

### Step 2: Deploy on Render
1. Connect your GitHub repository to Render
2. Create a new Web Service
3. Use these settings:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Environment**: Python 3

### Step 3: Environment Configuration
- **Port**: Automatically configured by Render
- **Host**: `0.0.0.0` (configured in app.py)

## API Endpoints

### POST /start_scan
Start a new directory scan
```json
{
  "target_url": "https://example.com",
  "wordlist": "admin\nlogin\nbackup",
  "extensions": ".php, .html"
}
```

### GET /scan_status/{session_id}
Check scan progress and recent results

### GET /scan_results/{session_id}
Retrieve all scan results

### POST /stop_scan/{session_id}
Stop an active scan

### GET /download_results/{session_id}
Download results as text file

## Security Considerations

### Ethical Use Guidelines
- **Authorization Required**: Only scan systems you own or have permission to test
- **Rate Limiting**: Built-in delays to prevent server overload
- **Responsible Disclosure**: Follow proper vulnerability reporting practices

### Built-in Protections
- Request timeouts to prevent hanging
- Session-based isolation
- Temporary file cleanup
- User-agent rotation

## Technical Architecture

### Frontend
- **Vanilla JavaScript**: No framework dependencies
- **CSS Grid/Flexbox**: Responsive layout
- **Real-time Updates**: Polling-based status checks
- **Progressive Enhancement**: Works without JavaScript

### Backend
- **Flask**: Minimal web framework
- **Threading**: Background scan execution
- **Queue Management**: Session-based result storage
- **File Handling**: Temporary result export

### Deployment
- **Gunicorn**: Production WSGI server
- **Environment Variables**: Port configuration
- **Static Assets**: Inline CSS/JS for simplicity

## Performance Optimization

### Scanning Efficiency
- **Request Reuse**: Session-based HTTP connections
- **Smart Timeouts**: Configurable request timeouts
- **Memory Management**: Limited result storage

### Web Performance
- **Minimal Dependencies**: Lightweight Flask application
- **Efficient Polling**: Optimized status check intervals
- **Compressed Responses**: Gzip enabled by default

## Monitoring and Logging

### Application Logs
- Scan start/stop events
- Error tracking
- Performance metrics

### User Analytics
- Session duration tracking
- Popular target patterns
- Success rate metrics

## Future Enhancements

### Planned Features
- **User Authentication**: Secure access control
- **Scan History**: Persistent result storage
- **Advanced Filtering**: Content-based result analysis
- **API Rate Limiting**: Enhanced server protection
- **Report Generation**: PDF/HTML report export

### Technical Improvements
- **WebSocket Integration**: Real-time updates
- **Database Storage**: Persistent scan history
- **Caching Layer**: Improved performance
- **Load Balancing**: Multi-instance support

## Contributing

This project is part of the Deltaware internship program. Contributions welcome through:
- Bug reports and feature requests
- Code improvements and optimizations
- Documentation updates
- Security vulnerability reports

## License & Credits

**Developer**: Umair Aziz  
**Program**: Deltaware Internship Batch 7.2(A)  
**Tech Stack**: Python, Flask, HTML5, CSS3, JavaScript  
**Deployment**: Render Cloud Platform

---

*This tool is intended for educational and authorized security testing purposes only. Users are responsible for ensuring compliance with applicable laws and obtaining proper authorization before use.*
