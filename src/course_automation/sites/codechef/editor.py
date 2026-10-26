"""Editor automation, detection, and injection controller for Monaco, CodeMirror, and Ace."""

import base64
import time
from typing import Any, List, Optional
from playwright.sync_api import Page
from course_automation.logger import logger


class MonacoEditorController:
    """Automates code inspection, injection, and execution inside web editors across frames."""

    @staticmethod
    def _get_frames(page: Any) -> List[Any]:
        """Retrieve all active frames on page, falling back to [page]."""
        try:
            frames = getattr(page, "frames", None)
            if isinstance(frames, (list, tuple)):
                return [f for f in frames if f is not None] or [page]
        except Exception:
            pass
        return [page]

    @classmethod
    def is_editor_present(cls, page: Page) -> bool:
        """Check whether Monaco, CodeMirror 5/6, or Ace editor is mounted in any browsing context."""
        js_check = """() => {
            // Monaco
            const monacoEl = document.querySelector('.monaco-editor');
            const isMonaco = monacoEl && (monacoEl.offsetWidth > 0 || monacoEl.offsetHeight > 0 || monacoEl.getClientRects().length > 0);

            // CodeMirror 5
            const cm5El = document.querySelector('.CodeMirror');
            const isCm5 = cm5El && (cm5El.offsetWidth > 0 || cm5El.offsetHeight > 0 || cm5El.getClientRects().length > 0);

            // CodeMirror 6
            const cm6El = document.querySelector('.cm-editor, .cm-content');
            const isCm6 = cm6El && (cm6El.offsetWidth > 0 || cm6El.offsetHeight > 0 || cm6El.getClientRects().length > 0);

            // Ace
            const isAce = Boolean(window.ace && typeof window.ace.edit === 'function' && document.querySelector('.ace_editor'));

            // Fallback inputarea
            const ta = document.querySelector('textarea.inputarea, textarea.ace_text-input');
            const isTa = ta && (ta.offsetWidth > 0 || ta.offsetHeight > 0);

            return Boolean(isMonaco || isCm5 || isCm6 || isAce || isTa);
        }"""

        for frame in cls._get_frames(page):
            try:
                res = frame.evaluate(js_check)
                if res is True:
                    return True
            except Exception:
                continue
        return False

    @classmethod
    def wait_for_editor_ready(cls, page: Page, timeout_seconds: float = 8.0) -> bool:
        """Poll across all page frames until an editor is mounted and visible."""
        start_time = time.time()
        while time.time() - start_time < timeout_seconds:
            if cls.is_editor_present(page):
                return True
            time.sleep(0.25)
        return False

    @classmethod
    def get_editor_content(cls, page: Page) -> str:
        """Extract the current text buffer from the code editor across all frames."""
        js_read = """() => {
            // 1. Monaco
            try {
                if (window.monaco && window.monaco.editor) {
                    const models = window.monaco.editor.getModels();
                    if (models && models.length > 0) {
                        return models[0].getValue();
                    }
                }
            } catch (e) {}

            // 2. CodeMirror 5
            try {
                const cm5El = document.querySelector('.CodeMirror');
                if (cm5El && cm5El.CodeMirror && typeof cm5El.CodeMirror.getValue === 'function') {
                    return cm5El.CodeMirror.getValue();
                }
            } catch (e) {}

            // 3. CodeMirror 6
            try {
                const cm6Content = document.querySelector('.cm-content');
                if (cm6Content) {
                    const cmEditor = document.querySelector('.cm-editor');
                    const cmView = (cm6Content && cm6Content.cmView) || (cmEditor && cmEditor.cmView);
                    if (cmView && cmView.view && cmView.view.state && cmView.view.state.doc) {
                        return cmView.view.state.doc.toString();
                    }
                    return cm6Content.innerText || cm6Content.textContent || '';
                }
            } catch (e) {}

            // 4. Ace
            try {
                if (window.ace && typeof window.ace.edit === 'function') {
                    const el = document.querySelector('.ace_editor');
                    if (el) {
                        const editor = window.ace.edit(el);
                        if (editor && typeof editor.getValue === 'function') {
                            return editor.getValue();
                        }
                    }
                }
            } catch (e) {}

            // 5. Fallback textarea
            try {
                const ta = document.querySelector('textarea.inputarea, textarea.ace_text-input, textarea');
                if (ta && ta.value) {
                    return ta.value;
                }
            } catch (e) {}

            return null;
        }"""

        for frame in cls._get_frames(page):
            try:
                content = frame.evaluate(js_read)
                if content is not None:
                    return str(content)
            except Exception as e:
                logger.debug(f"Frame content read attempt error: {e}")
                continue
        return ""

    @classmethod
    def set_editor_content(cls, page: Page, code: str) -> bool:
        """Inject code using base64 decoding and verify the editor buffer afterwards."""
        b64_code = base64.b64encode(code.encode("utf-8")).decode("ascii")
        js_inject = f"""() => {{
            try {{
                const raw = atob('{b64_code}');

                // 1. Monaco
                if (window.monaco && window.monaco.editor) {{
                    const models = window.monaco.editor.getModels();
                    if (models && models.length > 0) {{
                        models[0].setValue(raw);
                        return true;
                    }}
                }}

                // 2. CodeMirror 5
                const cm5El = document.querySelector('.CodeMirror');
                if (cm5El && cm5El.CodeMirror && typeof cm5El.CodeMirror.setValue === 'function') {{
                    cm5El.CodeMirror.setValue(raw);
                    return true;
                }}

                // 3. CodeMirror 6
                const cm6Content = document.querySelector('.cm-content');
                if (cm6Content) {{
                    const cmEditor = document.querySelector('.cm-editor');
                    const cmView = (cm6Content && cm6Content.cmView) || (cmEditor && cmEditor.cmView);
                    if (cmView && cmView.view && typeof cmView.view.dispatch === 'function') {{
                        const view = cmView.view;
                        view.dispatch({{
                            changes: {{ from: 0, to: view.state.doc.length, insert: raw }}
                        }});
                        return true;
                    }}
                    cm6Content.focus();
                    if (document.execCommand) {{
                        document.execCommand('selectAll', false, null);
                        document.execCommand('insertText', false, raw);
                        return true;
                    }}
                    cm6Content.innerText = raw;
                    cm6Content.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    return true;
                }}

                // 4. Ace
                if (window.ace && typeof window.ace.edit === 'function') {{
                    const el = document.querySelector('.ace_editor');
                    if (el) {{
                        const editor = window.ace.edit(el);
                        if (editor && typeof editor.setValue === 'function') {{
                            editor.setValue(raw, -1);
                            return true;
                        }}
                    }}
                }}

                // 5. Fallback textarea
                const ta = document.querySelector('textarea.inputarea, textarea');
                if (ta) {{
                    ta.value = raw;
                    ta.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    ta.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    return true;
                }}
            }} catch (e) {{}}
            return false;
        }}"""

        injected_somewhere = False
        for frame in cls._get_frames(page):
            try:
                res = frame.evaluate(js_inject)
                if res is True:
                    injected_somewhere = True
                    break
            except Exception as e:
                logger.debug(f"Frame injection attempt error: {e}")
                continue

        # Post-injection buffer verification check across frames
        current_buffer = cls.get_editor_content(page)
        expected_clean = code.strip()
        actual_clean = current_buffer.strip()

        if actual_clean == expected_clean or (expected_clean and expected_clean in actual_clean):
            logger.info("Verified code injection in editor buffer.")
            return True

        if injected_somewhere:
            logger.warning(
                f"Injection script succeeded but buffer verification failed. "
                f"Expected {len(expected_clean)} chars, found {len(actual_clean)} chars."
            )
            if len(actual_clean) > 0 and len(actual_clean) >= len(expected_clean) * 0.9:
                return True

        logger.error("Failed to verify code injection in editor buffer.")
        return False

    @classmethod
    def click_run(cls, page: Page) -> bool:
        """Click the 'Run' or 'Run Code' button across all frames."""
        run_selectors = [
            "button:has-text('Run Code')",
            "button:has-text('Run')",
            "[data-testid='run-code-button']",
            ".run-button",
            "button[class*='_runButton_']",
            "button[class*='_run_']",
        ]
        for frame in cls._get_frames(page):
            for sel in run_selectors:
                try:
                    btn = frame.locator(sel).first
                    if hasattr(btn, "is_visible") and btn.is_visible():
                        logger.info(f"Clicking Run button ({sel})...")
                        btn.click()
                        return True
                except Exception:
                    continue
        logger.warning("Run button not found.")
        return False

    @classmethod
    def click_submit(cls, page: Page) -> bool:
        """Click the 'Submit' or 'Submit Code' button across all frames."""
        submit_selectors = [
            "button:has-text('Submit Code')",
            "button:has-text('Submit')",
            "[data-testid='submit-button']",
            ".submit-button",
            "button[class*='_submitButton_']",
            "button[class*='_submit_']",
        ]
        for frame in cls._get_frames(page):
            for sel in submit_selectors:
                try:
                    btn = frame.locator(sel).first
                    if hasattr(btn, "is_visible") and btn.is_visible():
                        logger.info(f"Clicking Submit button ({sel})...")
                        btn.click()
                        return True
                except Exception:
                    continue
        logger.warning("Submit button not found.")
        return False


# Backward compatibility alias
WebEditorController = MonacoEditorController
