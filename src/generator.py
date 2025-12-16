from jinja2 import Environment, FileSystemLoader
from typing import Dict, Any
from src.interfaces import ContentGenerator

class Jinja2Generator(ContentGenerator):
    """Generates content using Jinja2 templates."""
    
    def __init__(self, template_dir: str):
        self.env = Environment(loader=FileSystemLoader(template_dir))

    def render(self, context: Dict[str, Any], template_name: str) -> str:
        template = self.env.get_template(template_name)
        return template.render(**context)

    def generate(self, context: Dict[str, Any], template_name: str, output_path: str) -> None:
        output = self.render(context, template_name)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output)
        
        print(f"Successfully generated {output_path}")
