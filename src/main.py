import os
from src.loader import YamlDataLoader
from src.generator import Jinja2Generator
from src.ai import GeminiAIProvider

def main():
    data_dir = 'data'
    template_dir = 'templates'
    
    if not os.path.exists(data_dir):
        print(f"Error: {data_dir} directory not found.")
        return

    try:
        # Dependency Injection
        loader = YamlDataLoader(data_dir)
        generator = Jinja2Generator(template_dir)
        ai_provider = GeminiAIProvider()
        
        # Load Data
        profile = loader.load()
        
        # Generate Markdown Resume
        generator.generate(profile, 'resume.md.j2', 'RESUME.md')
        
        # Generate HTML Resume
        generator.generate(profile, 'resume.html.j2', 'resume.html')
        
        # Generate AI Highlight
        ai_highlight = ai_provider.generate_highlight(profile)
        if ai_highlight:
            profile['ai_highlight'] = ai_highlight
            
        # Generate Profile README
        generator.generate(profile, 'readme.md.j2', 'README.md')
        
    except ImportError:
        print("Error: Required libraries not installed.")
        print("Please run: pip install pyyaml jinja2 google-generativeai python-dotenv")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
