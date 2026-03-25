# Quick Start Guide

## 🚀 Your App is Ready!

**URL:** http://127.0.0.1:5000

---

## ✅ What I Just Built For You

### **1. Resume Generation (Main Feature)**
Two ways to generate your resume:

**Option A: Quick Resume**
- Click "Quick Resume" button
- Uses your current job/bullet order
- Instant PDF download

**Option B: AI-Optimized Resume**
- Click "AI-Optimized" button
- Paste job description
- AI picks best bullets and reorders
- PDF downloads after ~10 seconds

### **2. Education Section**
- New page in navigation (graduation cap icon)
- Add your degrees, schools, GPAs
- Automatically included in resume

### **3. Bug Fixes**
- Removed 9 duplicate bullet points
- Resume now uses your Settings (4 jobs, 3 bullets each)
- LaTeX template pulls from your actual data

---

## 📋 First-Time Setup Checklist

- [ ] **Add your education** (click graduation cap icon)
- [ ] **Verify Settings** (click gear icon)
  - Check name, email, phone
  - Verify LinkedIn, GitHub, website
- [ ] **Review your jobs** (main page)
  - Make sure all experience is current
  - Reorder if needed (drag & drop)
- [ ] **Test PDF generation** (click "Quick Resume")

---

## 🎯 Apply to Your First Job

1. Find a job posting you like
2. Copy the full job description
3. Go to http://127.0.0.1:5000
4. Click "AI-Optimized"
5. Paste job description
6. Click "Optimize & Generate Resume"
7. Download PDF
8. Go to Applications page
9. Track the application

---

## 🔑 Key Features

| Feature | Location | What It Does |
|---------|----------|--------------|
| Quick Resume | Main page | Generate PDF with current order |
| AI-Optimized | Main page | AI tailors resume to job description |
| Education | Sidebar (🎓) | Manage your education |
| Experience | Sidebar (💼) | Manage jobs & bullets |
| Applications | Sidebar (✈️) | Track job applications |
| Journal | Sidebar (📖) | Log daily work |
| Settings | Sidebar (⚙️) | Configure contact info |

---

## 💻 Commands

**Start server:**
```bash
source /opt/anaconda3/bin/activate resume-env
python app.py
```

**Stop server:**
```bash
lsof -ti:5000 | xargs kill -9
```

**Check database:**
```bash
sqlite3 resume.db "SELECT * FROM jobs;"
```

---

## 📁 Important Files

- `app.py` - Main Flask application
- `database.py` - All database operations
- `ai_service.py` - AI/OpenAI integration
- `config.py` - API keys (keep secret!)
- `resume.db` - Your data (backup this!)
- `templates/resume_template.tex` - LaTeX resume template

---

## 🐛 If Something Breaks

**Server won't start:**
- Port 5000 in use? Kill it: `lsof -ti:5000 | xargs kill -9`
- Check terminal for error messages

**PDF won't generate:**
- Check LaTeX is installed: `which pdflatex`
- Look for `.log` files in `static/` folder
- Check you have at least 1 job

**AI fails:**
- Verify OpenAI API key in `config.py`
- Check API credits at platform.openai.com
- Try DeepSeek model instead

---

## 📊 Your Current Status

✅ **Fixed:** Duplicate bullet points removed  
✅ **Added:** Education section with full CRUD  
✅ **Added:** Resume generation panel  
✅ **Added:** AI optimization with job description  
✅ **Updated:** LaTeX template to be dynamic  
✅ **Server:** Running on port 5000  

---

## 🎓 What's Next?

1. **Add your education** - Don't forget this!
2. **Generate a test resume** - Make sure PDF works
3. **Try AI optimization** - Paste a real job description
4. **Apply to a job** - Use it for real!

---

**Need help?** Check these files:
- `WHATS_NEW.md` - Detailed feature list
- `MVP_ACTION_PLAN.md` - MVP roadmap
- `BACKEND_REFERENCE.md` - Technical docs

**Ready to apply to jobs! 🚀**
