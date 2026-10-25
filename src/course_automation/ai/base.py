"""Abstract base interface for AI providers."""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from pydantic import BaseModel, Field


class MCQReasoningResult(BaseModel):
    """Structured reasoning result for multiple choice questions."""
    question: str
    options: List[str]
    selected_option_index: Optional[int] = None  # 1-based index
    selected_option_text: str = ""
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    explanation: str = ""
    supporting_evidence: str = ""
    requires_human_confirmation: bool = False


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

    def reason_mcq(
        self,
        question: str,
        options: List[str],
        context: str = ""
    ) -> MCQReasoningResult:
        """Perform structured reasoning over an MCQ with confidence assessment."""
        # Default fallback calls solve_mcq
        answer, explanation = self.solve_mcq(question, options)
        idx = None
        for i, opt in enumerate(options, 1):
            if opt.strip().lower() == answer.strip().lower() or answer.strip().lower() in opt.strip().lower():
                idx = i
                break
        return MCQReasoningResult(
            question=question,
            options=options,
            selected_option_index=idx,
            selected_option_text=answer,
            confidence=0.9 if idx else 0.5,
            explanation=explanation,
            requires_human_confirmation=False if idx else True,
        )
