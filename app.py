from flask import Flask, render_template, send_file, request, redirect, url_for
import os
import subprocess
from jinja2 import Environment, FileSystemLoader
from database import get_all_jobs, add_job, add_job_points

app = Flask(__name__)

def generate_pdf():
    # Get jobs from database
    jobs = get_all_jobs()
    
    # Convert to template format
    experience_data = {
        f'job{i+1}': job for i, job in enumerate(jobs)
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
def add_job():
    # Get form data
    title = request.form['title']
    company = request.form['company']
    location = request.form['location']
    start_date = request.form['start_date']
    end_date = request.form['end_date'] if request.form['end_date'] else None
    current = 'current' in request.form
    points = request.form['points'].split('\n')
    
    # Add job to database
    job_id = add_job(title, company, location, start_date, end_date, current)
    
    # Add job points
    for i, point in enumerate(points):
        if point.strip():  # Skip empty lines
            add_job_points(job_id, point.strip(), i+1)
    
    return redirect(url_for('index'))

@app.route('/download-resume')
def download_resume():
    pdf_path = generate_pdf()
    return send_file(pdf_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
