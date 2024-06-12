import os
import re
import shutil
from datetime import datetime

BASE_DIRS = ['vas-data/Download_All_In_One', 'vas-data/vas-data-phase2-home (Bang)', 'vas-data/vas-data-phase2-home (Bang)/final-period']
DEST_DIR = 'project/refolder'   

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
    try:
        with open(file_path, 'r') as file:
            for line in file:
                if '*PAR:' in line:
                    year_match = re.search(r'\{(\d{4})-', line)
                    if year_match:
                        year = year_match.group(1)
                        if start_year is None:
                            start_year = year
                        end_year = year
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
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

def get_files_for_participant(participant_id):
    files = []
    display_id = f"P{participant_id[-3:]}"
    cha_files = {}
    wav_files = {}

    for base_dir in BASE_DIRS:
        for root, dirs, files_in_dir in os.walk(base_dir):
            for file_name in files_in_dir:
                if file_name.endswith('.cha') or file_name.endswith('.wav'):
                    parent_dir = os.path.basename(root)
                    if parent_dir.startswith(participant_id):
                        file_path = os.path.join(root, file_name)
                        if file_name.endswith('.cha'):
                            cha_files[file_name] = file_path
                        elif file_name.endswith('.wav'):
                            wav_files[file_name] = file_path

    for cha_file_name, cha_file_path in cha_files.items():
        base_name = cha_file_name.replace('.cha', '')
        wav_file_name = base_name + '.wav'
        if wav_file_name in wav_files:
            start_year, end_year = extract_years_from_cha(cha_file_path)
            formatted_cha_name = format_filename(cha_file_name, start_year, end_year, display_id)
            formatted_wav_name = format_filename(wav_file_name, start_year, end_year, display_id)
            files.append((cha_file_path, formatted_cha_name))
            files.append((wav_files[wav_file_name], formatted_wav_name))
        else:
            print(f"Warning: .cha file {cha_file_name} has no corresponding .wav file")

    return files, display_id

def copy_files_to_local_disk():
    if not os.path.exists(DEST_DIR):
        os.makedirs(DEST_DIR)

    participants = get_participants()
    print(f"Found participants: {participants}")
    for participant_id in participants:
        print(f"Processing participant: {participant_id}")
        files, display_id = get_files_for_participant(participant_id)
        participant_dir = os.path.join(DEST_DIR, display_id)
        if not os.path.exists(participant_dir):
            os.makedirs(participant_dir)

        for file_path, formatted_name in files:
            dest_path = os.path.join(participant_dir, formatted_name)
            try:
                shutil.copy2(file_path, dest_path)
                print(f"Copied {file_path} to {dest_path}")
            except Exception as e:
                print(f"Error copying {file_path} to {dest_path}: {e}")

if __name__ == '__main__':
    copy_files_to_local_disk()