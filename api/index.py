import os
import json
import csv
from PyPDF2 import PdfReader
from flask import Flask, render_template, request, send_file
from io import BytesIO

app = Flask(__name__, static_folder="../static", template_folder="../templates")

root_folder = r"C:\Users\iaimo\OneDrive\Desktop\DATABASES"
last_results = []

def search_in_file(file_path, keyword, results):
    try:
        if file_path.endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for i, line in enumerate(f, 1):
                    if keyword in line.lower():
                        results.append([os.path.basename(file_path), f"Line {i}: {line.strip()}"])
        elif file_path.endswith('.csv'):
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.reader(f)
                for i, row in enumerate(reader, 1):
                    if any(keyword in str(cell).lower() for cell in row):
                        results.append([os.path.basename(file_path), f"Row {i}: {' | '.join(row)}"])
        elif file_path.endswith('.json'):
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                data = json.load(f)
                data_str = json.dumps(data, indent=2)
                for i, line in enumerate(data_str.splitlines(), 1):
                    if keyword in line.lower():
                        results.append([os.path.basename(file_path), f"Line {i}: {line.strip()}"])
        elif file_path.endswith('.pdf'):
            reader = PdfReader(file_path)
            for i, page in enumerate(reader.pages, 1):
                text = page.extract_text()
                if text and keyword in text.lower():
                    snippet = next((line.strip() for line in text.split('\n') if keyword in line.lower()), '[keyword found]')
                    results.append([os.path.basename(file_path), f"Page {i}: {snippet}"])
    except Exception:
        pass

@app.route("/", methods=["GET", "POST"])
def index():
    global last_results
    last_results = []
    if request.method == "POST":
        keyword = request.form.get("keyword", "").lower()
        for foldername, _, filenames in os.walk(root_folder):
            for filename in filenames:
                file_path = os.path.join(foldername, filename)
                if filename.lower().endswith(('.txt', '.csv', '.json', '.pdf')):
                    search_in_file(file_path, keyword, last_results)
        return render_template("index.html", results=last_results, keyword=keyword)
    return render_template("index.html", results=[])

@app.route('/export')
def export():
    global last_results
    output = BytesIO()
    content = '\n'.join(f"{row[0]} - {row[1]}" for row in last_results)
    output.write(content.encode('utf-8'))
    output.seek(0)
    return send_file(output, mimetype='text/plain', as_attachment=True, download_name='osint_results.txt')

def handler(environ, start_response):
    return app(environ, start_response)
