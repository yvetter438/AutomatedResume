from flask import Flask, render_template, send_file
import json

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download-resume')
def download_resume():
    # TODO: Implement PDF generation
    # For now, we'll just return a static PDF if you have one
    return send_file('static/resume.pdf', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
