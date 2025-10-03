# 🚀 Deploying to Vercel

This guide will help you deploy your Interactive Flashcard Study Session app to Vercel.

## Prerequisites

- A [GitHub](https://github.com) account
- A [Vercel](https://vercel.com) account (you can sign up with your GitHub account)
- Git installed on your computer

## Step-by-Step Deployment

### Option 1: Deploy via Vercel Dashboard (Recommended)

#### 1. Push Your Code to GitHub

```bash
# Navigate to your frontend directory
cd /Users/arunkumarmurugesan/Documents/entreprenuer-apps/self-learning-ai/frontend

# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: Interactive Flashcard Study App"

# Create a new repository on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git branch -M main
git push -u origin main
```

#### 2. Deploy on Vercel

1. Go to [vercel.com](https://vercel.com) and sign in
2. Click **"Add New Project"**
3. Click **"Import Git Repository"**
4. Select your repository from the list
5. Configure your project:
   - **Framework Preset:** Vite
   - **Root Directory:** `frontend` (if deploying from root repo) OR leave as `.` (if deploying just the frontend folder)
   - **Build Command:** `npm run build` (should be auto-detected)
   - **Output Directory:** `dist` (should be auto-detected)
6. Click **"Deploy"**

#### 3. Wait for Deployment

Vercel will:
- Install dependencies
- Build your project
- Deploy to a live URL
- Give you a URL like: `https://your-app-name.vercel.app`

### Option 2: Deploy via Vercel CLI

```bash
# Install Vercel CLI globally
npm install -g vercel

# Navigate to frontend directory
cd /Users/arunkumarmurugesan/Documents/entreprenuer-apps/self-learning-ai/frontend

# Login to Vercel
vercel login

# Deploy
vercel

# For production deployment
vercel --prod
```

## Configuration Files

Your project includes:

- ✅ `vercel.json` - Vercel configuration
- ✅ `package.json` - Dependencies and build scripts
- ✅ `vite.config.js` - Vite configuration

## Post-Deployment

### Custom Domain (Optional)

1. Go to your project on Vercel dashboard
2. Click **"Settings"** → **"Domains"**
3. Add your custom domain
4. Follow DNS configuration instructions

### Environment Variables (If Needed)

If you need environment variables:
1. Go to **"Settings"** → **"Environment Variables"**
2. Add your variables
3. Redeploy

## Troubleshooting

### Build Fails

- Check that all dependencies are in `package.json`
- Ensure `node_modules` is in `.gitignore`
- Verify build works locally: `npm run build`

### 404 Errors on Refresh

- The `vercel.json` file handles this with rewrites
- Ensures React Router works correctly

### Mermaid Diagrams Not Showing

- Mermaid works on Vercel
- Check browser console for errors
- Ensure JSON file is in `public` folder

## Local Testing Before Deploy

```bash
# Build the project
npm run build

# Preview the production build
npm run preview
```

This will start a local server with the production build, so you can test before deploying.

## Updating Your App

Every time you push to your GitHub repository, Vercel will automatically:
1. Detect the changes
2. Build the new version
3. Deploy it live

No manual redeployment needed! 🎉

## Your App Features

✅ Interactive flashcards with flip animation  
✅ Mermaid diagram rendering  
✅ Smart quiz with visual feedback  
✅ Performance scorecard  
✅ Responsive design  
✅ Fast loading with Vite  

## Support

- Vercel Documentation: https://vercel.com/docs
- Vite Documentation: https://vitejs.dev/
- React Documentation: https://react.dev/

---

Happy Studying! 📚✨

