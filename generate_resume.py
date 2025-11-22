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

from jinja2 import Environment, FileSystemLoader

def generate_resume(profile, template_name, output_path):
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template(template_name)
    output = template.render(**profile)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(output)
    
    print(f"Successfully generated {output_path}")


def update_readme(md_content, readme_path='README.md'):
    if not os.path.exists(readme_path):
        print(f"Warning: {readme_path} not found. Skipping update.")
        return

    with open(readme_path, 'r', encoding='utf-8') as f:
        readme_content = f.read()

    start_marker = "<!-- RESUME_START -->"
    end_marker = "<!-- RESUME_END -->"

    if start_marker not in readme_content or end_marker not in readme_content:
        print(f"Warning: Markers {start_marker} and {end_marker} not found in {readme_path}. Skipping update.")
        return

    start_index = readme_content.find(start_marker) + len(start_marker)
    end_index = readme_content.find(end_marker)

    new_readme_content = (
        readme_content[:start_index] +
        "\n" + md_content + "\n" +
        readme_content[end_index:]
    )

    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(new_readme_content)
    
    print(f"Successfully updated {readme_path}")

import google.generativeai as genai

def generate_ai_highlight(profile):
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        print("Warning: GEMINI_API_KEY not found. Skipping AI highlight.")
        return None

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Construct a prompt from the profile
        basics = profile.get('basics', {})
        work = profile.get('work', [])
        skills = profile.get('skills', [])
        
        prompt = f"""
        You are a professional career coach. Write a short, engaging, and impressive "Professional Highlight" (max 100 words) for a GitHub Profile README based on the following profile:
        
        Name: {basics.get('name')}
        Label: {basics.get('label')}
        Summary: {basics.get('summary')}
        
        Latest Role: {work[0].get('position')} at {work[0].get('name')} if work else 'N/A'
        Top Skills: {', '.join([s.get('name') for s in skills[:3]])}
        
        Focus on their unique value proposition and recent achievements. Use emojis sparingly.
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error generating AI highlight: {e}")
        return None

def main():
    data_dir = 'data'
    
    if not os.path.exists(data_dir):
        print(f"Error: {data_dir} directory not found.")
        return

    try:
        profile = load_profile(data_dir)
        
        # Generate Markdown Resume
        generate_resume(profile, 'resume.md.j2', 'RESUME.md')
        
        # Generate HTML Resume
        generate_resume(profile, 'resume.html.j2', 'resume.html')
        
        # Generate AI Highlight
        ai_highlight = generate_ai_highlight(profile)
        if ai_highlight:
            profile['ai_highlight'] = ai_highlight
            
        # Generate Profile README
        generate_resume(profile, 'readme.md.j2', 'README.md')
        
    except ImportError:
        print("Error: PyYAML, Jinja2, or google-generativeai is not installed.")
        print("Please run: pip install pyyaml jinja2 google-generativeai")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
