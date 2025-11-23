from jinja2 import Environment, FileSystemLoader
from typing import Dict, Any
from src.interfaces import ContentGenerator

class Jinja2Generator(ContentGenerator):
    """Generates content using Jinja2 templates."""
    
    def __init__(self, template_dir: str):
        self.env = Environment(loader=FileSystemLoader(template_dir))

    def generate(self, context: Dict[str, Any], template_name: str, output_path: str) -> None:
        template = self.env.get_template(template_name)
        output = template.render(**context)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output)
        
        print(f"Successfully generated {output_path}")
