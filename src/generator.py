from jinja2 import Environment, FileSystemLoader

def generate_resume(profile, template_name, output_path):
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template(template_name)
    output = template.render(**profile)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(output)
    
    print(f"Successfully generated {output_path}")
