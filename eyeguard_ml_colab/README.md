# 👁️ Eye-Guard ML Package for Google Colab

## Presentation-Ready Machine Learning Demo

This package contains everything you need to present the ML components of Eye-Guard in Google Colab.

---

## 📁 Contents

| File | Description |
|------|-------------|
| `EyeGuard_ML_Presentation.ipynb` | Main Colab notebook with full demo |
| `README.md` | This file |

---

## 🚀 Quick Start

### Option 1: Upload to Google Colab
1. Go to [Google Colab](https://colab.research.google.com/)
2. Click **File → Upload Notebook**
3. Upload `EyeGuard_ML_Presentation.ipynb`
4. Run all cells (Runtime → Run all)

### Option 2: Open from GitHub
If you push this to GitHub, you can open directly:
```
https://colab.research.google.com/github/gaurav620/Eye-Guard/blob/main/eyeguard_ml_colab/EyeGuard_ML_Presentation.ipynb
```

---

## 📊 What's Inside the Notebook

### Part 1: Eye Detection & Blink Tracking
- MediaPipe FaceMesh initialization
- Eye Aspect Ratio (EAR) calculation
- Visual explanation with diagrams
- Sample image processing

### Part 2: Fatigue Classification Model
- Synthetic dataset generation (2000 samples)
- Feature visualization by fatigue level
- Deep neural network architecture
- Training with TensorFlow/Keras
- Confusion matrix & classification report

### Part 3: Real-Time Demo
- Single prediction examples
- Interactive dashboard with sliders
- Health score visualization

### Part 4: Model Export
- Save trained model
- Download for deployment

---

## 🧠 Model Architecture

```
Input (21 features)
    ↓
Dense(128, ReLU) + BatchNorm + Dropout(0.3)
    ↓
Dense(64, ReLU) + BatchNorm + Dropout(0.3)
    ↓
Dense(32, ReLU) + BatchNorm + Dropout(0.2)
    ↓
Dense(4, Softmax) → [No Fatigue, Mild, Moderate, Severe]
```

---

## 📈 Expected Results

| Metric | Value |
|--------|-------|
| Training Accuracy | ~95%+ |
| Test Accuracy | ~90%+ |
| Training Time | ~2-3 min |

---

## 🎓 For Presentation

### Key Talking Points
1. **Eye Detection**: Real-time face mesh with 478 landmarks
2. **Blink Detection**: EAR algorithm (scientifically validated)
3. **Fatigue Classification**: Deep learning with 4 classes
4. **Features**: 21 engineered features from eye metrics
5. **Applications**: Screen time monitoring, driver alertness, workplace wellness

### Demo Flow
1. Run Part 1 to show eye detection
2. Run Part 2 to train the model live
3. Use Part 3's interactive sliders for live demo
4. Show confusion matrix for accuracy

---

## 👥 Team

- **Gaurav Kumar Mehta** - Project Lead & ML Engineer
- **Ayan Biswas** - Computer Vision
- **Arpan Mirsha** - Backend Development
- **Arka Bhattacharya** - Frontend & UI

---

## 📧 Contact

For questions, reach out at: gaurav620@github

---

### 👁️ Eye-Guard - Protecting Your Vision with AI
