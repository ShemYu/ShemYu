from abc import ABC, abstractmethod
from typing import Any, Dict


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
