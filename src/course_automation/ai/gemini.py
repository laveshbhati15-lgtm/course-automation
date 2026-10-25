"""Google Gemini AI provider implementation using google-genai."""

import json
import re
from typing import List, Optional, Tuple
from course_automation.ai.base import BaseAIProvider, MCQReasoningResult
from course_automation.ai.sanitizer import redact_secrets
from course_automation.logger import logger


class GeminiProvider(BaseAIProvider):
    """AI provider using Google Gemini models via google-genai SDK."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-flash-lite-latest"):
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
        result = self.reason_mcq(question, options)
        return result.selected_option_text, result.explanation

    def reason_mcq(
        self,
        question: str,
        options: List[str],
        context: str = ""
    ) -> MCQReasoningResult:
        """Perform structured reasoning over MCQ with step-by-step evaluation and confidence."""
        clean_q = redact_secrets(question)
        clean_options = [f"[{i+1}] {redact_secrets(opt)}" for i, opt in enumerate(options)]
        options_text = "\n".join(clean_options)
        clean_ctx = redact_secrets(context[:1500]) if context else ""

        prompt = (
            f"You are an academic computer science expert and educator.\n"
            f"Evaluate the following multiple-choice question against the provided options.\n\n"
        )
        if clean_ctx:
            prompt += f"Lesson Context / Reference Notes:\n{clean_ctx}\n\n"

        prompt += (
            f"Question:\n{clean_q}\n\n"
            f"Options:\n{options_text}\n\n"
            f"Carefully reason about each option. Identify the single best correct choice.\n"
            f"Respond strictly in the following JSON format:\n"
            f"{{\n"
            f'  "selected_option_index": <1-based integer index of correct option>,\n'
            f'  "selected_option_text": "<exact string text of chosen option>",\n'
            f'  "confidence": <float between 0.0 and 1.0 representing certainty>,\n'
            f'  "explanation": "<step-by-step explanation why this option is correct>",\n'
            f'  "supporting_evidence": "<key concept, theorem, or DBMS principle justifying choice>"\n'
            f"}}\n"
        )

        logger.info(f"Querying Gemini ({self.model_name}) for structured MCQ reasoning...")
        response = self._client.models.generate_content(
            model=self.model_name,
            contents=prompt,
        )
        raw_text = self._strip_markdown_fences(response.text or "{}")

        try:
            # Parse JSON
            match = re.search(r"\{[\s\S]*\}", raw_text)
            json_str = match.group(0) if match else raw_text
            data = json.loads(json_str)

            opt_idx = data.get("selected_option_index")
            opt_text = data.get("selected_option_text") or ""
            confidence = float(data.get("confidence", 0.85))
            explanation = data.get("explanation") or ""
            evidence = data.get("supporting_evidence") or ""

            # Validate index bounds
            if isinstance(opt_idx, int) and 1 <= opt_idx <= len(options):
                if not opt_text:
                    opt_text = options[opt_idx - 1]
            else:
                opt_idx = None

            # Determine if human confirmation should be flagged
            requires_human = confidence < 0.85 or opt_idx is None

            return MCQReasoningResult(
                question=question,
                options=options,
                selected_option_index=opt_idx,
                selected_option_text=opt_text,
                confidence=confidence,
                explanation=explanation,
                supporting_evidence=evidence,
                requires_human_confirmation=requires_human,
            )

        except Exception as e:
            logger.warning(f"Failed to parse Gemini structured JSON: {e}. Falling back to text matching.")
            # Fallback text parsing
            matched_idx = None
            chosen_text = ""
            for i, opt in enumerate(options, 1):
                if opt.lower() in raw_text.lower():
                    matched_idx = i
                    chosen_text = opt
                    break

            return MCQReasoningResult(
                question=question,
                options=options,
                selected_option_index=matched_idx,
                selected_option_text=chosen_text or (options[0] if options else ""),
                confidence=0.6 if matched_idx else 0.3,
                explanation=raw_text[:200],
                requires_human_confirmation=True,
            )
