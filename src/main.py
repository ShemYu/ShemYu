import os
from src.loader import load_profile
from src.generator import generate_resume
from src.ai import generate_ai_highlight

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
        print("Please run: pip install pyyaml jinja2 google-generativeai python-dotenv")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
