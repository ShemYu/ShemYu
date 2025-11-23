import yaml
import os
import glob

def load_profile(data_dir):
    profile = {}
    
    # Load basics
    basics_path = os.path.join(data_dir, 'basics.yaml')
    if os.path.exists(basics_path):
        with open(basics_path, 'r', encoding='utf-8') as f:
            profile['basics'] = yaml.safe_load(f)
    
    # Load other sections
    sections = ['work', 'education', 'certificates', 'publications', 'skills', 'projects']
    for section in sections:
        profile[section] = []
        section_dir = os.path.join(data_dir, section)
        if os.path.exists(section_dir):
            files = sorted(glob.glob(os.path.join(section_dir, '*.yaml')))
            for file_path in files:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    if data:
                        profile[section].append(data)
    
    # Sort sections by startDate descending
    for section in ['work', 'education', 'projects']:
        if section in profile:
            profile[section].sort(key=lambda x: x.get('startDate', ''), reverse=True)
            
    return profile
