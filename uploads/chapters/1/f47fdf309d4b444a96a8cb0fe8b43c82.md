# Project Setup Guide

## Overview
This guide will help you set up the database and deploy the backend application to Render.

---

## 📋 Prerequisites

- GitHub account
- Neon database account (https://neon.tech)
- Render account (https://render.com)
- The database backup file: `database_backup.sql`

---

## 🗄️ Part 1: Database Setup (Neon)

### Step 1: Create Neon Account & Project

1. Go to https://neon.tech and sign up/login
2. Click **"Create Project"**
3. Choose a project name (e.g., `your-project-db`)
4. Select your preferred region
5. Click **"Create Project"**

### Step 2: Get Your Connection String

1. In your Neon dashboard, go to **"Dashboard"**
2. You'll see the connection string in the format:
   ```
   postgresql://username:password@ep-xxxxx.region.aws.neon.tech/dbname?sslmode=require
   ```
3. **Copy this** - you'll need it for importing data and for Render

### Step 3: Import the Database

**Option A: Using Command Line (Recommended)**

If you have PostgreSQL installed:
```bash
psql "your-neon-connection-string" < database_backup.sql
```

**Option B: Using pgAdmin**

1. Open pgAdmin
2. Register a new server with your Neon connection details
3. Right-click your database → **"Restore"**
4. Select the `database_backup.sql` file
5. Click **"Restore"**

### Step 4: Verify the Import

Connect to your database and check:
```bash
psql "your-neon-connection-string"
```

Then run:
```sql
\dt              -- List all tables
SELECT COUNT(*) FROM your_main_table;  -- Verify data
\q               -- Exit
```

---

## 🚀 Part 2: Backend Deployment (Render)

### Step 1: Push Code to GitHub

1. Create a new GitHub repository (e.g., `project-backend`)
2. Push your backend code to the repository:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/your-username/project-backend.git
   git push -u origin main
   ```

### Step 2: Create Render Account

1. Go to https://render.com
2. Sign up using your GitHub account (recommended)
3. Authorize Render to access your repositories

### Step 3: Deploy Backend on Render

1. From Render dashboard, click **"New +"** → **"Web Service"**
2. Connect your GitHub repository
3. Configure the service:

   **Basic Settings:**
   - **Name**: `your-project-backend` (or any name)
   - **Region**: Choose closest to your users
   - **Branch**: `main`
   - **Root Directory**: Leave blank (unless your backend is in a subfolder)
   
   **Build Settings:**
   - **Runtime**: Select based on your backend
     - Node.js: `Node`
     - Python: `Python`
     - Go: `Go`
     - etc.
   
   - **Build Command**: (examples)
     ```bash
     
     
     # For Python
     pip install -r requirements.txt
     ```
    
   
   - **Start Command**: (examples)
     ```bash
     
     # For Python/FastAPI
     uvicorn main:app --host 0.0.0.0 --port $PORT
     
     
     ```

4. Click **"Advanced"** to add environment variables (see next step)

### Step 4: Configure Environment Variables

Click **"Add Environment Variable"** and add all your variables:

#### Required Variables:

| Key | Value | Description |
|-----|-------|-------------|
| `DATABASE_URL` | `postgresql://username:password@ep-xxxxx.region.aws.neon.tech/dbname?sslmode=require` | Your Neon connection string |
| `PORT` | `10000` | Render provides this automatically |
| `NODE_ENV` | `production` | Environment mode |

#### Common Additional Variables:

| Key | Example Value | Description |
|-----|---------------|-------------|
| `JWT_SECRET` | `your-secret-key-here` | JWT signing secret |
| `API_KEY` | `your-api-key` | External API keys |
| `CORS_ORIGIN` | `https://your-frontend.com` | Allowed CORS origins |
| `SESSION_SECRET` | `your-session-secret` | Session secret |
| `100MS_SECRET` | `your-session-secret` | 100MS secret |


**Security Note:** Never commit these values to GitHub. Only add them in Render's environment variables section.

### Step 5: Deploy

1. Click **"Create Web Service"**
2. Render will automatically:
   - Clone your repository
   - Install dependencies
   - Build your application
   - Deploy it

3. Monitor the deployment in the **"Logs"** section
4. Once deployed, you'll get a URL like: `https://your-project-backend.onrender.com`

---

## 🔧 Environment Variables Template

Create a `.env.example` file in your repository (without actual values):

```env
# Database
DATABASE_URL=postgresql://username:password@host/dbname

# Server
PORT=10000
NODE_ENV=production

# Authentication
JWT_SECRET=your-jwt-secret-here
SESSION_SECRET=your-session-secret-here

# CORS
CORS_ORIGIN=https://your-frontend-domain.com

# External APIs (if applicable)
API_KEY=your-api-key
```

---

## 📝 Post-Deployment Checklist

- [ ] Database imported successfully
- [ ] All environment variables added in Render
- [ ] Backend deployed without errors
- [ ] Backend URL accessible
- [ ] Database connection working (check logs)
- [ ] API endpoints responding correctly
- [ ] CORS configured properly (if frontend is separate)

---

## 🧪 Testing the Deployment

### Test Database Connection

```bash
# Make a test API call
curl https://your-project-backend.onrender.com/health

# Or test a specific endpoint
curl https://your-project-backend.onrender.com/api/users
```

### Check Render Logs

1. Go to your Render dashboard
2. Click on your service
3. Go to **"Logs"** tab
4. Look for any errors or connection issues

---

## 🔍 Troubleshooting

### Database Connection Issues

**Problem**: `Connection refused` or `Connection timeout`

**Solution**:
- Verify your `DATABASE_URL` is correct
- Check Neon database is running
- Ensure `sslmode=require` is in connection string
- Whitelist Render's IP in Neon (usually not needed)

### Build Failures

**Problem**: Build fails on Render

**Solution**:
- Check build logs for specific errors
- Verify `package.json` or `requirements.txt` is present
- Ensure all dependencies are listed
- Check Node/Python version compatibility

### Port Binding Issues

**Problem**: Application crashes with port errors

**Solution**:
```javascript
// Ensure your app uses Render's PORT
const PORT = process.env.PORT || 3000;
app.listen(PORT, '0.0.0.0', () => {
  console.log(`Server running on port ${PORT}`);
});
```

### CORS Errors

**Problem**: Frontend can't access backend

**Solution**:
```javascript
// Add CORS middleware
const cors = require('cors');
app.use(cors({
  origin: process.env.CORS_ORIGIN || '*'
}));
```

---

## 🔄 Updating the Application

### Auto-Deploy on Git Push

Render automatically redeploys when you push to your connected branch:

```bash
git add .
git commit -m "Update feature"
git push origin main
```

Render will detect the push and redeploy automatically.

### Manual Deploy

1. Go to Render dashboard
2. Click your service
3. Click **"Manual Deploy"** → **"Deploy latest commit"**

---

## 📞 Support & Resources

- **Neon Documentation**: https://neon.tech/docs
- **Render Documentation**: https://render.com/docs
- **Render Community**: https://community.render.com

---

## 🔐 Security Best Practices

1. ✅ Never commit `.env` files to GitHub
2. ✅ Use strong, unique secrets for JWT and sessions
3. ✅ Keep dependencies updated
4. ✅ Use environment variables for all sensitive data
5. ✅ Enable HTTPS only (Render does this automatically)
6. ✅ Regularly backup your database
7. ✅ Monitor Render logs for suspicious activity

---

## 📊 Monitoring

### Free Tier Limitations (Render)

- Services spin down after 15 minutes of inactivity
- First request after spin-down takes 30-60 seconds
- 750 hours/month free (sufficient for one service)

### Keep Service Alive (Optional)

Use a service like UptimeRobot or Cron-job.org to ping your backend every 10 minutes:
```
https://your-project-backend.onrender.com/health
```

---

## 🎯 Next Steps

1. Import database to Neon ✓
2. Push code to GitHub ✓
3. Deploy to Render ✓
4. Configure environment variables ✓
5. Test all endpoints ✓
6. Connect your frontend to the backend URL
7. Monitor and maintain

---

**Created**: [Date]  
**Last Updated**: [Date]  
**Maintained By**: [Your Organization Name]
