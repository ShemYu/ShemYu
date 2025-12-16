from jinja2 import Environment, FileSystemLoader
from typing import Dict, Any
import subprocess
import os
import shutil
from src.interfaces import ContentGenerator

class Jinja2Generator(ContentGenerator):
    """Generates content using Jinja2 templates."""
    
    def __init__(self, template_dir: str):
        self.env = Environment(loader=FileSystemLoader(template_dir))

    def render(self, context: Dict[str, Any], template_name: str) -> str:
        template = self.env.get_template(template_name)
        # Fix Jinja2 latex conflict with braces if needed, but standard template works if carefully written.
        # However, usually we need custom delimiters for LaTeX in Jinja.
        # For now, let's assume standard delimiters {{ }} worked in my template as I mostly used them in safe places.
        return template.render(**context)

    def generate(self, context: Dict[str, Any], template_name: str, output_path: str) -> None:
        output = self.render(context, template_name)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output)
            
    def compile_pdf(self, context: Dict[str, Any], template_name: str, output_dir: str, filename: str) -> str:
        """
        Generates a .tex file and compiles it to PDF using xelatex.
        Returns path to the generated PDF.
        """
        # 1. Generate .tex
        tex_filename = filename.replace('.pdf', '.tex')
        tex_path = os.path.join(output_dir, tex_filename)
        self.generate(context, template_name, tex_path)
        
        # 2. Check for xelatex
        if not shutil.which('xelatex'):
            raise RuntimeError("xelatex not found. Please install BasicTeX (brew install --cask basictex).")
            
        # 3. Compile
        try:
            # multiple passes might be needed for refs, but usually once is enough for this simple resume
            subprocess.run(
                ['xelatex', '-interaction=nonstopmode', f'-output-directory={output_dir}', tex_path],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            return os.path.join(output_dir, filename)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"LaTeX Compilation Failed: {e.stderr.decode()}")
        
        print(f"Successfully generated {output_path}")
