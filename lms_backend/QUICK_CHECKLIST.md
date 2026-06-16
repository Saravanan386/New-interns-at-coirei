# Quick Setup Checklist

## 📦 Files You Need

- [ ] `database_backup.sql` - Database export file
- [ ] Backend code repository
- [ ] `.env.example` - Environment variables template

---

## ⚡ Quick Start Steps

### 1. Database Setup (15 minutes)
- [ ] Create Neon account → https://neon.tech
- [ ] Create new project
- [ ] Copy connection string
- [ ] Import `database_backup.sql`
- [ ] Verify data imported

### 2. GitHub Setup (5 minutes)
- [ ] Create GitHub repository
- [ ] Push backend code
- [ ] Verify code is pushed

### 3. Render Setup (10 minutes)
- [ ] Create Render account → https://render.com
- [ ] Connect GitHub account
- [ ] Create new Web Service
- [ ] Connect your repository
- [ ] Configure build & start commands

### 4. Environment Variables (5 minutes)
- [ ] Add `DATABASE_URL` from Neon
- [ ] Add `PORT` = 10000
- [ ] Add `NODE_ENV` = production
- [ ] Add `JWT_SECRET` (generate new one)
- [ ] Add other required variables
- [ ] Save and deploy

### 5. Testing (5 minutes)
- [ ] Check deployment logs
- [ ] Test backend URL
- [ ] Verify database connection
- [ ] Test API endpoints

---

## 🔑 Critical Information to Collect

```
Neon Database URL:
postgresql://[username]:[password]@[host]/[dbname]?sslmode=require

Render Backend URL (after deployment):
https://[your-service-name].onrender.com

GitHub Repository:
https://github.com/[username]/[repo-name]
```

---

## ⚠️ Common Issues

| Issue | Solution |
|-------|----------|
| Build fails | Check build command matches your framework |
| Database connection error | Verify DATABASE_URL is correct with `?sslmode=require` |
| Port error | Use `process.env.PORT` in your code |
| CORS error | Add CORS middleware with proper origin |

---

## 🆘 Need Help?

1. Check the detailed `PROJECT_SETUP_README.md`
2. Review Render logs for errors
3. Verify all environment variables are set
4. Test database connection separately

---

**Total Setup Time: ~40 minutes**
