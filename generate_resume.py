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

def generate_markdown(profile):
    basics = profile.get('basics', {})
    lines = []

    # Header
    lines.append(f"# {basics.get('name', 'Name')}")
    lines.append(f"**{basics.get('label', '')}**")
    lines.append("")
    
    # Contact / Links
    links = []
    if basics.get('email'): links.append(f"[Email](mailto:{basics['email']})")
    if basics.get('url'): links.append(f"[Website]({basics['url']})")
    for p in basics.get('profiles', []):
        links.append(f"[{p['network']}]({p['url']})")
    
    if links:
        lines.append(" | ".join(links))
        lines.append("")

    # Summary
    if basics.get('summary'):
        lines.append("## Summary")
        lines.append(basics['summary'])
        lines.append("")

    # Experience
    if profile.get('work'):
        lines.append("## Experience")
        for work in profile['work']:
            name = work.get('name', '')
            position = work.get('position', '')
            start = work.get('startDate', '')
            end = work.get('endDate', 'Present')
            lines.append(f"### {position} at {name}")
            lines.append(f"_{start} - {end}_")
            if work.get('summary'):
                lines.append(f"\n{work['summary']}")
            if work.get('highlights'):
                lines.append("")
                for highlight in work['highlights']:
                    lines.append(f"- {highlight}")
            lines.append("")

    # Skills
    if profile.get('skills'):
        lines.append("## Skills")
        for skill in profile['skills']:
            name = skill.get('name', '')
            keywords = ", ".join(skill.get('keywords', []))
            lines.append(f"- **{name}**: {keywords}")
        lines.append("")

    # Certificates
    if profile.get('certificates'):
        lines.append("## Certificates")
        for cert in profile['certificates']:
            lines.append(f"- {cert.get('name')} ({cert.get('issuer')})")
        lines.append("")

    # Publications
    if profile.get('publications'):
        lines.append("## Publications")
        for pub in profile['publications']:
            lines.append(f"- [{pub.get('name')}]({pub.get('url')}) - {pub.get('publisher')}")
        lines.append("")

    # Projects
    if profile.get('projects'):
        lines.append("## Projects")
        for project in profile['projects']:
            name = project.get('name', '')
            desc = project.get('description', '')
            url = project.get('url', '')
            start = project.get('startDate', '')
            end = project.get('endDate', '')
            
            header = f"### {name}"
            if url:
                header += f" ([Link]({url}))"
            lines.append(header)
            
            if start or end:
                lines.append(f"_{start} - {end}_")
            
            if desc:
                lines.append(f"\n{desc}")
                
            if project.get('highlights'):
                lines.append("")
                for highlight in project['highlights']:
                    lines.append(f"- {highlight}")
            
            if project.get('keywords'):
                lines.append(f"\n**Keywords**: {', '.join(project['keywords'])}")
            
            lines.append("")

    return "\n".join(lines)

def main():
    data_dir = 'data'
    output_path = 'RESUME.md'
    
    if not os.path.exists(data_dir):
        print(f"Error: {data_dir} directory not found.")
        return

    try:
        profile = load_profile(data_dir)
        md_content = generate_markdown(profile)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        print(f"Successfully generated {output_path}")
    except ImportError:
        print("Error: PyYAML is not installed. Please run: pip install pyyaml")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
