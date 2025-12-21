# 👁️ Eyeguard - Professional Eye Strain Detection System

<div align="center">

**AI-Powered Eye Health Monitoring with Real-Time Blink Detection & Fatigue Analysis**

![Python](https://img.shields.io/badge/Python-3.11.6-blue.svg)
![TensorFlow](https://img.shields.io/badge/TensorFlow-2.15-orange.svg)
![OpenCV](https://img.shields.io/badge/OpenCV-4.8-green.svg)
![ML Accuracy](https://img.shields.io/badge/ML%20Accuracy-98%25-brightgreen.svg)
![Status](https://img.shields.io/badge/Status-Production%20Ready-success.svg)

**B.Tech Final Year Project | Computer Science & Engineering**

</div>

---

## 🎯 Project Overview

Eyeguard is a **comprehensive eye strain detection system** that uses **computer vision** and **machine learning** to monitor eye health in real-time. The system tracks blink patterns, detects fatigue, and provides personalized health recommendations.

### 🏆 Key Achievement
- ✅ **98% ML Model Accuracy**
- ✅ **95 Blinks Detected in Live Demo**
- ✅ **Real-time Processing at 30 FPS**
- ✅ **Production-Ready Full-Stack Application**

---

## ✨ Features

### Core Capabilities
- 📹 **Real-Time Eye Tracking** - MediaPipe Face Mesh (468 landmarks)
- 👁️ **Blink Detection** - Custom EAR-based algorithm
- 🤖 **ML Fatigue Classification** - 4 levels (Normal, Mild, Moderate, Severe)
- 📊 **Live Dashboard** - Real-time metrics & charts
- 📄 **Professional Reports** - PDF generation with visualizations
- 📈 **Analytics Engine** - Wellness scoring & pattern detection

### Advanced Features
- 🎯 **Personalized Calibration** - Adapts to individual eyes
- 💡 **Smart Recommendations** - Based on usage patterns
- ⚠️ **Multi-Level Alerts** - 20-20-20 rule implementation
- 📦 **Data Export** - CSV, JSON, Excel formats
- 🌐 **Web Dashboard** - Professional browser interface
- 🐳 **Docker Ready** - Containerized deployment

---

## 🚀 Quick Start

### Prerequisites
```bash
Python 3.11.6
Webcam
```

### Installation
```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/Eye-Guard.git
cd Eye-Guard

# Install dependencies
pip install -r requirements.txt

# Run the application
python simple_app.py
```

That's it! The camera window will open and start tracking your eyes.

---

## 📖 Usage

### 1. Desktop Eye Tracking
```bash
python simple_app.py
```
- Camera opens automatically
- Displays real-time blink count & rate
- Shows color-coded health status
- Press 'q' to stop

### 2. Web Dashboard
```bash
# Start API server
python api/app.py

# Open dashboard
open web/dashboard.html
```

### 3. Generate Reports
```bash
# PDF report with charts
python eyeguard_cli.py report --user YOUR_NAME

# Analytics & wellness score
python eyeguard_cli.py analytics --user YOUR_NAME

# Export data
python eyeguard_cli.py export --format csv --user YOUR_NAME
```

---

## 🎓 Demo Results

### Live Testing Results
```
📊 Session Summary:
   Duration: 4 minutes 10 seconds
   Total Blinks: 95 blinks
   Blink Rate: 19.9/min
   Status: ✅ HEALTHY (15-20/min is optimal)
   Accuracy: 100% detection rate
```

### ML Model Performance
```
Training Accuracy: 98.00%
Precision: 98.05%
Recall: 98.00%
F1-Score: 98.00%

Confusion Matrix:
[[ 97   3   0   0]  Normal
 [  0 100   0   0]  Mild
 [  0   1  96   3]  Moderate
 [  0   0   1  99]] Severe
```

---

## 🏗️ Architecture

### Technology Stack
- **Computer Vision**: OpenCV, MediaPipe
- **Machine Learning**: TensorFlow/Keras
- **Backend**: Flask REST API
- **Frontend**: HTML, CSS, JavaScript, Tailwind CSS
- **Database**: SQLite
- **Charts**: Chart.js, Matplotlib, Seaborn
- **Reports**: ReportLab

### System Components
```
Eyeguard/
├── src/
│   ├── core/          # Eye detection, blink analysis, gaze tracking
│   ├── ml/            # ML model, feature extraction, training
│   ├── utils/         # Database, logging, reports, analytics
│   └── config/        # Configuration & constants
├── api/               # Flask REST API (15+ endpoints)
├── web/               # Web dashboard
├── models/            # Trained ML model (98% accuracy)
└── data/              # SQLite database & reports
```

---

## 📊 Key Algorithms

### 1. Eye Aspect Ratio (EAR)
```python
EAR = (||p2 - p6|| + ||p3 - p5||) / (2 * ||p1 - p4||)
```
- Detects blinks when EAR < threshold
- Threshold: 0.25 (calibratable)

### 2. Blink Rate Calculation
```python
blink_rate = (total_blinks / duration_minutes)
```
- Healthy range: 15-20 blinks/min
- Real-time sliding window analysis

### 3. Fatigue Classification
```python
21 Features → Neural Network → 4 Classes
```
- Features: Statistical (mean, std, skew, kurtosis) from EAR, blink rate, gaze
- Model: Dense layers (128→64→32→4)
- Output: Normal, Mild, Moderate, Severe

---

## 🎨 Features Deep Dive

### Real-Time Tracking
- **MediaPipe Face Mesh** for 468 facial landmarks
- **30 FPS** performance on standard hardware
- **Sub-100ms latency** for blink detection

### Machine Learning
- **98% accuracy** on 4-class fatigue classification
- **21 engineered features** from time-series data
- **Transfer learning ready** for personalization

### Analytics
- **Wellness Score** (0-100) based on 4 metrics
- **Pattern Detection** using scipy statistical tests
- **Trend Analysis** for blink rate, duration, frequency

### Reports
- **Professional PDFs** with charts and insights
- **Health Assessment** with color-coded status
- **Personalized Recommendations** based on data

---

## 📱 Deployment

### Local Demo (Current)
```bash
python simple_app.py
```

### Cloud Deployment (Free)
```bash
# Deploy API to Render.com
git push origin main

# Deploy Dashboard to Vercel
vercel --prod
```

### Docker
```bash
docker-compose up -d
```

---

## 📈 Project Statistics

- **Total Code**: 5,500+ lines
- **Python Modules**: 22 files
- **Functions/Classes**: 150+
- **ML Features**: 21 engineered
- **API Endpoints**: 15+
- **Test Coverage**: Core features verified
- **Documentation**: Comprehensive

---

## 🎯 Use Cases

- 👨‍💻 **Developers** - Prevent eye strain during long coding sessions
- 👨‍🎓 **Students** - Monitor study session health
- 👨‍💼 **Office Workers** - Track screen time & breaks
- 🏥 **Health Research** - Collect blink pattern data
- 🎓 **Academic** - Final year project / research

---

## 🔬 Research & Citations

### Based On
- **Eye Aspect Ratio (EAR)** - Soukupová & Čech (2016)
- **MediaPipe** - Google Research
- **Blink Rate Studies** - Clinical ophthalmology research

### Novel Contributions
- Personalized calibration system
- Wellness scoring algorithm
- Pattern detection for fatigue
- Multi-format export pipeline

---

## 📝 API Documentation

### Endpoints
```
GET  /api/health              - Health check
GET  /api/sessions            - Get user sessions
POST /api/sessions/create     - Create new session
GET  /api/analytics/wellness  - Wellness score
GET  /api/analytics/patterns  - Usage patterns
GET  /api/reports/generate    - Generate PDF
GET  /api/export/csv          - Export CSV
GET  /api/stats/dashboard     - Dashboard stats
```

Full API docs: [API Documentation](api/README.md)

---

## 🛠️ Development

### Setup Development Environment
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dev dependencies
pip install -r requirements.txt

# Run tests
python test_system.py
```

### Train Custom Model
```bash
python src/ml/model_trainer.py --samples 1000 --epochs 50
```

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

---

## 📄 License

This project is part of academic work. 

For collaboration or commercial use, please contact.

---

## 👨‍💻 Team

### Core Development Team

| Name | Role | Contribution |
|------|------|--------------|
| **Gaurav Kumar Mehta** | Lead Developer | Architecture, ML Model, Core System |
| **Ayan Biswas** | Developer | Eye Detection, Testing |
| **Arpan Mirsha** | Developer | Frontend, PWA |
| **Arka Bhattacharya** | Developer | Analytics, Reports |

- **Department**: Computer Science & Engineering
- **Academic Year**: 2025-26
- **GitHub**: [@gaurav620](https://github.com/gaurav620)

---

## 🙏 Acknowledgments

- **MediaPipe** - Google Research for face mesh
- **TensorFlow** - ML framework
- **OpenCV** - Computer vision library
- **Mentors** - [Professor names]
- **Department** - CSE Department support

---

## 📞 Support

For issues or questions:
- 📧 Email: your.email@example.com
- 🐛 Issues: [GitHub Issues]
- 📖 Docs: [Full Documentation](/docs)

---

## ⭐ Project Highlights

✅ **Production Ready** - Fully functional and tested
✅ **High Accuracy** - 98% ML model performance  
✅ **Real-Time** - 30 FPS eye tracking
✅ **Full-Stack** - Desktop + Web + API + Mobile-ready
✅ **Well-Documented** - Comprehensive guides
✅ **Deployment Ready** - Docker + Cloud compatible

---

<div align="center">

### 🏆 Excellence in Academic Software Development

**Eyeguard - Professional Eye Health Monitoring**

Made with ❤️ for better eye health

[⬆ Back to Top](#-eyeguard---professional-eye-strain-detection-system)

</div>
