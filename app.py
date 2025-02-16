from flask import Flask, render_template, send_file
import os
import subprocess
from jinja2 import Environment, FileSystemLoader

app = Flask(__name__)

# Sample experience data (using your existing content)
experience_data = {
    'job1': {
        'dates': 'Sept 2023 – Present',
        'title': 'Vice President',
        'company': 'Pathway Ventures',
        'location': 'Fargo, ND',
        'points': [
            'Reduced time to render user buddy lists by 75\\% by implementing a prediction algorithm',
            'Integrated iChat with Spotlight Search by creating a tool to extract metadata from saved chat transcripts and provide metadata to a system-wide search database',
            'Redesigned chat file format and implemented backward compatibility for search'
        ]
    },
    'job2': {
        'dates': 'December 2022 – Aug 2024',
        'title': 'Software Engineer Intern',
        'company': 'WorkOdyssey',
        'location': 'Fargo, ND',
        'points': [
            'Designed a UI for the VS open file switcher (Ctrl-Tab) and extended it to tool windows',
            'Created a service to provide gradient across VS and VS add-ins, optimizing its performance via caching',
            'Built an app to compute the similarity of all methods in a codebase, reducing the time from $\\mathcal{O}(n^2)$ to $\\mathcal{O}(n \\log n)$'
        ]
    },
    'job3': {
        'dates': 'June 2003 – Aug 2003',
        'title': 'Web Developer Intern',
        'company': 'NSF I-Corps',
        'location': 'Fargo, ND',
        'points': [
            'Designed a UI for the VS open file switcher (Ctrl-Tab) and extended it to tool windows',
            'Created a service to provide gradient across VS and VS add-ins, optimizing its performance via caching'
        ]
    },
    'job4': {
        'dates': 'June 2003 – Aug 2003',
        'title': 'President',
        'company': 'NDSU Entrepreneurship Club',
        'location': 'Fargo, ND',
        'points': [
            'Designed a UI for the VS open file switcher (Ctrl-Tab) and extended it to tool windows',
            'Created a service to provide gradient across VS and VS add-ins, optimizing its performance via caching'
        ]
    }
}

def generate_pdf():
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
    return render_template('index.html')

@app.route('/download-resume')
def download_resume():
    pdf_path = generate_pdf()
    return send_file(pdf_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
