# 🚀 Eyeguard - VS Code Command Guide

## 📋 Quick Start Commands

### 1️⃣ **Run Camera Tracking** (Most Used)
```bash
python simple_app.py
```
- Opens camera window
- Real-time eye tracking
- Blink detection
- Press 'q' to stop

### 2️⃣ **Start Web Dashboard**
```bash
# Terminal 1: Start API Server
python api/app.py

# Terminal 2: Open Dashboard
open web/dashboard.html
```

### 3️⃣ **Generate Reports**
```bash
# PDF Report
python eyeguard_cli.py report --user YOUR_NAME

# Analytics
python eyeguard_cli.py analytics --user YOUR_NAME

# Session History
python eyeguard_cli.py history --limit 10 --user YOUR_NAME
```

---

## 🎯 All Available Commands

### **Eye Tracking Commands**

#### Simple Camera App
```bash
python simple_app.py
```

#### Advanced Live Test
```bash
python test_system.py --live
```

#### Component Test (No Camera)
```bash
python test_system.py
```

---

### **Web Application Commands**

#### Start API Server
```bash
python api/app.py
```
- Runs on: http://localhost:8080
- 15+ REST endpoints
- CORS enabled

#### Open Web Dashboard
```bash
open web/dashboard.html
```
Or manually open in browser:
- File → Open → `web/dashboard.html`

#### Open Complete Web App
```bash
open web/complete-app.html
```

---

### **Report Generation Commands**

#### Generate PDF Report
```bash
python eyeguard_cli.py report --user YOUR_NAME
```

#### Generate PDF for Specific Date
```bash
python eyeguard_cli.py report --user YOUR_NAME --date 2025-11-27
```

#### View Analytics
```bash
python eyeguard_cli.py analytics --user YOUR_NAME --days 7
```

#### Export Data
```bash
# CSV Export
python eyeguard_cli.py export --format csv --user YOUR_NAME

# JSON Export  
python eyeguard_cli.py export --format json --user YOUR_NAME

# Excel Export
python eyeguard_cli.py export --format excel --user YOUR_NAME
```

#### View Session History
```bash
python eyeguard_cli.py history --limit 20 --user YOUR_NAME
```

---

### **Machine Learning Commands**

#### Train ML Model
```bash
python src/ml/model_trainer.py
```

#### Train with Custom Parameters
```bash
python src/ml/model_trainer.py --samples 1000 --epochs 50
```

---

### **Data Management Commands**

#### View Reports Folder
```bash
open data/reports/
```

#### View Database
```bash
sqlite3 data/eyeguard_sessions.db
```

#### List All Datasets
```bash
ls -lh data/datasets/
```

---

## 🔧 Setup & Installation Commands

### Initial Setup
```bash
# Navigate to project
cd /Users/sauravkumar/CODE_FOR_TEST/Eye-Guard

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "import cv2, mediapipe, tensorflow; print('✅ All installed')"
```

### Check Environment
```bash
# Python version
python --version

# List installed packages
pip list | grep -E "opencv|mediapipe|tensorflow"

# Check camera access
python -c "import cv2; print('Camera:', cv2.VideoCapture(0).isOpened())"
```

---

## 🛠️ VS Code Terminal Setup

### Open Multiple Terminals in VS Code

**Method 1: Split Terminal**
1. Press `Ctrl + Shift + \` ` (backtick)
2. Click the split terminal icon

**Method 2: New Terminal**
1. Press `Ctrl + Shift + \` ` 
2. Click "+" to add new terminal

### Recommended Terminal Layout

**Terminal 1**: API Server
```bash
python api/app.py
```

**Terminal 2**: Camera Tracking
```bash
python simple_app.py
```

**Terminal 3**: Commands (reports, analytics, etc.)
```bash
python eyeguard_cli.py <command>
```

---

## 🎬 Demo Flow Commands

### For Project Presentation

**Step 1: Start Camera**
```bash
python simple_app.py
```
Run for 1-2 minutes, let it detect blinks

**Step 2: Generate Report**
```bash
python eyeguard_cli.py report --user demo
```

**Step 3: Show Analytics**
```bash
python eyeguard_cli.py analytics --user demo
```

**Step 4: Open Web Dashboard**
```bash
python api/app.py &
open web/dashboard.html
```

**Step 5: Show Exports**
```bash
python eyeguard_cli.py export --format csv --user demo
open data/reports/
```

---

## 📊 Verification Commands

### Check System Status
```bash
# Check if API is running
curl http://localhost:8080/api/health

# Test session creation
curl -X POST http://localhost:8080/api/sessions/create \
  -H "Content-Type: application/json" \
  -d '{"user_profile":"test_user"}'
```

### View Logs
```bash
# View latest logs
tail -f data/logs/eyeguard.log

# View error logs
tail -f data/logs/eyeguard_error.log
```

---

## 🐛 Debugging Commands

### Camera Issues
```bash
# Test camera directly
python -c "import cv2; cap=cv2.VideoCapture(0); print('Camera:', cap.isOpened())"

# List available cameras
python -c "import cv2; [print(f'Camera {i}:', cv2.VideoCapture(i).isOpened()) for i in range(3)]"
```

### Module Issues
```bash
# Check imports
python -c "from src.core.eye_detector import EyeDetector; print('✅ OK')"

# Test MediaPipe
python -c "import mediapipe as mp; print('MediaPipe:', mp.__version__)"

# Test TensorFlow
python -c "import tensorflow as tf; print('TensorFlow:', tf.__version__)"
```

---

## 🔄 Restart Commands

### Kill Running Processes
```bash
# Kill API server on port 8080
lsof -ti :8080 | xargs kill -9

# Kill all Python processes (careful!)
pkill -f python
```

### Clean Reset
```bash
# Remove Python cache
find . -type d -name __pycache__ -exec rm -rf {} +

# Remove temp files
rm -rf data/reports/temp_*.png
```

---

## 📦 Deployment Commands

### Git Setup
```bash
# Initialize repository
git init

# Add all files
git add .

# Commit
git commit -m "Eyeguard: Complete Eye Strain Detection System"

# Add remote
git remote add origin https://github.com/YOUR_USERNAME/Eye-Guard.git

# Push
git push -u origin main
```

### Docker Commands
```bash
# Build image
docker build -t eyeguard .

# Run container
docker run -p 8080:8080 eyeguard

# Use Docker Compose
docker-compose up -d
```

---

## 🎓 Evaluation Demo Commands

### Quick 5-Minute Demo

**Minute 1**: Show camera tracking
```bash
python simple_app.py
```

**Minute 2**: Show results & stats
```bash
# Let camera run, see blinks detected
# Press 'q' to stop
```

**Minute 3**: Generate report
```bash
python eyeguard_cli.py report --user demo
open data/reports/eyeguard_daily_report_*.pdf
```

**Minute 4**: Show web dashboard
```bash
python api/app.py &
open web/dashboard.html
```

**Minute 5**: Show analytics
```bash
python eyeguard_cli.py analytics --user demo
```

---

## 💡 Pro Tips for VS Code

### Create Tasks (tasks.json)
```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Run Camera",
      "type": "shell",
      "command": "python simple_app.py",
      "group": "test"
    },
    {
      "label": "Start API",
      "type": "shell",
      "command": "python api/app.py",
      "group": "test"
    }
  ]
}
```

### Create Launch Configuration (launch.json)
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Camera Tracking",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/simple_app.py"
    },
    {
      "name": "API Server",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/api/app.py"
    }
  ]
}
```

### Keyboard Shortcuts
- `F5` - Run with debugger
- `Ctrl + F5` - Run without debugger
- `Ctrl + C` - Stop running process
- `Ctrl + \` ` - Toggle terminal

---

## ✅ Command Checklist

Before Presentation:
- [ ] `python test_system.py` - Verify all components
- [ ] `python simple_app.py` - Test camera
- [ ] `python api/app.py` - Start API
- [ ] `open web/dashboard.html` - Check dashboard
- [ ] `python eyeguard_cli.py report --user demo` - Generate sample report

---

## 🆘 Quick Help

```bash
# Get help for any command
python eyeguard_cli.py --help
python simple_app.py --help
python test_system.py --help
```

---

**Save this file as `COMMANDS.md` for quick reference!**

**For immediate use, run:**
```bash
python simple_app.py
```

This starts camera tracking and you're ready to go! 🚀
