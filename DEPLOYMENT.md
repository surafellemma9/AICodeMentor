# 🚀 LeetAI Deployment Guide

Your LeetAI is now ready for deployment! Here are the best options to make it public:

## 🎯 **Recommended: Railway (Free & Easy)**

### Step 1: Prepare Your Repository
1. **Push your code to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/LeetAI.git
   git push -u origin main
   ```

### Step 2: Deploy on Railway
1. **Go to [Railway](https://railway.app/)**
2. **Sign up/Login** with your GitHub account
3. **Click "New Project"** → "Deploy from GitHub repo"
4. **Select your LeetAI repository**
5. **Add Environment Variables:**
   - `OPENROUTER_API_KEY`: `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`
   - `SECRET_KEY`: Generate a new one at [Django Secret Key Generator](https://djecrety.ir/)
6. **Deploy!** Your app will be live at `https://your-app-name.railway.app`

---

## 🌐 **Alternative: Render (Free Tier)**

### Step 1: Deploy on Render
1. **Go to [Render](https://render.com/)**
2. **Sign up/Login** with GitHub
3. **Click "New"** → "Web Service"
4. **Connect your GitHub repo**
5. **Configure:**
   - **Name**: `leetai`
   - **Environment**: `Python 3`
   - **Build Command**: `./build.sh`
   - **Start Command**: `gunicorn LeetAI.wsgi:application`
6. **Add Environment Variables:**
   - `OPENROUTER_API_KEY`: Your API key
   - `SECRET_KEY`: New Django secret key
7. **Deploy!** Your app will be live at `https://your-app-name.onrender.com`

---

## 🔧 **Environment Variables to Set:**

```bash
OPENROUTER_API_KEY=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
SECRET_KEY=your-new-secret-key-here
```

---

## 📱 **Share with Collaborators:**

Once deployed, you'll get a public URL like:
- `https://leetai.railway.app`
- `https://leetai.onrender.com`

**Share this URL with your collaborators!** 🎉

---

## 🔒 **Security Notes:**

1. **Never commit API keys** to GitHub
2. **Use environment variables** for sensitive data
3. **Generate a new Django secret key** for production
4. **Keep your OpenRouter API key secure**

---

## 🛠 **Troubleshooting:**

### If deployment fails:
1. **Check the logs** in your deployment platform
2. **Verify environment variables** are set correctly
3. **Ensure all files** are committed to GitHub
4. **Check Python version** compatibility

### If the app doesn't work:
1. **Check the API key** is correct
2. **Verify the URL** is accessible
3. **Check deployment logs** for errors

---

## 🎊 **You're Ready!**

Your LeetAI will be live and accessible to anyone with the URL. Your collaborators can:
- ✅ **Ask coding questions**
- ✅ **Upload code files**
- ✅ **Get AI-powered guidance**
- ✅ **Access from anywhere**

**Happy coding!** 🚀 