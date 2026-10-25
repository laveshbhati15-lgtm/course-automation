"""Monaco and Ace editor automation and injection controllers."""

import base64
import time
from typing import Optional
from playwright.sync_api import Page
from course_automation.logger import logger


class MonacoEditorController:
    """Automates code inspection, injection, and execution inside web editors."""

    @staticmethod
    def is_editor_present(page: Page) -> bool:
        """Check whether a Monaco or Ace code editor is mounted on the page."""
        try:
            return bool(
                page.evaluate(
                    """() => {
                        return (window.monaco && window.monaco.editor && window.monaco.editor.getModels().length > 0)
                            || (window.ace && typeof window.ace.edit === 'function')
                            || (document.querySelector('.monaco-editor') !== null);
                    }"""
                )
            )
        except Exception:
            return False

    @staticmethod
    def get_editor_content(page: Page) -> str:
        """Extract the current text buffer from the code editor."""
        try:
            content = page.evaluate(
                """() => {
                    if (window.monaco && window.monaco.editor) {
                        const models = window.monaco.editor.getModels();
                        if (models && models.length > 0) {
                            return models[0].getValue();
                        }
                    }
                    if (window.ace) {
                        const el = document.querySelector('.ace_editor');
                        if (el && window.ace.edit(el)) {
                            return window.ace.edit(el).getValue();
                        }
                    }
                    const ta = document.querySelector('textarea.inputarea');
                    return ta ? ta.value : '';
                }"""
            )
            return content or ""
        except Exception as e:
            logger.warning(f"Failed to read editor buffer: {e}")
            return ""

    @classmethod
    def set_editor_content(cls, page: Page, code: str) -> bool:
        """Inject code using base64 decoding to preserve formatting, newlines, and quotes."""
        b64_code = base64.b64encode(code.encode("utf-8")).decode("ascii")
        try:
            success = page.evaluate(
                f"""() => {{
                    try {{
                        const raw = atob('{b64_code}');
                        if (window.monaco && window.monaco.editor) {{
                            const models = window.monaco.editor.getModels();
                            if (models && models.length > 0) {{
                                models[0].setValue(raw);
                                return true;
                            }}
                        }}
                        if (window.ace) {{
                            const el = document.querySelector('.ace_editor');
                            if (el && window.ace.edit(el)) {{
                                window.ace.edit(el).setValue(raw, -1);
                                return true;
                            }}
                        }}
                    }} catch (e) {{}}
                    return false;
                }}"""
            )

            # Verification check
            current_buffer = cls.get_editor_content(page)
            if current_buffer.strip() == code.strip():
                logger.info("Verified code injection in editor buffer.")
                return True
            return bool(success)
        except Exception as e:
            logger.error(f"Error setting editor content: {e}")
            return False

    @staticmethod
    def click_run(page: Page) -> bool:
        """Click the 'Run' or 'Run Code' button."""
        run_selectors = [
            "button:has-text('Run Code')",
            "button:has-text('Run')",
            "[data-testid='run-code-button']",
            ".run-button",
        ]
        for sel in run_selectors:
            btn = page.locator(sel).first
            if btn.is_visible():
                logger.info(f"Clicking Run button ({sel})...")
                btn.click()
                return True
        logger.warning("Run button not found.")
        return False

    @staticmethod
    def click_submit(page: Page) -> bool:
        """Click the 'Submit' or 'Submit Code' button."""
        submit_selectors = [
            "button:has-text('Submit Code')",
            "button:has-text('Submit')",
            "[data-testid='submit-button']",
            ".submit-button",
        ]
        for sel in submit_selectors:
            btn = page.locator(sel).first
            if btn.is_visible():
                logger.info(f"Clicking Submit button ({sel})...")
                btn.click()
                return True
        logger.warning("Submit button not found.")
        return False
