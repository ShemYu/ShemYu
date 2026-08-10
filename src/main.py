import os
import sys
from src.loader import YamlDataLoader
from src.generator import Jinja2Generator
from src.ai import GeminiAIProvider

def main(target_jd=None):
    data_dir = 'data'
    template_dir = 'templates'

    if not os.path.exists(data_dir):
        raise FileNotFoundError(f"{data_dir} directory not found.")
    if target_jd and not os.path.exists(target_jd):
        raise FileNotFoundError(f"JD file not found: {target_jd}")

    loader = YamlDataLoader(data_dir)
    generator = Jinja2Generator(template_dir)
    output_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)

    profile = loader.load()

    if target_jd:
        print(f"Targeting JD: {target_jd}")
        with open(target_jd, 'r', encoding='utf-8') as f:
            jd_text = f.read()
        print("Tailoring profile with AI...")
        profile = GeminiAIProvider().tailor_profile(profile, jd_text)
        generator.generate(profile, 'resume.md.j2', os.path.join(output_dir, 'RESUME_tailored.md'))
        generator.generate(profile, 'resume.html.j2', os.path.join(output_dir, 'resume_tailored.html'))
        generator.generate(profile, 'resume_bible.html.j2', os.path.join(output_dir, 'resume_bible_tailored.html'))
        return

    generator.generate(profile, 'resume.md.j2', 'RESUME.md')
    generator.generate(profile, 'resume.html.j2', os.path.join(output_dir, 'resume.html'))
    generator.generate(profile, 'resume_bible.html.j2', os.path.join(output_dir, 'resume_bible.html'))
    generator.generate(profile, 'readme.md.j2', 'README.md')

if __name__ == "__main__":
    try:
        main(sys.argv[1] if len(sys.argv) > 1 else None)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
