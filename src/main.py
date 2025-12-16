import os
import sys
from src.loader import YamlDataLoader
from src.generator import Jinja2Generator
from src.ai import GeminiAIProvider

def main():
    data_dir = 'data'
    template_dir = 'templates'
    
    # Check for JD file argument
    target_jd = None
    if len(sys.argv) > 1:
        target_jd = sys.argv[1]
        print(f"Targeting JD: {target_jd}")
    
    if not os.path.exists(data_dir):
        print(f"Error: {data_dir} directory not found.")
        return

    try:
        # Dependency Injection
        loader = YamlDataLoader(data_dir)
        generator = Jinja2Generator(template_dir)
        ai_provider = GeminiAIProvider()
        
        # Prepare Output Directory
        output_dir = 'output'
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Load Data
        profile = loader.load()

            
        # Tailor Profile if JD provided
        if target_jd and os.path.exists(target_jd):
            with open(target_jd, 'r') as f:
                jd_text = f.read()
            print("Tailoring profile with AI...")
            profile = ai_provider.tailor_profile(profile, jd_text)
            output_suffix = "_tailored"
        else:
            output_suffix = ""
        
        # Generate Markdown Resume
        generator.generate(profile, 'resume.md.j2', os.path.join(output_dir, f'RESUME{output_suffix}.md'))
        
        # Generate HTML Resume
        generator.generate(profile, 'resume.html.j2', os.path.join(output_dir, f'resume{output_suffix}.html'))
        
        # Generate Bible HTML Resume
        generator.generate(profile, 'resume_bible.html.j2', os.path.join(output_dir, f'resume_bible{output_suffix}.html'))
        
        # Generate AI Highlight (Only for full profile)
        if not output_suffix:
            ai_highlight = ai_provider.generate_highlight(profile)
            if ai_highlight:
                profile['ai_highlight'] = ai_highlight
                
            # Generate Profile README
            # Keep README in root as it's for GitHub Profile
            generator.generate(profile, 'readme.md.j2', 'README.md')
        
    except ImportError:
        print("Error: Required libraries not installed.")
        print("Please run: pip install pyyaml jinja2 google-generativeai python-dotenv")
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
