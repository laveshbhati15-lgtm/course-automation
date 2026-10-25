"""Abstract base interface for AI providers."""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple


class BaseAIProvider(ABC):
    """Abstract interface for AI code generation and question solving."""

    @abstractmethod
    def generate_solution(
        self,
        problem_statement: str,
        language: str,
        starter_code: str = ""
    ) -> str:
        """Generate source code solution for a programming exercise."""
        pass

    @abstractmethod
    def solve_mcq(
        self,
        question: str,
        options: List[str]
    ) -> Tuple[str, str]:
        """Solve multiple-choice question. Returns (selected_option, explanation)."""
        pass
