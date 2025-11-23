import yaml
import os
import glob
from typing import Dict, Any
from src.interfaces import DataLoader

class YamlDataLoader(DataLoader):
    """Loads profile data from YAML files."""
    
    def __init__(self, data_dir: str):
        self.data_dir = data_dir

    def load(self) -> Dict[str, Any]:
        profile = {}
        
        # Load basics
        basics_path = os.path.join(self.data_dir, 'basics.yaml')
        if os.path.exists(basics_path):
            with open(basics_path, 'r', encoding='utf-8') as f:
                profile['basics'] = yaml.safe_load(f)
        
        # Load other sections
        sections = ['work', 'education', 'certificates', 'publications', 'skills', 'projects']
        for section in sections:
            profile[section] = []
            section_dir = os.path.join(self.data_dir, section)
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
