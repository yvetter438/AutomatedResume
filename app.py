from flask import Flask, render_template, send_file, request, redirect, url_for, jsonify
import os
import subprocess
from jinja2 import Environment, FileSystemLoader
from database import (
    get_all_jobs, add_job, add_job_points, get_next_order_num,
    delete_job_point, delete_job_and_points, update_job_order,
    update_job_point_order, get_ai_ordered_jobs, store_ai_ordering,
    update_point_order_db, get_settings, save_settings,
    get_all_applications, get_application, create_application as db_create_application,
    update_application, delete_application as db_delete_application,
    get_jobs_for_application,
    # Journal functions
    create_journal_entry, get_journal_entries, get_journal_entry,
    update_journal_entry, delete_journal_entry, get_journal_stats,
    get_entries_by_date_range, get_all_tags
)
from ai_service import test_ai_connection, AIModel, AIService
import sqlite3
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)

UPLOAD_FOLDER = 'static/resumes'
ALLOWED_EXTENSIONS = {'pdf'}

def generate_pdf(mode='handcrafted', model_type='openai'):
    # Get jobs based on mode
    if mode == 'handcrafted':
        all_jobs = get_all_jobs()
    else:
        all_jobs = get_ai_ordered_jobs(model_type)
    
    # Take only first 4 jobs and their first 3 points
    resume_jobs = all_jobs[:4]
    
    # Convert to template format
    experience_data = {
        f'job{i+1}': {
            'dates': job['dates'],
            'title': job['title'],
            'company': job['company'],
            'location': job['location'],
            'points': job['resume_points']
        } for i, job in enumerate(resume_jobs)
    }
    
    # Define paths
    temp_tex_path = os.path.join('static', 'temp_resume.tex')
    output_dir = 'static'
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Load and render the LaTeX template
    env = Environment(
        loader=FileSystemLoader('templates'),
        block_start_string=r'\BLOCK{',
        block_end_string='}',
        variable_start_string=r'\VAR{',
        variable_end_string='}',
        comment_start_string=r'\#{',
        comment_end_string='}',
        line_statement_prefix='%%',
        line_comment_prefix='%#',
        trim_blocks=True,
        autoescape=False,
    )
    template = env.get_template('resume_template.tex')
    rendered_tex = template.render(**experience_data)
    
    # Write the rendered template to a temporary file
    with open(temp_tex_path, 'w') as f:
        f.write(rendered_tex)
    
    # Run pdflatex with error checking using full MacTeX path
    result = subprocess.run([
        '/Library/TeX/texbin/pdflatex',  # Use explicit MacTeX path
        '-output-directory', output_dir,
        temp_tex_path
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print("LaTeX Error:", result.stderr)
        raise Exception("PDF generation failed")
        
    pdf_path = os.path.join(output_dir, 'temp_resume.pdf')
    if not os.path.exists(pdf_path):
        raise Exception(f"PDF not generated at {pdf_path}")
        
    return pdf_path

@app.route('/')
def index():
    jobs = get_all_jobs()
    return render_template('index.html', jobs=jobs)

@app.route('/add-job', methods=['POST'])
def create_job():
    # Get form data
    title = request.form['title']
    company = request.form['company']
    location = request.form['location']
    start_date = request.form['start_date']
    current = 'current' in request.form
    end_date = None if current else request.form.get('end_date')
    
    # Get points array directly
    points = request.form.getlist('points[]')
    
    # Add job to database
    job_id = add_job(title, company, location, start_date, end_date, current)
    
    # Add job points
    for i, point in enumerate(points):
        if point.strip():  # Skip empty points
            add_job_points(job_id, point.strip(), i+1)
    
    return redirect(url_for('index'))

@app.route('/download-resume')
def download_resume():
    # Check if we're in AI mode
    mode = request.args.get('mode', 'handcrafted')
    model_type = request.args.get('model_type', 'openai')
    
    pdf_path = generate_pdf(mode, model_type)
    return send_file(pdf_path, as_attachment=True)

@app.route('/add-point/<int:job_id>', methods=['POST'])
def add_point(job_id):
    point = request.form['point']
    # Get the next order number for this job
    order_num = get_next_order_num(job_id)
    add_job_points(job_id, point, order_num)
    return redirect(url_for('index'))

@app.route('/delete-point/<int:point_id>', methods=['POST'])
def delete_point(point_id):
    delete_job_point(point_id)
    return redirect(url_for('index'))

@app.route('/delete-job/<int:job_id>', methods=['POST'])
def delete_job(job_id):
    delete_job_and_points(job_id)
    return redirect(url_for('index'))

@app.route('/update-order', methods=['POST'])
def update_order():
    job_orders = request.json['jobs']
    update_job_order(job_orders)
    return jsonify({'status': 'success'})

@app.route('/update-point-order/<int:job_id>', methods=['POST'])
def update_point_order(job_id):
    point_orders = request.json['points']
    update_job_point_order(job_id, point_orders)
    return jsonify({'status': 'success'})

@app.route('/test-ai/<model_type>')
def test_ai(model_type):
    model = AIModel.DEEPSEEK if model_type == 'deepseek' else AIModel.OPENAI
    success, message = test_ai_connection(model)
    return jsonify({
        'success': success,
        'message': message,
        'model': model_type
    })

@app.route('/optimize-resume', methods=['POST'])
def optimize_resume():
    try:
        data = request.get_json()
        model_type = data.get('model_type', 'openai')
        job_description = data.get('job_description', '')
        story = data.get('story', '')
        
        # Get all jobs from database
        jobs = get_all_jobs()
        
        # Initialize AI service with the selected model
        ai_service = AIService(AIModel.DEEPSEEK if model_type == 'deepseek' else AIModel.OPENAI)
        
        # Call optimize_resume method
        success, result = ai_service.optimize_resume(jobs, job_description, story)
        
        if success:
            # Update job orders in database
            update_job_order(result['job_order'])
            
            # Update point orders
            for job_id, points in result['point_orders'].items():
                for point_id, order_data in points.items():
                    update_point_order_db(point_id, order_data['order'])
            
            # Store the AI ordering
            store_ai_ordering(result['job_order'], result['point_orders'], model_type)
            
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': result})
            
    except Exception as e:
        print(f"Error in optimize_resume: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get-resume-view')
def get_resume_view():
    mode = request.args.get('mode', 'handcrafted')
    model_type = request.args.get('model_type', 'openai')
    
    try:
        if mode == 'handcrafted':
            jobs = get_all_jobs()
        else:
            jobs = get_ai_ordered_jobs(model_type)
        
        return render_template('_jobs_list.html', jobs=jobs)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/resumes')
def resumes():
    applications = get_all_applications()
    jobs = get_all_jobs()  # For the job selection in new application form
    return render_template('resumes.html', applications=applications, jobs=jobs)

@app.route('/application/<int:app_id>')
def view_application(app_id):
    application = get_application(app_id)
    if not application:
        return jsonify({'error': 'Application not found'}), 404
    return jsonify(application)

@app.route('/update-status/<int:app_id>', methods=['POST'])
def update_status(app_id):
    status = request.json.get('status')
    update_application(app_id, status=status)
    return jsonify({'success': True})

@app.route('/api/jobs')
def api_jobs():
    """API endpoint to get all jobs with their points"""
    jobs = get_all_jobs()
    return jsonify(jobs)

@app.route('/generate-application-resume/<int:app_id>')
def generate_application_resume(app_id):
    """Generate a resume PDF for a specific application using its linked jobs"""
    try:
        jobs = get_jobs_for_application(app_id)
        settings = get_settings()
        
        if not jobs:
            return "No jobs linked to this application", 400
        
        # Convert to template format
        experience_data = {
            f'job{i+1}': {
                'dates': job['dates'],
                'title': job['title'],
                'company': job['company'],
                'location': job['location'],
                'points': job['points'][:settings['points_per_job']]
            } for i, job in enumerate(jobs[:settings['jobs_on_resume']])
        }
        
        # Define paths
        temp_tex_path = os.path.join('static', 'temp_resume.tex')
        output_dir = 'static'
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Load and render the LaTeX template
        env = Environment(
            loader=FileSystemLoader('templates'),
            block_start_string=r'\BLOCK{',
            block_end_string='}',
            variable_start_string=r'\VAR{',
            variable_end_string='}',
            comment_start_string=r'\#{',
            comment_end_string='}',
            line_statement_prefix='%%',
            line_comment_prefix='%#',
            trim_blocks=True,
            autoescape=False,
        )
        template = env.get_template('resume_template.tex')
        rendered_tex = template.render(**experience_data)
        
        # Write the rendered template
        with open(temp_tex_path, 'w') as f:
            f.write(rendered_tex)
        
        # Run pdflatex
        result = subprocess.run([
            '/Library/TeX/texbin/pdflatex',
            '-output-directory', output_dir,
            temp_tex_path
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print("LaTeX Error:", result.stderr)
            return "PDF generation failed", 500
            
        pdf_path = os.path.join(output_dir, 'temp_resume.pdf')
        if not os.path.exists(pdf_path):
            return "PDF not generated", 500
            
        return send_file(pdf_path, as_attachment=True, download_name='resume.pdf')
    except Exception as e:
        print(f"Error generating resume: {str(e)}")
        return str(e), 500

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/create-application', methods=['POST'])
def create_application_route():
    try:
        # Ensure upload directory exists
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        # Handle file upload
        resume_path = None
        if 'resume' in request.files:
            file = request.files['resume']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)
                resume_path = filepath

        # Get form data
        data = request.form
        
        # Parse job IDs (comma-separated or JSON array)
        job_ids = []
        job_ids_str = data.get('job_ids', '')
        if job_ids_str:
            job_ids = [int(jid.strip()) for jid in job_ids_str.split(',') if jid.strip()]
        
        # Parse point selections (JSON format: {point_id: order})
        point_selections = {}
        points_str = data.get('point_selections', '')
        if points_str:
            import json
            try:
                point_selections = json.loads(points_str)
            except:
                pass
        
        # Create application using database function
        app_id = db_create_application(
            company=data['company'],
            title=data['title'],
            application_date=data['application_date'],
            job_description=data.get('job_description', ''),
            story=data.get('story', ''),
            job_ids=job_ids,
            point_selections=point_selections,
            resume_path=resume_path
        )
        
        return jsonify({'success': True, 'id': app_id})
    except Exception as e:
        print(f"Error creating application: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/download-application-resume/<int:app_id>')
def download_application_resume(app_id):
    conn = sqlite3.connect('resume.db')
    c = conn.cursor()
    
    c.execute('SELECT resume_path FROM job_applications WHERE id = ?', (app_id,))
    result = c.fetchone()
    conn.close()
    
    if not result or not result[0]:
        return "No resume found", 404
        
    return send_file(result[0], as_attachment=True)

@app.route('/delete-application/<int:app_id>', methods=['POST'])
def delete_application_route(app_id):
    try:
        # Delete from database and get resume path
        resume_path = db_delete_application(app_id)
        
        # Delete resume file if it exists
        if resume_path and os.path.exists(resume_path):
            os.remove(resume_path)
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error deleting application: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/generate-pdf')
def generate_pdf_route():
    mode = request.args.get('mode', 'handcrafted')
    model_type = request.args.get('model_type', 'openai')
    pdf_path = generate_pdf(mode, model_type)
    return send_file(pdf_path, as_attachment=True, download_name='resume.pdf')

# ============================================
# Settings Routes
# ============================================

@app.route('/settings')
def settings():
    user_settings = get_settings()
    return render_template('settings.html', settings=user_settings)

@app.route('/settings/save', methods=['POST'])
def save_settings_route():
    try:
        settings_data = {
            'full_name': request.form.get('full_name', ''),
            'email': request.form.get('email', ''),
            'phone': request.form.get('phone', ''),
            'location': request.form.get('location', ''),
            'linkedin_url': request.form.get('linkedin_url', ''),
            'github_url': request.form.get('github_url', ''),
            'website_url': request.form.get('website_url', ''),
            'my_story': request.form.get('my_story', ''),
            'jobs_on_resume': int(request.form.get('jobs_on_resume', 4)),
            'points_per_job': int(request.form.get('points_per_job', 3))
        }
        save_settings(settings_data)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# ============================================
# Journal Routes
# ============================================

@app.route('/journal')
def journal():
    """Main journal page"""
    jobs = get_all_jobs()
    entries = get_journal_entries(limit=20)
    stats = get_journal_stats()
    tags = get_all_tags()
    
    # Get selected job filter if any
    job_id = request.args.get('job_id', type=int)
    if job_id:
        entries = get_journal_entries(job_id=job_id, limit=20)
        stats = get_journal_stats(job_id=job_id)
    
    return render_template('journal.html', 
                         jobs=jobs, 
                         entries=entries, 
                         stats=stats,
                         tags=tags,
                         selected_job_id=job_id)

@app.route('/journal/entry', methods=['POST'])
def create_entry():
    """Create a new journal entry"""
    try:
        data = request.form
        
        # Parse tags from comma-separated string
        tags = []
        tags_str = data.get('tags', '')
        if tags_str:
            tags = [t.strip() for t in tags_str.split(',') if t.strip()]
        
        entry_id = create_journal_entry(
            job_id=int(data['job_id']),
            entry_date=data['entry_date'],
            content=data['content'],
            title=data.get('title'),
            hours_worked=float(data['hours_worked']) if data.get('hours_worked') else None,
            category=data.get('category', 'task'),
            mood=data.get('mood', 'neutral'),
            is_highlight=data.get('is_highlight') == 'true',
            tags=tags
        )
        
        return jsonify({'success': True, 'id': entry_id})
    except Exception as e:
        print(f"Error creating journal entry: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/journal/entry/<int:entry_id>')
def get_entry(entry_id):
    """Get a single journal entry"""
    entry = get_journal_entry(entry_id)
    if not entry:
        return jsonify({'error': 'Entry not found'}), 404
    return jsonify(entry)

@app.route('/journal/entry/<int:entry_id>', methods=['PUT'])
def update_entry(entry_id):
    """Update a journal entry"""
    try:
        data = request.get_json()
        
        # Parse tags if provided
        if 'tags' in data and isinstance(data['tags'], str):
            data['tags'] = [t.strip() for t in data['tags'].split(',') if t.strip()]
        
        update_journal_entry(entry_id, **data)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/journal/entry/<int:entry_id>', methods=['DELETE'])
def delete_entry(entry_id):
    """Delete a journal entry"""
    try:
        delete_journal_entry(entry_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/journal/entries')
def get_entries():
    """Get journal entries with filters (API endpoint)"""
    job_id = request.args.get('job_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    entries = get_journal_entries(
        job_id=job_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset
    )
    
    return jsonify(entries)

@app.route('/journal/stats')
def journal_stats():
    """Get journal statistics"""
    job_id = request.args.get('job_id', type=int)
    stats = get_journal_stats(job_id=job_id)
    return jsonify(stats)

@app.route('/journal/calendar')
def journal_calendar():
    """Get entries for calendar view"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    job_id = request.args.get('job_id', type=int)
    
    if not start_date or not end_date:
        # Default to current month
        today = datetime.now()
        start_date = today.replace(day=1).strftime('%Y-%m-%d')
        if today.month == 12:
            end_date = today.replace(year=today.year+1, month=1, day=1).strftime('%Y-%m-%d')
        else:
            end_date = today.replace(month=today.month+1, day=1).strftime('%Y-%m-%d')
    
    entries = get_entries_by_date_range(start_date, end_date, job_id)
    return jsonify(entries)

if __name__ == '__main__':
    app.run(debug=True)
