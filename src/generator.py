from jinja2 import Environment, FileSystemLoader
from datetime import datetime
from typing import Dict, Any
from src.interfaces import ContentGenerator


def format_date(value: Any) -> str:
    """Format resume dates consistently while preserving unknown values."""
    if value is None or value == '':
        return ''

    text = str(value)
    if text.lower() == 'present':
        return 'Present'

    for date_format in ('%Y-%m-%d', '%Y-%m'):
        try:
            return datetime.strptime(text, date_format).strftime('%b %Y')
        except ValueError:
            pass

    return text


class Jinja2Generator(ContentGenerator):
    """Generates content using Jinja2 templates."""
    
    def __init__(self, template_dir: str):
        self.env = Environment(loader=FileSystemLoader(template_dir))
        self.env.filters['format_date'] = format_date

    def generate(self, context: Dict[str, Any], template_name: str, output_path: str) -> None:
        template = self.env.get_template(template_name)
        output = template.render(**context)
        output = '\n'.join(line.rstrip() for line in output.splitlines())

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output)

        print(f"Successfully generated {output_path}")
