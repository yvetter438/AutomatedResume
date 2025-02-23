from flask import Flask, render_template, send_file, request, redirect, url_for, jsonify
import os
import subprocess
from jinja2 import Environment, FileSystemLoader
from database import (
    get_all_jobs, add_job, add_job_points, get_next_order_num,
    delete_job_point, delete_job_and_points, update_job_order,
    update_job_point_order, get_ai_ordered_jobs, store_ai_ordering,
    update_point_order_db
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
    conn = sqlite3.connect('resume.db')
    c = conn.cursor()
    
    c.execute('''
        SELECT id, company, title, application_date, status
        FROM job_applications
        ORDER BY application_date DESC
    ''')
    
    applications = [{
        'id': row[0],
        'company': row[1],
        'title': row[2],
        'date': row[3],
        'status': row[4]
    } for row in c.fetchall()]
    
    conn.close()
    return render_template('resumes.html', applications=applications)

@app.route('/application/<int:app_id>')
def view_application(app_id):
    conn = sqlite3.connect('resume.db')
    c = conn.cursor()
    
    c.execute('''
        SELECT id, company, title, application_date, status, job_description, story, model_type
        FROM job_applications
        WHERE id = ?
    ''', (app_id,))
    
    row = c.fetchone()
    application = {
        'id': row[0],
        'company': row[1],
        'title': row[2],
        'date': row[3],
        'status': row[4],
        'job_description': row[5],
        'story': row[6],
        'model_type': row[7]
    }
    
    conn.close()
    return jsonify(application)

@app.route('/update-status/<int:app_id>', methods=['POST'])
def update_status(app_id):
    status = request.json.get('status')
    conn = sqlite3.connect('resume.db')
    c = conn.cursor()
    
    c.execute('''
        UPDATE job_applications
        SET status = ?
        WHERE id = ?
    ''', (status, app_id))
    
    conn.commit()
    conn.close()
    return jsonify({'success': True})

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/create-application', methods=['POST'])
def create_application():
    try:
        # Ensure upload directory exists
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        # Handle file upload
        resume_path = None
        if 'resume' in request.files:
            file = request.files['resume']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)
                resume_path = filepath

        # Get other form data
        data = request.form
        
        conn = sqlite3.connect('resume.db')
        c = conn.cursor()
        
        c.execute('''
            INSERT INTO job_applications 
            (company, title, application_date, job_description, story, resume_path)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            data['company'],
            data['title'],
            data['application_date'],
            data.get('job_description', ''),
            data.get('story', ''),
            resume_path
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error creating application: {str(e)}")
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
def delete_application(app_id):
    try:
        conn = sqlite3.connect('resume.db')
        c = conn.cursor()
        
        # Get resume path before deleting
        c.execute('SELECT resume_path FROM job_applications WHERE id = ?', (app_id,))
        result = c.fetchone()
        
        # Delete application
        c.execute('DELETE FROM job_applications WHERE id = ?', (app_id,))
        conn.commit()
        conn.close()
        
        # Delete resume file if it exists
        if result and result[0] and os.path.exists(result[0]):
            os.remove(result[0])
        
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

if __name__ == '__main__':
    app.run(debug=True)
