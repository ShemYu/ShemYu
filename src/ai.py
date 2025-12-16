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

    def tailor_profile(self, profile: Dict[str, Any], job_description: str) -> Dict[str, Any]:
        """
        Uses Gemini to filter and rewrite the profile to match the JD.
        """
        if not self._configure():
            print("AI not configured, returning original profile.")
            return profile
            
        try:
            model = genai.GenerativeModel(self.model_name, generation_config={"response_mime_type": "application/json"})
            
            # Prepare context (avoid sending too much noise if possible, but sending full profile is usually fine for Gemini 1.5/2.0)
            import json
            profile_json = json.dumps(profile, default=str)
            
            prompt = f"""
            You are an expert Resume Tailor. Your goal is to adapt a candidate's "Master Profile" (Bible) to fit a specific "Job Description" (JD).
            
            RULES:
            1.  **Strict Size Limit**: The output MUST fit on ONE PAGE when formatted. This means:
                -   Select MAX 3-4 most relevant WORK EXPERIENCES.
                -   For each selected work experience, select MAX 3-4 bullet points that match the JD keywords.
                -   Select MAX 2-3 most relevant PROJECTS.
                -   Keep the Summary concise (rewrite it to target the JD, max 3 lines).
            2.  **Relevance**: Prioritize experiences and skills that directly match the JD.
            3.  **Structure**: The output must be a valid JSON object matching the exact structure of the input `Profile`.
            4.  **Content**: 
                -   You may rewrite bullet points to emphasize impact and JD keywords.
                -   Do NOT invent facts. Only use info present in the Profile.
                -   Remove completely irrelevant sections if needed (but keep Basics, Education).
            
            ---
            JOB DESCRIPTION:
            {job_description}
            
            ---
            CANDIDATE PROFILE (JSON):
            {profile_json}
            
            ---
            Output the tailored JSON profile:
            """
            
            response = model.generate_content(prompt)
            tailored_profile = json.loads(response.text)
            return tailored_profile
            
        except Exception as e:
            print(f"Error tailoring profile: {e}")
            # Fallback to original if AI fails
            return profile
