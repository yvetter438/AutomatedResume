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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
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

# Add this function to help with initialization
def initialize_database():
    """Initialize all database tables"""
    init_db()
    print("Database initialized successfully!")

if __name__ == "__main__":
    initialize_database()