from flask import Flask, render_template, send_from_directory
import os
import re
from datetime import datetime

app = Flask(__name__)

BASE_DIRS = ['vas-data/Download_All_In_One', 'vas-data/vas-data-phase2-home (Bang)', 'vas-data/vas-data-phase2-home (Bang)/final-period']

def get_participants():
    participants = set()
    for base_dir in BASE_DIRS:
        for root, dirs, files in os.walk(base_dir):
            for dir_name in dirs:
                match = re.match(r'VASP\d{4}', dir_name)
                if match:
                    participants.add(match.group(0))
    return sorted(participants)

def remove_participant_id(filename):
    return re.sub(r'^VASP\d{4}_', '', filename)

def extract_years_from_cha(file_path):
    start_year = None
    end_year = None
    with open(file_path, 'r') as file:
        for line in file:
            if '*PAR:' in line:
                year_match = re.search(r'\{(\d{4})-', line)
                if year_match:
                    year = year_match.group(1)
                    if start_year is None:
                        start_year = year
                    end_year = year
    return start_year, end_year

def format_filename(filename, start_year, end_year, display_id):
    filename = remove_participant_id(filename)
    match = re.match(r'(\d{4})(\d{4})\.(cha|wav)', filename)
    if match:
        start = match.group(1)
        end = match.group(2)
        extension = match.group(3)
        return f"{display_id}_{start[:2]}{start[2:]}_{start_year}-{end[:2]}{end[2:]}_{end_year}.{extension}"
    return filename

def parse_date_from_filename(formatted_name):
    match = re.match(r'P\d{3}_(\d{2})(\d{2})_(\d{4})-(\d{2})(\d{2})_(\d{4})\.(cha|wav)', formatted_name)
    if match:
        start_month = match.group(1)
        start_day = match.group(2)
        start_year = match.group(3)
        end_month = match.group(4)
        end_day = match.group(5)
        end_year = match.group(6)
        try:
            start_date = datetime.strptime(f"{start_year}-{start_month}-{start_day}", "%Y-%m-%d")
            end_date = datetime.strptime(f"{end_year}-{end_month}-{end_day}", "%Y-%m-%d")
            return start_date, end_date
        except ValueError:
            return None, None
    return None, None

def get_files_for_participant(participant_id):
    files = []
    year_info = {}
    display_id = f"P{participant_id[-3:]}"
    for base_dir in BASE_DIRS:
        for root, dirs, files_in_dir in os.walk(base_dir):
            for file_name in files_in_dir:
                if file_name.endswith('.cha') or file_name.endswith('.wav'):
                    parent_dir = os.path.basename(root)
                    if parent_dir.startswith(participant_id):
                        file_path = os.path.join(root, file_name)
                        if file_name.endswith('.cha'):
                            start_year, end_year = extract_years_from_cha(file_path)
                            year_info[file_name] = (start_year, end_year)
                            formatted_name = format_filename(file_name, start_year, end_year, display_id)
                            files.append((os.path.relpath(file_path, base_dir), formatted_name))
                        elif file_name.endswith('.wav'):
                            cha_file_name = file_name.replace('.wav', '.cha')
                            if cha_file_name in year_info:
                                start_year, end_year = year_info[cha_file_name]
                                formatted_name = format_filename(file_name, start_year, end_year, display_id)
                                files.append((os.path.relpath(file_path, base_dir), formatted_name))
    files.sort(key=lambda x: parse_date_from_filename(x[1])[0] or datetime.min)
    return files

@app.route('/')
def index():
    participants = get_participants()
    return render_template('index.html', participants=participants)

@app.route('/participant/<participant_id>')
def participant(participant_id):
    files = get_files_for_participant(participant_id)
    display_id = f"P{participant_id[-3:]}"
    return render_template('participant.html', participant_id=participant_id, display_id=display_id, files=files)

@app.route('/files/<path:filename>')
def download_file(filename):
    for base_dir in BASE_DIRS:
        file_path = os.path.join(base_dir, filename)
        if os.path.exists(file_path):
            return send_from_directory(base_dir, filename)
    return "File not found", 404

if __name__ == '__main__':
    app.run(debug=True)