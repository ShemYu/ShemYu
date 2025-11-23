import os
import google.generativeai as genai
from dotenv import load_dotenv
from typing import Dict, Any, Optional
from src.interfaces import AIProvider

load_dotenv()

class GeminiAIProvider(AIProvider):
    """Provides AI features using Google Gemini."""
    
    def __init__(self, model_name: str = 'gemini-2.5-flash-lite'):
        self.api_key = os.environ.get('GEMINI_API_KEY')
        self.model_name = model_name
        self._configured = False

    def _configure(self):
        if not self.api_key:
            print("Warning: GEMINI_API_KEY not found. Skipping AI highlight.")
            return False
        
        if not self._configured:
            genai.configure(api_key=self.api_key)
            self._configured = True
        return True

    def generate_highlight(self, profile: Dict[str, Any]) -> Optional[str]:
        if not self._configure():
            return None

        try:
            model = genai.GenerativeModel(self.model_name)
            
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
