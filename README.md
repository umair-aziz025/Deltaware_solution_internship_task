# Directory Bruteforcer Tool

## Project Overview

The Directory Bruteforcer is a cybersecurity penetration testing tool designed to discover hidden directories and files on web servers through automated dictionary attacks. This tool helps security professionals and ethical hackers identify potential entry points and vulnerabilities in web applications by systematically testing common directory and file names.

## Features

### Core Functionality
- **Multi-threaded Scanning**: Utilizes configurable threading for faster scanning performance
- **Custom Wordlist Support**: Load custom wordlists for targeted directory discovery
- **Extension Testing**: Automatically test paths with multiple file extensions (.php, .html, .asp, etc.)
- **HTTP Status Code Analysis**: Identifies accessible resources based on response codes
- **Real-time Progress Tracking**: Visual progress bar and status updates

### User Interface
- **Modern GUI**: Built with CustomTkinter for an intuitive dark-themed interface
- **File Browser Integration**: Easy wordlist file selection through built-in file dialog
- **Live Results Display**: Real-time output of discovered directories and files
- **Export Functionality**: Save scan results to text files for reporting

### Technical Capabilities
- **Smart Request Handling**: Uses HEAD requests for efficiency, falls back to GET when needed
- **Error Resilience**: Robust exception handling for network timeouts and errors
- **Customizable User-Agent**: Mimics legitimate browser requests to avoid detection
- **Session Management**: Efficient connection reuse for improved performance

## Installation & Requirements

### Prerequisites
```
Python 3.7+
Required Libraries:
- customtkinter
- requests
- tkinter (usually included with Python)
```

### Installation Steps
1. Clone the repository
2. Install dependencies: `pip install customtkinter requests`
3. Run the application: `python dir_bruteforce.py`

## Usage Guide

### Basic Operation
1. **Target URL**: Enter the target website URL (e.g., https://example.com)
2. **Wordlist**: Select a wordlist file containing directory/file names to test
3. **Threads**: Configure the number of concurrent threads (default: 50)
4. **Extensions**: Optionally specify file extensions to test (.php, .html, etc.)
5. **Start Scan**: Begin the directory bruteforce attack
6. **Monitor Results**: View discovered directories in real-time
7. **Save Results**: Export findings to a file for documentation

### Wordlist Format
```
admin
login
backup
config
uploads
test
```

### Sample Output
```
[+] Found: https://example.com/admin [Status: 200]
[+] Found: https://example.com/login.php [Status: 200]
[+] Found: https://example.com/backup [Status: 403]
```

## Technical Architecture

### Threading Model
- **Main Thread**: Handles GUI updates and user interactions
- **Worker Threads**: Perform HTTP requests concurrently
- **Queue System**: Manages task distribution and result collection

### Request Strategy
1. Initial HEAD request for efficiency
2. Fallback to GET request if HEAD returns 405 (Method Not Allowed)
3. Filter out 404 responses (not found)
4. Report all other status codes as potential discoveries

### Performance Optimization
- Session reuse for connection pooling
- Configurable timeout settings
- Non-blocking GUI updates
- Memory-efficient queue management

## Security Considerations

### Ethical Use Only
This tool is designed for:
- Authorized penetration testing
- Security assessments on owned systems
- Educational purposes in controlled environments

### Important Disclaimers
- Only use on systems you own or have explicit permission to test
- Respect rate limits and server resources
- Follow responsible disclosure practices
- Comply with local laws and regulations

## Configuration Options

### Thread Configuration
- **Low**: 10-20 threads for slow servers
- **Medium**: 30-50 threads for standard use
- **High**: 50+ threads for fast servers (use cautiously)

### Extension Lists
Common web extensions to test:
- `.php, .html, .htm, .asp, .aspx, .jsp`
- `.txt, .xml, .json, .config`
- `.bak, .backup, .old, .tmp`

## Troubleshooting

### Common Issues
1. **Empty Results**: Check target URL accessibility
2. **Slow Performance**: Reduce thread count or check network connection
3. **High False Positives**: Verify wordlist quality and target responses

### Error Handling
- Network timeouts are handled gracefully
- Invalid URLs are detected and reported
- File access errors provide clear feedback

## Future Enhancements

### Planned Features
- **Custom Headers**: Support for authentication headers
- **Proxy Support**: Route requests through proxy servers
- **Response Analysis**: Content-based filtering of results
- **Report Generation**: HTML/PDF report output
- **Recursive Scanning**: Automatic subdirectory discovery

## Contributing

This project was developed as part of the Deltaware internship program. Contributions and improvements are welcome through proper channels.

## License & Credits

**Developer**: Umair Aziz  
**Program**: Deltaware Internship Batch 7.2(A)  
**Purpose**: Cybersecurity Education and Ethical Penetration Testing

---

*This tool is intended for educational and authorized security testing purposes only. Users are responsible for ensuring compliance with applicable laws and obtaining proper authorization before use.*
