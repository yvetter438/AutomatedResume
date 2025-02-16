from flask import Flask, render_template, send_file
import os
import subprocess

app = Flask(__name__)


def generate_pdf():
    #define paths
    template_path = os.path.join('templates', 'resume.tex')
    out_dir = 'static'

    #run pdflatex
    subprocess.run([
        'pdflatex',
        '-output-directory', out_dir,
        template_path
    ])

    return os.path.join(out_dir, 'resume.pdf')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download-resume')
def download_resume():
    # TODO: Implement PDF generation
    pdf_path = generate_pdf()
    # For now, we'll just return a static PDF if you have one
    return send_file(pdf_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
