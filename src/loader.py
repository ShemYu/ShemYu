import yaml
import os
import glob
import shutil
from typing import Dict, Any, List
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

    def save_basics(self, data: Dict[str, Any]) -> None:
        """Save basics.yaml"""
        file_path = os.path.join(self.data_dir, 'basics.yaml')
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, sort_keys=False)

    def save_section(self, section: str, data_list: List[Dict[str, Any]]) -> None:
        """
        Save a list based section.
        Strategy: Clear the directory and recreate files based on item names or index.
        """
        section_dir = os.path.join(self.data_dir, section)
        
        # Ensure dir exists
        if not os.path.exists(section_dir):
            os.makedirs(section_dir)
            
        # Clear existing yaml files
        files = glob.glob(os.path.join(section_dir, '*.yaml'))
        for f in files:
            os.remove(f)
            
        # Write new files
        for i, item in enumerate(data_list):
            # Try to make a filename from name or position or title
            filename = f"{i:02d}_item.yaml"
            if 'name' in item:
                safe_name = "".join([c if c.isalnum() else "_" for c in item['name']]).lower()
                filename = f"{safe_name}.yaml"
            elif 'institution' in item: # Education
                safe_name = "".join([c if c.isalnum() else "_" for c in item['institution']]).lower()
                filename = f"{safe_name}.yaml"
                
            file_path = os.path.join(section_dir, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(item, f, allow_unicode=True, sort_keys=False)
