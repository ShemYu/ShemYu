from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class DataLoader(ABC):
    """Interface for loading profile data."""
    
    @abstractmethod
    def load(self) -> Dict[str, Any]:
        """Load and return the profile data."""
        pass

class ContentGenerator(ABC):
    """Interface for generating content from profile data."""
    
    @abstractmethod
    def generate(self, context: Dict[str, Any], template_name: str, output_path: str) -> None:
        """Generate content based on context and template."""
        pass

class AIProvider(ABC):
    """Interface for AI-powered features."""
    
    @abstractmethod
    def generate_highlight(self, profile: Dict[str, Any]) -> Optional[str]:
        """Generate a professional highlight based on the profile."""
        pass

    @abstractmethod
    def tailor_profile(self, profile: Dict[str, Any], job_description: str) -> Dict[str, Any]:
        """Tailor the profile based on the job description."""
        pass
