import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect('resume.db')
    c = conn.cursor()
    
    # Create tables
    c.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT,
            current BOOLEAN DEFAULT 0,
            display_order INTEGER
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS job_points (
            id INTEGER PRIMARY KEY,
            job_id INTEGER,
            point TEXT NOT NULL,
            order_num INTEGER,
            FOREIGN KEY (job_id) REFERENCES jobs (id)
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS ai_job_orders (
            id INTEGER PRIMARY KEY,
            job_id INTEGER,
            ai_display_order INTEGER,
            model_type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES jobs (id)
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS ai_point_orders (
            id INTEGER PRIMARY KEY,
            job_id INTEGER,
            point_id INTEGER,
            ai_order_num INTEGER,
            relevance_score FLOAT,
            model_type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES jobs (id),
            FOREIGN KEY (point_id) REFERENCES job_points (id)
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS job_applications (
            id INTEGER PRIMARY KEY,
            company TEXT NOT NULL,
            title TEXT NOT NULL,
            application_date TEXT NOT NULL,
            status TEXT CHECK(status IN ('applied', 'interviewing', 'rejected', 'accepted')) NOT NULL DEFAULT 'applied',
            job_description TEXT,
            story TEXT,
            model_type TEXT,
            resume_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # User settings table (single row for now, can expand to multi-user later)
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_settings (
            id INTEGER PRIMARY KEY DEFAULT 1,
            full_name TEXT,
            email TEXT,
            phone TEXT,
            location TEXT,
            linkedin_url TEXT,
            github_url TEXT,
            website_url TEXT,
            my_story TEXT,
            jobs_on_resume INTEGER DEFAULT 4,
            points_per_job INTEGER DEFAULT 3,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert default settings row if not exists
    c.execute('''
        INSERT OR IGNORE INTO user_settings (id) VALUES (1)
    ''')
    
    # Application-Jobs linking table (which jobs were used in each application)
    c.execute('''
        CREATE TABLE IF NOT EXISTS application_jobs (
            id INTEGER PRIMARY KEY,
            application_id INTEGER NOT NULL,
            job_id INTEGER NOT NULL,
            display_order INTEGER,
            FOREIGN KEY (application_id) REFERENCES job_applications (id) ON DELETE CASCADE,
            FOREIGN KEY (job_id) REFERENCES jobs (id),
            UNIQUE(application_id, job_id)
        )
    ''')
    
    # Application-specific point orders (which points and in what order for each application)
    c.execute('''
        CREATE TABLE IF NOT EXISTS application_points (
            id INTEGER PRIMARY KEY,
            application_id INTEGER NOT NULL,
            point_id INTEGER NOT NULL,
            display_order INTEGER,
            FOREIGN KEY (application_id) REFERENCES job_applications (id) ON DELETE CASCADE,
            FOREIGN KEY (point_id) REFERENCES job_points (id),
            UNIQUE(application_id, point_id)
        )
    ''')
    
    # ============================================
    # Daily Work Journal
    # ============================================
    c.execute('''
        CREATE TABLE IF NOT EXISTS journal_entries (
            id INTEGER PRIMARY KEY,
            job_id INTEGER NOT NULL,
            entry_date DATE NOT NULL,
            title TEXT,
            content TEXT NOT NULL,
            hours_worked REAL,
            category TEXT CHECK(category IN ('task', 'accomplishment', 'meeting', 'learning', 'other')) DEFAULT 'task',
            mood TEXT CHECK(mood IN ('great', 'good', 'neutral', 'challenging', 'difficult')) DEFAULT 'neutral',
            is_highlight BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES jobs (id) ON DELETE CASCADE
        )
    ''')
    
    # Tags for journal entries (flexible categorization)
    c.execute('''
        CREATE TABLE IF NOT EXISTS journal_tags (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            color TEXT DEFAULT '#58a6ff'
        )
    ''')
    
    # Many-to-many relationship between entries and tags
    c.execute('''
        CREATE TABLE IF NOT EXISTS journal_entry_tags (
            entry_id INTEGER NOT NULL,
            tag_id INTEGER NOT NULL,
            PRIMARY KEY (entry_id, tag_id),
            FOREIGN KEY (entry_id) REFERENCES journal_entries (id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES journal_tags (id) ON DELETE CASCADE
        )
    ''')
    
    # Future: Manager/peer sign-offs on entries
    c.execute('''
        CREATE TABLE IF NOT EXISTS journal_signoffs (
            id INTEGER PRIMARY KEY,
            entry_id INTEGER NOT NULL,
            signoff_name TEXT NOT NULL,
            signoff_email TEXT,
            signoff_role TEXT,
            signed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT,
            FOREIGN KEY (entry_id) REFERENCES journal_entries (id) ON DELETE CASCADE
        )
    ''')
    
    # Check if resume_path column exists, if not add it
    c.execute("PRAGMA table_info(job_applications)")
    columns = [column[1] for column in c.fetchall()]
    if 'resume_path' not in columns:
        c.execute('ALTER TABLE job_applications ADD COLUMN resume_path TEXT')
    
    # Sample data
    c.execute('''INSERT OR IGNORE INTO jobs 
                (id, title, company, location, start_date, end_date, current)
                VALUES 
                (1, 'Vice President', 'Pathway Ventures', 'Fargo, ND', 
                '2023-09', NULL, 1)''')
                
    c.execute('''INSERT OR IGNORE INTO job_points 
                (job_id, point, order_num) 
                VALUES 
                (1, 'Reduced time to render user buddy lists by 75% by implementing a prediction algorithm', 1)''')
    
    # Initialize display_order for existing records if needed
    c.execute('''
        UPDATE jobs 
        SET display_order = (
            SELECT COUNT(*) 
            FROM jobs j2 
            WHERE j2.id <= jobs.id
        )
        WHERE display_order IS NULL
    ''')
    
    conn.commit()
    conn.close()

def get_all_jobs():
    conn = sqlite3.connect('resume.db')
    c = conn.cursor()
    
    c.execute('''
        SELECT j.id, j.title, j.company, j.location, j.start_date, 
               j.end_date, j.current, j.display_order,
               GROUP_CONCAT(jp.id || ':' || jp.point, '||' ORDER BY jp.order_num) as points
        FROM jobs j
        LEFT JOIN job_points jp ON j.id = jp.job_id
        GROUP BY j.id
        ORDER BY j.display_order
    ''')
    
    jobs = []
    for row in c.fetchall():
        points_data = []
        if row[8]:  # If there are points
            for point_str in row[8].split('||'):
                if ':' in point_str:
                    point_id, point_text = point_str.split(':', 1)
                    points_data.append({'id': point_id, 'text': point_text})
        
        job = {
            'id': row[0],
            'title': row[1],
            'company': row[2],
            'location': row[3],
            'dates': format_dates(row[4], row[5], row[6]),
            'points': [p['text'] for p in points_data],
            'point_ids': [p['id'] for p in points_data],
            'display_order': row[7],
            'resume_points': [p['text'] for p in points_data[:3]] if points_data else []
        }
        jobs.append(job)
    
    conn.close()
    return jobs

def format_dates(start_date, end_date, current):
    start = datetime.strptime(start_date, '%Y-%m').strftime('%b %Y')
    if current:
        return f'{start} – Present'
    elif end_date:
        end = datetime.strptime(end_date, '%Y-%m').strftime('%b %Y')
        return f'{start} – {end}'
    return start

def add_job_points(job_id, point, order_num):
    conn = sqlite3.connect('resume.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO job_points (job_id, point, order_num)
        VALUES (?, ?, ?)
    ''', (job_id, point, order_num))
    conn.commit()
    conn.close()

def add_job(title, company, location, start_date, end_date=None, current=False):
    conn = sqlite3.connect('resume.db')
    c = conn.cursor()
    
    # Get the next display order
    c.execute('SELECT COALESCE(MAX(display_order), 0) + 1 FROM jobs')
    next_order = c.fetchone()[0]
    
    c.execute('''
        INSERT INTO jobs (title, company, location, start_date, end_date, current, display_order)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (title, company, location, start_date, end_date, current, next_order))
    job_id = c.lastrowid
    conn.commit()
    conn.close()
    return job_id

def get_next_order_num(job_id):
    conn = sqlite3.connect('resume.db')
    c = conn.cursor()
    c.execute('SELECT MAX(order_num) FROM job_points WHERE job_id = ?', (job_id,))
    max_order = c.fetchone()[0]
    conn.close()
    return (max_order or 0) + 1

def delete_job_point(point_id):
    conn = sqlite3.connect('resume.db')
    c = conn.cursor()
    c.execute('DELETE FROM job_points WHERE id = ?', (point_id,))
    conn.commit()
    conn.close()

def delete_job_and_points(job_id):
    conn = sqlite3.connect('resume.db')
    c = conn.cursor()
    # Delete points first (due to foreign key constraint)
    c.execute('DELETE FROM job_points WHERE job_id = ?', (job_id,))
    # Then delete the job
    c.execute('DELETE FROM jobs WHERE id = ?', (job_id,))
    conn.commit()
    conn.close()

def update_job_order(job_orders):
    conn = sqlite3.connect('resume.db')
    c = conn.cursor()
    
    # If job_orders is a dictionary, convert it to the expected format
    if isinstance(job_orders, dict):
        job_orders = [{'id': job_id, 'order': order} for job_id, order in job_orders.items()]
    
    for job in job_orders:
        c.execute('''
            UPDATE jobs 
            SET display_order = ? 
            WHERE id = ?
        ''', (job['order'], job['id']))
    
    conn.commit()
    conn.close()

def update_job_point_order(job_id, point_orders):
    conn = sqlite3.connect('resume.db')
    c = conn.cursor()
    
    for point in point_orders:
        c.execute('''
            UPDATE job_points 
            SET order_num = ? 
            WHERE id = ? AND job_id = ?
        ''', (point['order'], point['id'], job_id))
    
    conn.commit()
    conn.close()

def store_ai_ordering(job_orders, point_orders, model_type):
    conn = sqlite3.connect('resume.db')
    c = conn.cursor()
    
    # Clear old orderings for this model type
    c.execute('DELETE FROM ai_job_orders WHERE model_type = ?', (model_type,))
    c.execute('DELETE FROM ai_point_orders WHERE model_type = ?', (model_type,))
    
    # Store job orders
    for job_id, order in job_orders.items():
        c.execute('''
            INSERT INTO ai_job_orders (job_id, ai_display_order, model_type)
            VALUES (?, ?, ?)
        ''', (job_id, order, model_type))
    
    # Store point orders
    for job_id, points in point_orders.items():
        for point_id, order_data in points.items():
            c.execute('''
                INSERT INTO ai_point_orders 
                (job_id, point_id, ai_order_num, relevance_score, model_type)
                VALUES (?, ?, ?, ?, ?)
            ''', (job_id, point_id, order_data['order'], 
                  order_data['score'], model_type))
    
    conn.commit()
    conn.close()

def get_ai_ordered_jobs(model_type):
    conn = sqlite3.connect('resume.db')
    c = conn.cursor()
    
    # Get jobs with AI ordering
    c.execute('''
        SELECT j.id, j.title, j.company, j.location, j.start_date, 
               j.end_date, j.current, COALESCE(ao.ai_display_order, j.display_order) as display_order,
               GROUP_CONCAT(
                   jp.id || ':' || jp.point, 
                   '||' 
                   ORDER BY COALESCE(apo.ai_order_num, jp.order_num), jp.id
               ) as points
        FROM jobs j
        LEFT JOIN job_points jp ON j.id = jp.job_id
        LEFT JOIN ai_job_orders ao ON j.id = ao.job_id AND ao.model_type = ?
        LEFT JOIN ai_point_orders apo ON jp.id = apo.point_id AND apo.model_type = ?
        GROUP BY j.id
        ORDER BY COALESCE(ao.ai_display_order, j.display_order), j.id
    ''', (model_type, model_type))
    
    jobs = []
    for row in c.fetchall():
        points_data = []
        if row[8]:  # If there are points
            seen_points = set()  # Track unique points
            for point_str in row[8].split('||'):
                if ':' in point_str:
                    point_id, point_text = point_str.split(':', 1)
                    if point_id not in seen_points:  # Only add if not seen
                        points_data.append({'id': point_id, 'text': point_text})
                        seen_points.add(point_id)
        
        job = {
            'id': row[0],
            'title': row[1],
            'company': row[2],
            'location': row[3],
            'dates': format_dates(row[4], row[5], row[6]),
            'points': [p['text'] for p in points_data],
            'point_ids': [p['id'] for p in points_data],
            'display_order': row[7],
            'resume_points': [p['text'] for p in points_data[:3]] if points_data else []
        }
        jobs.append(job)
    
    conn.close()
    return jobs

def update_point_order_db(point_id, new_order):
    conn = sqlite3.connect('resume.db')
    c = conn.cursor()
    c.execute('UPDATE job_points SET order_num = ? WHERE id = ?', (new_order, point_id))
    conn.commit()
    conn.close()

# ============================================
# Settings Functions
# ============================================

def get_settings():
    """Get user settings"""
    conn = sqlite3.connect('resume.db')
    c = conn.cursor()
    
    c.execute('SELECT * FROM user_settings WHERE id = 1')
    row = c.fetchone()
    conn.close()
    
    if row:
        return {
            'full_name': row[1] or '',
            'email': row[2] or '',
            'phone': row[3] or '',
            'location': row[4] or '',
            'linkedin_url': row[5] or '',
            'github_url': row[6] or '',
            'website_url': row[7] or '',
            'my_story': row[8] or '',
            'jobs_on_resume': row[9] or 4,
            'points_per_job': row[10] or 3
        }
    return {
        'full_name': '',
        'email': '',
        'phone': '',
        'location': '',
        'linkedin_url': '',
        'github_url': '',
        'website_url': '',
        'my_story': '',
        'jobs_on_resume': 4,
        'points_per_job': 3
    }

def save_settings(settings):
    """Save user settings"""
    conn = sqlite3.connect('resume.db')
    c = conn.cursor()
    
    c.execute('''
        UPDATE user_settings SET
            full_name = ?,
            email = ?,
            phone = ?,
            location = ?,
            linkedin_url = ?,
            github_url = ?,
            website_url = ?,
            my_story = ?,
            jobs_on_resume = ?,
            points_per_job = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = 1
    ''', (
        settings.get('full_name', ''),
        settings.get('email', ''),
        settings.get('phone', ''),
        settings.get('location', ''),
        settings.get('linkedin_url', ''),
        settings.get('github_url', ''),
        settings.get('website_url', ''),
        settings.get('my_story', ''),
        settings.get('jobs_on_resume', 4),
        settings.get('points_per_job', 3)
    ))
    
    conn.commit()
    conn.close()

# ============================================
# Application Functions
# ============================================

def get_all_applications():
    """Get all applications with their linked jobs"""
    conn = sqlite3.connect('resume.db')
    c = conn.cursor()
    
    c.execute('''
        SELECT ja.id, ja.company, ja.title, ja.application_date, ja.status,
               ja.job_description, ja.story, ja.resume_path, ja.created_at,
               GROUP_CONCAT(aj.job_id) as job_ids
        FROM job_applications ja
        LEFT JOIN application_jobs aj ON ja.id = aj.application_id
        GROUP BY ja.id
        ORDER BY ja.application_date DESC
    ''')
    
    applications = []
    for row in c.fetchall():
        job_ids = []
        if row[9]:
            job_ids = [int(jid) for jid in row[9].split(',')]
        
        applications.append({
            'id': row[0],
            'company': row[1],
            'title': row[2],
            'date': row[3],
            'status': row[4],
            'job_description': row[5] or '',
            'story': row[6] or '',
            'resume_path': row[7],
            'created_at': row[8],
            'job_ids': job_ids,
            'job_count': len(job_ids)
        })
    
    conn.close()
    return applications

def get_application(app_id):
    """Get a single application with full details"""
    conn = sqlite3.connect('resume.db')
    c = conn.cursor()
    
    # Get application details
    c.execute('''
        SELECT id, company, title, application_date, status,
               job_description, story, resume_path, created_at
        FROM job_applications
        WHERE id = ?
    ''', (app_id,))
    
    row = c.fetchone()
    if not row:
        conn.close()
        return None
    
    application = {
        'id': row[0],
        'company': row[1],
        'title': row[2],
        'date': row[3],
        'status': row[4],
        'job_description': row[5] or '',
        'story': row[6] or '',
        'resume_path': row[7],
        'created_at': row[8],
        'jobs': []
    }
    
    # Get linked jobs with their points
    c.execute('''
        SELECT j.id, j.title, j.company, j.location, j.start_date, j.end_date, j.current,
               aj.display_order
        FROM application_jobs aj
        JOIN jobs j ON aj.job_id = j.id
        WHERE aj.application_id = ?
        ORDER BY aj.display_order
    ''', (app_id,))
    
    for job_row in c.fetchall():
        job = {
            'id': job_row[0],
            'title': job_row[1],
            'company': job_row[2],
            'location': job_row[3],
            'dates': format_dates(job_row[4], job_row[5], job_row[6]),
            'display_order': job_row[7],
            'points': []
        }
        
        # Get points for this job in this application
        c.execute('''
            SELECT jp.id, jp.point, ap.display_order
            FROM application_points ap
            JOIN job_points jp ON ap.point_id = jp.id
            WHERE ap.application_id = ? AND jp.job_id = ?
            ORDER BY ap.display_order
        ''', (app_id, job_row[0]))
        
        for point_row in c.fetchall():
            job['points'].append({
                'id': point_row[0],
                'text': point_row[1],
                'order': point_row[2]
            })
        
        application['jobs'].append(job)
    
    conn.close()
    return application

def create_application(company, title, application_date, job_description='', story='', 
                       job_ids=None, point_selections=None, resume_path=None):
    """Create a new application with linked jobs and points"""
    conn = sqlite3.connect('resume.db')
    c = conn.cursor()
    
    # Insert application
    c.execute('''
        INSERT INTO job_applications 
        (company, title, application_date, job_description, story, resume_path, status)
        VALUES (?, ?, ?, ?, ?, ?, 'applied')
    ''', (company, title, application_date, job_description, story, resume_path))
    
    app_id = c.lastrowid
    
    # Link jobs if provided
    if job_ids:
        for order, job_id in enumerate(job_ids, 1):
            c.execute('''
                INSERT INTO application_jobs (application_id, job_id, display_order)
                VALUES (?, ?, ?)
            ''', (app_id, job_id, order))
    
    # Link points if provided
    if point_selections:
        for point_id, order in point_selections.items():
            c.execute('''
                INSERT INTO application_points (application_id, point_id, display_order)
                VALUES (?, ?, ?)
            ''', (app_id, int(point_id), order))
    
    conn.commit()
    conn.close()
    return app_id

def update_application(app_id, **kwargs):
    """Update application details"""
    conn = sqlite3.connect('resume.db')
    c = conn.cursor()
    
    # Build update query dynamically
    updates = []
    values = []
    
    allowed_fields = ['company', 'title', 'application_date', 'status', 
                      'job_description', 'story', 'resume_path']
    
    for field in allowed_fields:
        if field in kwargs:
            updates.append(f'{field} = ?')
            values.append(kwargs[field])
    
    if updates:
        values.append(app_id)
        c.execute(f'''
            UPDATE job_applications 
            SET {', '.join(updates)}
            WHERE id = ?
        ''', values)
    
    # Update job links if provided
    if 'job_ids' in kwargs:
        # Clear existing links
        c.execute('DELETE FROM application_jobs WHERE application_id = ?', (app_id,))
        c.execute('DELETE FROM application_points WHERE application_id = ?', (app_id,))
        
        # Add new links
        for order, job_id in enumerate(kwargs['job_ids'], 1):
            c.execute('''
                INSERT INTO application_jobs (application_id, job_id, display_order)
                VALUES (?, ?, ?)
            ''', (app_id, job_id, order))
    
    # Update point selections if provided
    if 'point_selections' in kwargs:
        c.execute('DELETE FROM application_points WHERE application_id = ?', (app_id,))
        for point_id, order in kwargs['point_selections'].items():
            c.execute('''
                INSERT INTO application_points (application_id, point_id, display_order)
                VALUES (?, ?, ?)
            ''', (app_id, int(point_id), order))
    
    conn.commit()
    conn.close()

def delete_application(app_id):
    """Delete an application and its links"""
    conn = sqlite3.connect('resume.db')
    c = conn.cursor()
    
    # Get resume path before deleting
    c.execute('SELECT resume_path FROM job_applications WHERE id = ?', (app_id,))
    result = c.fetchone()
    resume_path = result[0] if result else None
    
    # Delete links first
    c.execute('DELETE FROM application_jobs WHERE application_id = ?', (app_id,))
    c.execute('DELETE FROM application_points WHERE application_id = ?', (app_id,))
    
    # Delete application
    c.execute('DELETE FROM job_applications WHERE id = ?', (app_id,))
    
    conn.commit()
    conn.close()
    
    return resume_path

def get_jobs_for_application(app_id):
    """Get jobs linked to an application with their selected points"""
    conn = sqlite3.connect('resume.db')
    c = conn.cursor()
    
    c.execute('''
        SELECT j.id, j.title, j.company, j.location, j.start_date, j.end_date, j.current,
               aj.display_order
        FROM application_jobs aj
        JOIN jobs j ON aj.job_id = j.id
        WHERE aj.application_id = ?
        ORDER BY aj.display_order
    ''', (app_id,))
    
    jobs = []
    for row in c.fetchall():
        job = {
            'id': row[0],
            'title': row[1],
            'company': row[2],
            'location': row[3],
            'dates': format_dates(row[4], row[5], row[6]),
            'display_order': row[7],
            'points': []
        }
        
        # Get selected points for this job
        c.execute('''
            SELECT jp.point, ap.display_order
            FROM application_points ap
            JOIN job_points jp ON ap.point_id = jp.id
            WHERE ap.application_id = ? AND jp.job_id = ?
            ORDER BY ap.display_order
        ''', (app_id, row[0]))
        
        job['points'] = [p[0] for p in c.fetchall()]
        jobs.append(job)
    
    conn.close()
    return jobs

# ============================================
# Journal Functions
# ============================================

def create_journal_entry(job_id, entry_date, content, title=None, hours_worked=None, 
                         category='task', mood='neutral', is_highlight=False, tags=None):
    """Create a new journal entry"""
    conn = sqlite3.connect('resume.db')
    c = conn.cursor()
    
    c.execute('''
        INSERT INTO journal_entries 
        (job_id, entry_date, title, content, hours_worked, category, mood, is_highlight)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (job_id, entry_date, title, content, hours_worked, category, mood, is_highlight))
    
    entry_id = c.lastrowid
    
    # Add tags if provided
    if tags:
        for tag_name in tags:
            # Get or create tag
            c.execute('SELECT id FROM journal_tags WHERE name = ?', (tag_name,))
            tag_row = c.fetchone()
            if tag_row:
                tag_id = tag_row[0]
            else:
                c.execute('INSERT INTO journal_tags (name) VALUES (?)', (tag_name,))
                tag_id = c.lastrowid
            
            # Link tag to entry
            c.execute('INSERT OR IGNORE INTO journal_entry_tags (entry_id, tag_id) VALUES (?, ?)',
                     (entry_id, tag_id))
    
    conn.commit()
    conn.close()
    return entry_id

def get_journal_entries(job_id=None, start_date=None, end_date=None, limit=50, offset=0):
    """Get journal entries with optional filters"""
    conn = sqlite3.connect('resume.db')
    c = conn.cursor()
    
    query = '''
        SELECT je.id, je.job_id, je.entry_date, je.title, je.content, 
               je.hours_worked, je.category, je.mood, je.is_highlight,
               je.created_at, j.title as job_title, j.company,
               GROUP_CONCAT(jt.name) as tags
        FROM journal_entries je
        JOIN jobs j ON je.job_id = j.id
        LEFT JOIN journal_entry_tags jet ON je.id = jet.entry_id
        LEFT JOIN journal_tags jt ON jet.tag_id = jt.id
    '''
    
    conditions = []
    params = []
    
    if job_id:
        conditions.append('je.job_id = ?')
        params.append(job_id)
    
    if start_date:
        conditions.append('je.entry_date >= ?')
        params.append(start_date)
    
    if end_date:
        conditions.append('je.entry_date <= ?')
        params.append(end_date)
    
    if conditions:
        query += ' WHERE ' + ' AND '.join(conditions)
    
    query += ' GROUP BY je.id ORDER BY je.entry_date DESC, je.created_at DESC'
    query += f' LIMIT {limit} OFFSET {offset}'
    
    c.execute(query, params)
    
    entries = []
    for row in c.fetchall():
        entries.append({
            'id': row[0],
            'job_id': row[1],
            'entry_date': row[2],
            'title': row[3],
            'content': row[4],
            'hours_worked': row[5],
            'category': row[6],
            'mood': row[7],
            'is_highlight': bool(row[8]),
            'created_at': row[9],
            'job_title': row[10],
            'company': row[11],
            'tags': row[12].split(',') if row[12] else []
        })
    
    conn.close()
    return entries

def get_journal_entry(entry_id):
    """Get a single journal entry"""
    conn = sqlite3.connect('resume.db')
    c = conn.cursor()
    
    c.execute('''
        SELECT je.id, je.job_id, je.entry_date, je.title, je.content, 
               je.hours_worked, je.category, je.mood, je.is_highlight,
               je.created_at, j.title as job_title, j.company,
               GROUP_CONCAT(jt.name) as tags
        FROM journal_entries je
        JOIN jobs j ON je.job_id = j.id
        LEFT JOIN journal_entry_tags jet ON je.id = jet.entry_id
        LEFT JOIN journal_tags jt ON jet.tag_id = jt.id
        WHERE je.id = ?
        GROUP BY je.id
    ''', (entry_id,))
    
    row = c.fetchone()
    conn.close()
    
    if not row:
        return None
    
    return {
        'id': row[0],
        'job_id': row[1],
        'entry_date': row[2],
        'title': row[3],
        'content': row[4],
        'hours_worked': row[5],
        'category': row[6],
        'mood': row[7],
        'is_highlight': bool(row[8]),
        'created_at': row[9],
        'job_title': row[10],
        'company': row[11],
        'tags': row[12].split(',') if row[12] else []
    }

def update_journal_entry(entry_id, **kwargs):
    """Update a journal entry"""
    conn = sqlite3.connect('resume.db')
    c = conn.cursor()
    
    allowed_fields = ['job_id', 'entry_date', 'title', 'content', 'hours_worked', 
                      'category', 'mood', 'is_highlight']
    
    updates = []
    values = []
    
    for field in allowed_fields:
        if field in kwargs:
            updates.append(f'{field} = ?')
            values.append(kwargs[field])
    
    if updates:
        updates.append('updated_at = CURRENT_TIMESTAMP')
        values.append(entry_id)
        c.execute(f'''
            UPDATE journal_entries 
            SET {', '.join(updates)}
            WHERE id = ?
        ''', values)
    
    # Update tags if provided
    if 'tags' in kwargs:
        # Clear existing tags
        c.execute('DELETE FROM journal_entry_tags WHERE entry_id = ?', (entry_id,))
        
        # Add new tags
        for tag_name in kwargs['tags']:
            c.execute('SELECT id FROM journal_tags WHERE name = ?', (tag_name,))
            tag_row = c.fetchone()
            if tag_row:
                tag_id = tag_row[0]
            else:
                c.execute('INSERT INTO journal_tags (name) VALUES (?)', (tag_name,))
                tag_id = c.lastrowid
            
            c.execute('INSERT OR IGNORE INTO journal_entry_tags (entry_id, tag_id) VALUES (?, ?)',
                     (entry_id, tag_id))
    
    conn.commit()
    conn.close()

def delete_journal_entry(entry_id):
    """Delete a journal entry"""
    conn = sqlite3.connect('resume.db')
    c = conn.cursor()
    
    c.execute('DELETE FROM journal_entry_tags WHERE entry_id = ?', (entry_id,))
    c.execute('DELETE FROM journal_entries WHERE id = ?', (entry_id,))
    
    conn.commit()
    conn.close()

def get_journal_stats(job_id=None):
    """Get journal statistics"""
    conn = sqlite3.connect('resume.db')
    c = conn.cursor()
    
    base_query = 'FROM journal_entries je'
    where_clause = f' WHERE je.job_id = {job_id}' if job_id else ''
    
    # Total entries
    c.execute(f'SELECT COUNT(*) {base_query}{where_clause}')
    total_entries = c.fetchone()[0]
    
    # Total hours
    c.execute(f'SELECT COALESCE(SUM(hours_worked), 0) {base_query}{where_clause}')
    total_hours = c.fetchone()[0]
    
    # Highlights count
    c.execute(f'SELECT COUNT(*) {base_query}{where_clause} AND is_highlight = 1' if where_clause else f'SELECT COUNT(*) {base_query} WHERE is_highlight = 1')
    highlights = c.fetchone()[0]
    
    # Entries by category
    c.execute(f'''
        SELECT category, COUNT(*) 
        {base_query}{where_clause}
        GROUP BY category
    ''')
    by_category = {row[0]: row[1] for row in c.fetchall()}
    
    # Recent streak (consecutive days with entries)
    c.execute(f'''
        SELECT DISTINCT entry_date 
        {base_query}{where_clause}
        ORDER BY entry_date DESC
        LIMIT 30
    ''')
    dates = [row[0] for row in c.fetchall()]
    streak = 0
    if dates:
        from datetime import datetime, timedelta
        today = datetime.now().date()
        for i, date_str in enumerate(dates):
            entry_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            expected_date = today - timedelta(days=i)
            if entry_date == expected_date:
                streak += 1
            else:
                break
    
    conn.close()
    
    return {
        'total_entries': total_entries,
        'total_hours': round(total_hours, 1),
        'highlights': highlights,
        'by_category': by_category,
        'streak': streak
    }

def get_entries_by_date_range(start_date, end_date, job_id=None):
    """Get entries grouped by date for calendar view"""
    conn = sqlite3.connect('resume.db')
    c = conn.cursor()
    
    query = '''
        SELECT entry_date, COUNT(*) as count, 
               SUM(CASE WHEN is_highlight = 1 THEN 1 ELSE 0 END) as highlights
        FROM journal_entries
    '''
    
    conditions = ['entry_date >= ?', 'entry_date <= ?']
    params = [start_date, end_date]
    
    if job_id:
        conditions.append('job_id = ?')
        params.append(job_id)
    
    query += ' WHERE ' + ' AND '.join(conditions)
    query += ' GROUP BY entry_date'
    
    c.execute(query, params)
    
    result = {}
    for row in c.fetchall():
        result[row[0]] = {'count': row[1], 'highlights': row[2]}
    
    conn.close()
    return result

def get_all_tags():
    """Get all journal tags"""
    conn = sqlite3.connect('resume.db')
    c = conn.cursor()
    
    c.execute('''
        SELECT jt.id, jt.name, jt.color, COUNT(jet.entry_id) as usage_count
        FROM journal_tags jt
        LEFT JOIN journal_entry_tags jet ON jt.id = jet.tag_id
        GROUP BY jt.id
        ORDER BY usage_count DESC
    ''')
    
    tags = [{'id': row[0], 'name': row[1], 'color': row[2], 'count': row[3]} 
            for row in c.fetchall()]
    
    conn.close()
    return tags

# Add this function to help with initialization
def initialize_database():
    """Initialize all database tables"""
    init_db()
    print("Database initialized successfully!")

if __name__ == "__main__":
    initialize_database()