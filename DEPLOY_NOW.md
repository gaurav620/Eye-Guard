# Eyeguard - Quick Deployment Guide

## 🚀 Deploy to Render.com (FREE & EASIEST)

### Step 1: Prepare Repository

```bash
cd /Users/sauravkumar/CODE_FOR_TEST/Eye-Guard

# Initialize git if not already
git init
git add .
git commit -m "Initial commit - Eyeguard Full Stack App"

# Create GitHub repository and push
# Go to github.com, create new repo "Eye-Guard"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/Eye-Guard.git
git push -u origin main
```

### Step 2: Deploy to Render

1. **Go to**: https://render.com
2. **Sign up** with GitHub
3. **Click**: "New +" → "Web Service"
4. **Connect** your GitHub repository "Eye-Guard"
5. **Configure**:
   - **Name**: eyeguard-api
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements-prod.txt`
   - **Start Command**: `gunicorn api.app:app --bind 0.0.0.0:$PORT`
   - **Plan**: Free
6. **Click**: "Create Web Service"
7. **Wait** ~5 minutes for deployment

### Step 3: Update Dashboard

Once deployed, you'll get a URL like: `https://eyeguard-api.onrender.com`

Update `web/dashboard.html`:
```javascript
// Change line 184:
const API_URL = 'https://eyeguard-api.onrender.com/api';
```

### Step 4: Deploy Dashboard (Vercel - FREE)

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy web dashboard
cd web
vercel --prod

# Your dashboard will be live at: https://your-app.vercel.app
```

---

## Alternative: Deploy to Heroku

```bash
# Install Heroku CLI
brew install heroku/brew/heroku

# Login
heroku login

# Create app
heroku create eyeguard-api

# Deploy
git push heroku main

# Open
heroku open
```

---

## Alternative: Use Netlify Drop

1. Go to: https://app.netlify.com/drop
2. Drag and drop the `web` folder
3. Get instant live URL
4. Update API_URL in dashboard.html to your Render URL

---

## ✅ Post-Deployment Checklist

- [ ] API is accessible at your Render URL
- [ ] Test: `https://your-app.onrender.com/api/health`
- [ ] Dashboard updated with correct API URL
- [ ] Dashboard deployed to Vercel/Netlify
- [ ] CORS configured correctly
- [ ] Database persisting (check Render disk)

---

## 🎯 **Your Live URLs** (After Deployment):

- **API**: https://eyeguard-api.onrender.com
- **Web**: https://eyeguard.vercel.app
- **Docs**: Share your GitHub repo

---

## 📱 For Mobile App Deployment:

### React Native (Expo)
```bash
expo publish
# Scan QR code with Expo Go app
```

### Flutter
```bash
flutter build apk
flutter build ios
```

---

**Status**: ✅ Ready for deployment!
**Time**: ~10 minutes total
**Cost**: FREE (Render Free + Vercel Free)
