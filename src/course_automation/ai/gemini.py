"""Google Gemini AI provider implementation using google-genai."""

from typing import List, Optional, Tuple
from course_automation.ai.base import BaseAIProvider
from course_automation.ai.sanitizer import redact_secrets
from course_automation.logger import logger


class GeminiProvider(BaseAIProvider):
    """AI provider using Google Gemini models via google-genai SDK."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.5-flash"):
        self.api_key = api_key
        self.model_name = model
        self._client = None

        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY is not set. Set it in .env or your environment, "
                "or disable AI assistance with --no-ai."
            )

        try:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
        except ImportError:
            raise RuntimeError(
                "The 'google-genai' library is required to use the Gemini provider. "
                "Install it with: pip install 'course-automation[ai]' or pip install google-genai"
            )

    def _strip_markdown_fences(self, text: str) -> str:
        """Remove markdown code fences from output."""
        cleaned = text.strip()
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        return "\n".join(lines).strip()

    def generate_solution(
        self,
        problem_statement: str,
        language: str,
        starter_code: str = ""
    ) -> str:
        """Generate source code solution matching problem requirements."""
        clean_statement = redact_secrets(problem_statement)
        clean_starter = redact_secrets(starter_code)

        prompt = (
            f"You are an expert software engineer and competitive programmer.\n"
            f"Solve the following programming problem in {language}.\n"
            f"CRITICAL REQUIREMENTS:\n"
            f"1. Return ONLY the complete executable source code.\n"
            f"2. Do not wrap code in conversational preamble or explanation.\n"
            f"3. Strictly adhere to input/output formatting, types, and constraints.\n"
        )
        if clean_starter:
            prompt += (
                f"4. If starter code provides a specific class/function signature, preserve it exactly.\n"
                f"Starter code:\n{clean_starter}\n"
            )

        prompt += f"\nProblem Statement:\n{clean_statement}\n"

        logger.info(f"Querying Gemini ({self.model_name}) for {language} solution...")
        response = self._client.models.generate_content(
            model=self.model_name,
            contents=prompt,
        )
        raw_code = response.text or ""
        return self._strip_markdown_fences(raw_code)

    def solve_mcq(
        self,
        question: str,
        options: List[str]
    ) -> Tuple[str, str]:
        """Solve multiple choice question, returning chosen option and explanation."""
        clean_q = redact_secrets(question)
        clean_options = [f"- {redact_secrets(opt)}" for opt in options]
        options_text = "\n".join(clean_options)

        prompt = (
            f"Answer the following multiple-choice question.\n"
            f"Question:\n{clean_q}\n\n"
            f"Options:\n{options_text}\n\n"
            f"Provide your answer in the following format:\n"
            f"ANSWER: [exact text of the chosen option]\n"
            f"EXPLANATION: [brief 1-2 sentence explanation]\n"
        )

        response = self._client.models.generate_content(
            model=self.model_name,
            contents=prompt,
        )
        text = response.text or ""

        answer = ""
        explanation = ""
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("ANSWER:"):
                answer = line.replace("ANSWER:", "").strip()
            elif line.startswith("EXPLANATION:"):
                explanation = line.replace("EXPLANATION:", "").strip()

        if not answer and text:
            answer = text.splitlines()[0].strip()

        return answer, explanation
