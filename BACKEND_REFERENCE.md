# Backend Reference Guide

## 🏗️ Architecture Overview

**Stack:** Flask + SQLite + OpenAI API + LaTeX  
**Pattern:** Traditional server-side rendering with Jinja2 templates  
**Database:** SQLite (`resume.db`) - single file, no setup needed

---

## 📁 File Structure

```
resume-generator/
├── app.py                 # Main Flask application (575 lines)
├── database.py            # All database operations (1069 lines)
├── ai_service.py          # AI/LLM integration (156 lines)
├── config.py              # API keys (2 lines)
├── resume.db              # SQLite database
├── templates/             # Jinja2 HTML templates
│   ├── base.html          # Base layout with nav
│   ├── index.html         # Experience management
│   ├── resumes.html       # Application tracker
│   ├── journal.html       # Daily work log
│   ├── settings.html      # User profile
│   └── resume_template.tex # LaTeX resume template
└── static/                # Generated PDFs, CSS, JS
```

---

## 🗄️ Database Schema

### **Core Tables**

**jobs** - Your work experience
```sql
id, title, company, location, start_date, end_date, 
current (boolean), display_order
```

**job_points** - Bullet points for each job
```sql
id, job_id (FK), point (text), order_num
```

**job_applications** - Applications you've submitted
```sql
id, company, title, application_date, status, 
job_description, story, resume_path, created_at
```

**application_jobs** - Links jobs to applications
```sql
id, application_id (FK), job_id (FK), display_order
```

**application_points** - Which bullets used in each application
```sql
id, application_id (FK), point_id (FK), display_order
```

### **AI Optimization Tables**

**ai_job_orders** - AI-suggested job ordering
```sql
id, job_id (FK), ai_display_order, model_type, created_at
```

**ai_point_orders** - AI-suggested bullet ordering
```sql
id, job_id (FK), point_id (FK), ai_order_num, 
relevance_score, model_type, created_at
```

### **User Data**

**user_settings** - Your profile (single row)
```sql
id, full_name, email, phone, location,
linkedin_url, github_url, website_url, my_story,
jobs_on_resume (default: 4), points_per_job (default: 3)
```

### **Journal Tables**

**journal_entries** - Daily work logs
```sql
id, job_id (FK), entry_date, title, content,
hours_worked, category, mood, is_highlight, created_at
```

**journal_tags** - Tag system
```sql
id, name, color
```

**journal_entry_tags** - Many-to-many relationship
```sql
entry_id (FK), tag_id (FK)
```

---

## 🛣️ API Routes

### **Experience Management**

| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | Experience page (main view) |
| `/add-job` | POST | Create new job |
| `/delete-job/<id>` | POST | Delete job and all points |
| `/add-point/<job_id>` | POST | Add bullet point to job |
| `/delete-point/<id>` | POST | Delete bullet point |
| `/update-order` | POST | Reorder jobs (drag & drop) |
| `/update-point-order/<job_id>` | POST | Reorder points |

### **AI Optimization**

| Route | Method | Description |
|-------|--------|-------------|
| `/test-ai/<model_type>` | GET | Test AI connection |
| `/optimize-resume` | POST | AI optimizes job/point order |
| `/get-resume-view` | GET | Get jobs in AI-optimized order |

### **PDF Generation**

| Route | Method | Description |
|-------|--------|-------------|
| `/download-resume` | GET | Generate & download PDF |
| `/generate-pdf` | GET | Alternative PDF endpoint |
| `/generate-application-resume/<id>` | GET | PDF for specific application |

### **Application Tracking**

| Route | Method | Description |
|-------|--------|-------------|
| `/resumes` | GET | Applications page |
| `/create-application` | POST | Create new application |
| `/application/<id>` | GET | Get application details (JSON) |
| `/update-status/<id>` | POST | Update application status |
| `/delete-application/<id>` | POST | Delete application |
| `/download-application-resume/<id>` | GET | Download uploaded resume |

### **Journal**

| Route | Method | Description |
|-------|--------|-------------|
| `/journal` | GET | Journal page |
| `/journal/entry` | POST | Create journal entry |
| `/journal/entry/<id>` | GET | Get single entry |
| `/journal/entry/<id>` | PUT | Update entry |
| `/journal/entry/<id>` | DELETE | Delete entry |
| `/journal/stats` | GET | Get statistics |
| `/journal/calendar` | GET | Calendar view data |

### **Settings**

| Route | Method | Description |
|-------|--------|-------------|
| `/settings` | GET | Settings page |
| `/settings/save` | POST | Save user settings |

### **Utility**

| Route | Method | Description |
|-------|--------|-------------|
| `/api/jobs` | GET | Get all jobs as JSON |

---

## 🤖 AI Service

### **AIService Class**

```python
from ai_service import AIService, AIModel

# Initialize
ai = AIService(AIModel.OPENAI)  # or AIModel.DEEPSEEK

# Optimize resume
success, result = ai.optimize_resume(
    jobs=jobs_list,
    job_description="...",
    story="..."
)

# Result format:
{
    "job_order": {
        1: 1,  # job_id: order_number
        2: 2
    },
    "point_orders": {
        1: {  # job_id
            "1": {"order": 1, "score": 0.95},  # point_id
            "2": {"order": 2, "score": 0.85}
        }
    }
}
```

### **How AI Optimization Works**

1. User pastes job description
2. System sends to GPT-4 with:
   - All your jobs and bullet points
   - Target job description
   - Your personal story/narrative
3. AI returns optimized ordering with relevance scores
4. System stores in `ai_job_orders` and `ai_point_orders`
5. User can toggle between "handcrafted" and "AI" view
6. PDF generation uses selected ordering

---

## 📄 PDF Generation Flow

```python
def generate_pdf(mode='handcrafted', model_type='openai'):
    # 1. Get jobs (either manual or AI order)
    if mode == 'handcrafted':
        jobs = get_all_jobs()
    else:
        jobs = get_ai_ordered_jobs(model_type)
    
    # 2. Take first 4 jobs, first 3 points each
    resume_jobs = jobs[:4]
    
    # 3. Render LaTeX template
    template = env.get_template('resume_template.tex')
    rendered_tex = template.render(**experience_data)
    
    # 4. Write to temp file
    with open('static/temp_resume.tex', 'w') as f:
        f.write(rendered_tex)
    
    # 5. Run pdflatex
    subprocess.run([
        '/Library/TeX/texbin/pdflatex',
        '-output-directory', 'static',
        'static/temp_resume.tex'
    ])
    
    # 6. Return PDF path
    return 'static/temp_resume.pdf'
```

**LaTeX Template Variables:**
- `job1`, `job2`, `job3`, `job4`
- Each has: `dates`, `title`, `company`, `location`, `points`

---

## 🔑 Key Database Functions

### **Job Management**

```python
from database import *

# Get all jobs (ordered)
jobs = get_all_jobs()

# Add new job
job_id = add_job(
    title="Software Engineer",
    company="Google",
    location="Mountain View, CA",
    start_date="2023-01",
    end_date="2024-01",
    current=False
)

# Add bullet point
add_job_points(job_id, "Built cool stuff", order_num=1)

# Delete job
delete_job_and_points(job_id)

# Reorder jobs
update_job_order([
    {'id': 1, 'order': 2},
    {'id': 2, 'order': 1}
])
```

### **Application Management**

```python
# Create application
app_id = create_application(
    company="Google",
    title="Software Engineer",
    application_date="2024-03-25",
    job_description="...",
    story="...",
    job_ids=[1, 2, 3],  # Which jobs to include
    point_selections={1: 1, 2: 2},  # point_id: order
    resume_path="/path/to/resume.pdf"
)

# Get application
app = get_application(app_id)

# Update status
update_application(app_id, status='interviewing')

# Delete application
delete_application(app_id)
```

### **Journal**

```python
# Create entry
entry_id = create_journal_entry(
    job_id=1,
    entry_date="2024-03-25",
    content="Shipped new feature!",
    title="Big Win",
    hours_worked=8.0,
    category='accomplishment',
    mood='great',
    is_highlight=True,
    tags=['python', 'leadership']
)

# Get entries
entries = get_journal_entries(
    job_id=1,
    start_date="2024-01-01",
    limit=50
)

# Get stats
stats = get_journal_stats(job_id=1)
# Returns: total_entries, total_hours, highlights, by_category, streak
```

---

## 🎨 Frontend Stack

**No JavaScript Framework** - Vanilla JS with:
- Drag & drop (native HTML5)
- Fetch API for AJAX
- Modal dialogs (custom CSS)
- Form handling

**CSS:**
- Custom design system with CSS variables
- Dark theme
- Responsive (mobile-friendly)
- No framework (no Bootstrap, Tailwind, etc.)

**Templates:**
- Jinja2 server-side rendering
- Base template with shared nav
- Each page extends base

---

## 🔧 Configuration

### **Environment Variables (Recommended)**

Create `.env` file:
```
OPENAI_API_KEY=sk-...
DEEPSEEK_API_KEY=sk-...
FLASK_ENV=development
FLASK_DEBUG=True
```

Then update `config.py`:
```python
import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')
```

### **Settings in Database**

```python
settings = get_settings()
# Returns:
{
    'full_name': 'Yannick Vetter',
    'email': 'yannick.vetter@ndsu.edu',
    'phone': '701-730-4709',
    'location': '',
    'linkedin_url': 'https://linkedin.com/in/yannickvetter',
    'github_url': 'https://github.com/yvetter438',
    'website_url': 'https://yannickvetter.com',
    'my_story': '',
    'jobs_on_resume': 4,
    'points_per_job': 3
}
```

---

## 🐛 Debugging

### **Check Database**

```bash
sqlite3 resume.db

# Useful queries:
SELECT * FROM jobs;
SELECT * FROM job_applications;
SELECT * FROM user_settings;
.schema jobs  # See table structure
.tables       # List all tables
```

### **Check Logs**

Flask prints to terminal where you ran `python app.py`

### **Test API Endpoints**

```bash
# Test AI connection
curl http://localhost:5000/test-ai/openai

# Get jobs as JSON
curl http://localhost:5000/api/jobs
```

---

## 🚀 Performance Notes

- SQLite is fast enough for single-user
- No caching implemented
- AI calls can take 5-10 seconds
- PDF generation takes 1-2 seconds
- All synchronous (no async/await)

---

## 🔒 Security Considerations

**Current state:** Development only, single-user

**Issues:**
- No authentication
- API keys in code
- No CSRF protection
- No rate limiting
- SQL injection protected (using parameterized queries ✓)

**For production:**
- Add Flask-Login for auth
- Use environment variables
- Add Flask-WTF for CSRF
- Use Flask-Limiter
- Deploy with gunicorn + nginx

---

## 📦 Dependencies

```
flask
jinja2
openai
werkzeug
sqlite3 (built-in)
```

**System dependencies:**
- MacTeX (for pdflatex)
- Python 3.10+

---

## 💡 Extension Ideas

1. **Multiple resume templates** - Switch between styles
2. **Cover letter generation** - AI writes cover letters
3. **LinkedIn sync** - Import from LinkedIn
4. **Export formats** - Word, HTML, Markdown
5. **Analytics** - Track application success rate
6. **Email integration** - Auto-track applications from Gmail
7. **Browser extension** - One-click apply with auto-fill

---

## 🆘 Common Issues

**PDF won't generate:**
- Check LaTeX is installed: `which pdflatex`
- Check template syntax: `templates/resume_template.tex`
- Look for `.log` files in `static/` folder

**AI not working:**
- Verify API key: `echo $OPENAI_API_KEY`
- Check OpenAI account has credits
- Look at terminal for error messages

**Database locked:**
- Close any SQLite browser tools
- Restart Flask server

**Port 5000 in use:**
- Kill process: `lsof -ti:5000 | xargs kill -9`
- Or change port in `app.py`: `app.run(port=5001)`

---

## 📚 Code Quality Notes

**Good:**
- Clean separation of concerns
- Proper foreign keys in database
- Parameterized SQL queries
- Comprehensive error handling in database layer

**Could improve:**
- Add type hints
- Write unit tests
- Add logging (instead of print statements)
- Extract magic numbers to constants
- Add docstrings to functions

---

**This is a solid foundation. The architecture is simple, maintainable, and gets the job done!**
