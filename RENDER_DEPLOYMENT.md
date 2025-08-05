# Render.com Deployment Configuration

## For the Render Dashboard, use these settings:

### Build Command:
```
pip install -r requirements.txt
```

### Start Command:
```
gunicorn app:app
```

### Environment Variables:
- PYTHON_VERSION: 3.9.16
- PORT: (automatically set by Render)

### Other Settings:
- Language: Python 3
- Branch: master
- Root Directory: (leave empty)
- Instance Type: Free (for testing) or Starter (for production)

## Why Render is Better Than Vercel for This App:

1. **Native Flask Support**: Render handles Flask apps natively without serverless complications
2. **Persistent File System**: Better for file uploads and temporary storage
3. **No Cold Starts**: Your app stays warm (on paid plans)
4. **Easier Debugging**: Real logs and persistent containers
5. **Better for Long-Running Processes**: Directory scans can take time

## Your App Structure (Perfect for Render):
```
/
├── app.py                 # Main Flask app (✅ Ready)
├── templates/
│   └── index.html         # Frontend (✅ Ready)
├── uploads/               # File uploads directory
├── requirements.txt       # Dependencies (✅ Updated with gunicorn)
└── README.md
```

## Test Locally Before Deploying:
```bash
pip install -r requirements.txt
python app.py
# Visit http://localhost:5000
```
