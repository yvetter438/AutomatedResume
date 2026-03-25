# Resume Generator - MVP Action Plan

## ✅ Current Status

**Server Running:** http://127.0.0.1:5000  
**Database:** 8 jobs loaded, 1 application tracked  
**Backend:** Flask + SQLite + OpenAI API  
**PDF Engine:** LaTeX (MacTeX installed ✓)

---

## 🎯 MVP Goal

**Make this a practical tool for YOU to apply to jobs RIGHT NOW.**

The core workflow should be:
1. Find a job posting
2. Paste job description
3. AI optimizes your resume
4. Download tailored PDF
5. Track application status

---

## 🚀 Critical Path to MVP

### **STEP 1: Test PDF Generation** (5 minutes)

**Test it now:**
1. Go to http://127.0.0.1:5000
2. Scroll to the floating action button (bottom right)
3. Click "Generate Resume" or navigate to the download endpoint
4. Check if PDF downloads successfully

**If it fails:**
- Check terminal output for LaTeX errors
- Look at `/static/temp_resume.pdf` to see if it was created
- LaTeX template is at `templates/resume_template.tex`

**Quick Fix Options:**
- Option A: Fix LaTeX template issues
- Option B: Switch to HTML → PDF (weasyprint, pdfkit)
- Option C: Use a simpler LaTeX template

---

### **STEP 2: Test AI Optimization** (10 minutes)

**Workflow:**
1. Go to Applications page
2. Click "+" to create new application
3. Paste a real job description
4. Select which jobs to include
5. Click "Optimize with AI"
6. Check if AI reorders bullets intelligently

**Current AI Setup:**
- OpenAI API Key: ✓ Configured
- DeepSeek API Key: ⚠️ Empty (optional)
- Model: GPT-4
- Function: `optimize_resume()` in `ai_service.py`

**If AI fails:**
- Check API key is valid
- Check terminal for error messages
- Verify OpenAI account has credits

---

### **STEP 3: Test Full Application Workflow** (15 minutes)

**Create a test application:**
1. Find a real job posting you're interested in
2. Create new application with:
   - Company name
   - Position title
   - Job description (full text)
3. Select 3-4 most relevant jobs from your experience
4. Let AI optimize
5. Generate PDF
6. Track status (Applied → Interviewing → etc.)

**What to verify:**
- [ ] Application saves correctly
- [ ] Jobs link to application
- [ ] PDF generates with selected jobs only
- [ ] Status updates work
- [ ] Can view/edit application later

---

## 🔧 Known Issues to Fix

### **Priority 1: Must Fix for MVP**

1. **Edit Job Functionality Missing**
   - Currently just `console.log('Edit job:', jobId)`
   - Location: `templates/index.html` line 504-507
   - **Fix:** Implement edit modal or make fields editable inline

2. **API Key Security**
   - OpenAI key is hardcoded in `config.py`
   - **Fix:** Move to environment variables or `.env` file
   - Add `config.py` to `.gitignore`

3. **Error Handling**
   - No user-friendly error messages
   - **Fix:** Add try-catch blocks and display errors in UI

### **Priority 2: Nice to Have**

4. **Journal Feature**
   - Fully built but not critical for MVP
   - Use it to log daily accomplishments → convert to resume bullets later

5. **Settings Page**
   - Your info is already configured
   - Test it to make sure contact info is correct

6. **Multiple Resume Versions**
   - Currently generates one PDF at a time
   - Consider saving generated PDFs per application

---

## 📋 MVP Testing Checklist

### **Core Workflow Test:**
- [ ] Create new job experience
- [ ] Edit existing job
- [ ] Reorder jobs (drag & drop)
- [ ] Reorder bullet points
- [ ] Create new application
- [ ] Paste job description
- [ ] AI optimizes resume
- [ ] Generate PDF
- [ ] Download PDF
- [ ] Update application status
- [ ] View application details

### **Edge Cases:**
- [ ] What if AI fails? (fallback to manual order)
- [ ] What if PDF generation fails?
- [ ] What if no jobs selected?
- [ ] What if job description is empty?

---

## 🎨 UI/UX Improvements (Post-MVP)

Your UI is already pretty good! But consider:
- Add loading spinners for AI optimization
- Show preview of resume before downloading
- Add "Copy to clipboard" for resume text
- Show AI's reasoning for reordering
- Add keyboard shortcuts

---

## 🔐 Security & Deployment (Future)

**Current state:** Development only  
**For production:**
- Move API keys to environment variables
- Add user authentication
- Use proper WSGI server (gunicorn)
- Set up proper database backups
- Consider hosting (Heroku, Railway, Fly.io)

---

## 📊 Backend Architecture Summary

```
app.py (Flask routes)
├── /                    → Experience page (CRUD jobs)
├── /resumes             → Applications tracker
├── /journal             → Daily work log
├── /settings            → User profile
├── /optimize-resume     → AI optimization endpoint
├── /generate-pdf        → PDF generation
└── /download-resume     → Download generated PDF

database.py (SQLite operations)
├── jobs                 → Your work experience
├── job_points           → Bullet points per job
├── job_applications     → Applications you've submitted
├── application_jobs     → Which jobs used in each application
├── ai_job_orders        → AI-optimized job ordering
├── ai_point_orders      → AI-optimized bullet ordering
└── journal_entries      → Daily work logs

ai_service.py (AI integration)
├── AIService            → Wrapper for OpenAI/DeepSeek
├── optimize_resume()    → Main AI optimization function
└── test_ai_connection() → API health check
```

---

## 🚦 Next Steps (Right Now)

1. **Test the app** - Click around, try everything
2. **Find one bug** - There's always something
3. **Fix that bug** - Make it work
4. **Apply to one job** - Use it for real
5. **Iterate** - Fix what annoys you

---

## 💡 Pro Tips

- Keep a backup of `resume.db` (it's your data!)
- Use the journal feature to track what you do daily
- AI works best with detailed job descriptions
- Reorder manually if AI gets it wrong
- Keep bullet points concise and quantified

---

## 🆘 Troubleshooting

**Server won't start:**
```bash
source /opt/anaconda3/bin/activate resume-env
python app.py
```

**Database issues:**
```bash
python database.py  # Reinitialize
```

**Check what's running:**
```bash
lsof -i :5000  # See what's on port 5000
```

**Kill the server:**
```bash
pkill -f "python app.py"
```

---

## 📝 Notes

- Your profile is already set up (Yannick Vetter)
- You have 8 jobs with solid experience
- One application already tracked (Arkero)
- LaTeX is installed and working
- OpenAI API key is configured

**You're 90% there. Just test and fix what breaks!**
