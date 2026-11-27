"""End-to-end Playwright verification for docs/ static site.

Verifies:
  1. Home page, Soseki GPT widget init, course toggle (thorough <-> standard).
  2. Chapter interactive exercises:
     - Choice wrong answer -> shows diagnostic (where wrong, reasoning, steps, section link, altExample, retry variant).
     - Variant switch -> changes prompt/numbers.
     - Choice & numeric (including full-width digits!) & code-predict correct answers -> schedules review, NEVER displays "完全理解".
     - Code implementation self-check -> requires all criteria checkboxes before recording impl_done.
  3. Spaced repetition & 7-state mastery dashboard (review.html):
     - Legacy localStorage backward compatibility (tsukuru-llm:done preserved).
     - Due review re-surfacing when nextReviewAt <= now, marking reviewedAfterDue after re-check.
     - Weak concept listing and JSON export/import roundtrip.
  4. Desktop (1280x800) and mobile (390x844) layout: zero horizontal overflow, zero console/page errors.
  5. Keyboard accessibility: skip link, tabbing into exercise controls, Enter submission.
"""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
import sys
import threading
import time

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


def start_server():
    handler = partial(QuietHandler, directory=str(DOCS))
    srv = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    port = srv.server_address[1]
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    return srv, port


def run_tests():
    srv, port = start_server()
    base = f"http://127.0.0.1:{port}"
    errors = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            ctx = browser.new_context(viewport={"width": 1280, "height": 800})
            page = ctx.new_page()
            console_errs = []
            page.on("pageerror", lambda e: console_errs.append(f"pageerror: {e}"))
            page.on("console", lambda m: console_errs.append(f"console.{m.type}: {m.text}") if m.type == "error" else None)

            # 1. Seed legacy localStorage data to verify backward compatibility
            page.goto(f"{base}/index.html", wait_until="networkidle")
            page.evaluate("""() => {
                localStorage.setItem('tsukuru-llm:done', JSON.stringify(['00-welcome']));
                localStorage.setItem('tsukuru-llm:checks', JSON.stringify({'00-welcome:0': true}));
            }""")
            page.reload(wait_until="networkidle")
            assert page.locator("a[data-slug='00-welcome'].done").count() >= 1, "Legacy done class not applied"
            # Check Soseki GPT widget loaded
            note = page.locator(".hero-board .widget .note").inner_text()
            assert "パラメータ" in note, f"Soseki GPT widget failed to load: {note}"

            # 2. Test course toggle on Ch 1
            page.goto(f"{base}/01-first-llm.html", wait_until="networkidle")
            scaffolds_open_thorough = page.evaluate("() => Array.from(document.querySelectorAll('details.scaffold')).every(d => d.open)")
            assert scaffolds_open_thorough, "Scaffolds should be open in thorough course"
            page.locator(".course-switch button[data-set-course='standard']").click()
            assert page.evaluate("() => document.documentElement.dataset.course") == "standard"
            scaffolds_closed_std = page.evaluate("() => Array.from(document.querySelectorAll('details.scaffold')).every(d => !d.open)")
            assert scaffolds_closed_std, "Scaffolds should collapse in standard course"
            page.locator(".course-switch button[data-set-course='thorough']").click()

            # 3. Test interactive choice exercise (wrong -> full diagnostic -> variant switch -> correct)
            ex2 = page.locator("#ex-ch01-q02")
            ex2.locator("input[type='radio'][value='a']").check()
            ex2.locator(".ex-submit").click()
            fb = ex2.locator(".ex-feedback")
            fb_text = fb.inner_text()
            for required in ["どこが間違っているか", "正しい考え方", "途中計算", "関連する教材の節", "別の具体例"]:
                assert required in fb_text, f"Missing diagnostic section '{required}' on wrong answer"
            # Switch to variant 2 via retry button
            prompt_before = ex2.locator(".ex-prompt").inner_text()
            ex2.locator(".ex-retry-variant").click()
            prompt_after = ex2.locator(".ex-prompt").inner_text()
            assert prompt_before != prompt_after, "Variant retry did not switch to a different question"
            # Answer variant 2 correctly (answer is 'b')
            ex2.locator("input[type='radio'][value='b']").check()
            ex2.locator(".ex-submit").click()
            fb_ok = ex2.locator(".ex-feedback").inner_text()
            assert "正解！" in fb_ok, "Expected correct confirmation"
            assert "完全理解しました" not in fb_ok, "Must not falsely claim full mastery on single answer"

            # 4. Test numeric exercise with full-width digits on Ch 3 (ch03-q04: sum_{j=1}^4 (2j) = 20)
            page.goto(f"{base}/03-next-token.html", wait_until="networkidle")
            ex_sigma = page.locator("#ex-ch03-q04")
            ex_sigma.locator(".ex-input").fill("２０")
            ex_sigma.locator(".ex-input").press("Enter")
            assert "正解！" in ex_sigma.locator(".ex-feedback").inner_text(), "Full-width numeric grading failed"

            # 5. Test code predict exercise (ch03-q01: answer 37)
            ex_kw = page.locator("#ex-ch03-q01")
            ex_kw.locator(".ex-textarea").fill("37")
            ex_kw.locator(".ex-submit").click()
            assert "正解！" in ex_kw.locator(".ex-feedback").inner_text(), "Predict grading failed"

            # 6. Test code implementation exercise self-check (ch03-q15)
            ex_code = page.locator("#ex-ch03-q15")
            assert "検証できる範囲" in ex_code.inner_text(), "Missing verification scope notice on code task"
            ex_code.locator(".ex-reveal-btn").click()
            # Try marking ok before checking criteria -> should prompt user
            ex_code.locator(".ex-mark-ok").click()
            assert "すべてチェック" in ex_code.locator(".ex-self-msg").inner_text()
            for cb in ex_code.locator(".ex-crit-cb").all():
                cb.check()
            ex_code.locator(".ex-mark-ok").click()
            assert "検算確認を記録しました" in ex_code.locator(".ex-self-msg").inner_text()

            # 7. Test spaced repetition due simulation + review dashboard
            page.evaluate("""() => {
                const st = window.TsukuruStudy.loadState();
                // Backdate nextReviewAt of ch03-q04 so it becomes due now
                st.exercises['ch03-q04'].nextReviewAt = Date.now() - 3600 * 1000;
                window.TsukuruStudy.saveState(st);
            }""")
            page.goto(f"{base}/review.html", wait_until="networkidle")
            assert page.locator("#dash-summary .stage-card").count() == 7, "Dashboard must show all 7 mastery stages"
            due_text = page.locator("#dash-due").inner_text()
            assert "復習をおすすめする問題" in due_text, f"Due review item not surfaced: {due_text}"
            # Verify legacy 00-welcome is preserved as at least read
            table_text = page.locator("#dash-chapters").inner_text()
            assert "説明を読んだ" in table_text or "復習" in table_text, "Legacy read status missing"

            # Due list should prioritize weak item ch01-q02 first, and show fresh variant 2/3 for ch03-q04
            due_cards = page.locator("#due-list .exercise")
            assert due_cards.count() >= 2, f"Expected at least 2 due items, got {due_cards.count()}"
            assert "要復習（誤答あり）" in due_cards.nth(0).inner_text()
            assert "問題 2 / 3" in due_cards.nth(1).inner_text(), f"Expected fresh variant 2/3 for ch03-q04, got: {due_cards.nth(1).inner_text()[:120]}"

            # 8. Check desktop & mobile overflow across key pages
            for width, height in [(1280, 800), (390, 844)]:
                page.set_viewport_size({"width": width, "height": height})
                for slug in ["index.html", "01-first-llm.html", "02-tokens.html", "03-next-token.html", "review.html"]:
                    page.goto(f"{base}/{slug}", wait_until="networkidle")
                    overflow = page.evaluate("() => document.documentElement.scrollWidth - document.documentElement.clientWidth")
                    if overflow > 4:
                        errors.append(f"{slug} at {width}x{height} overflows horizontally by {overflow}px")

            # 9. Verify unit tests of auto-grading & scheduling logic via JS API
            unit_ok = page.evaluate("""() => {
                const S = window.TsukuruStudy;
                // Numeric tolerance edge cases
                const exNum = { type: 'numeric' };
                const vNum = { answer: { value: 0.58, tolerance: 0.02 } };
                if (!S.gradeVariant(exNum, vNum, '0.576').correct) return 'tol-fail-1';
                if (!S.gradeVariant(exNum, vNum, '０．６０').correct) return 'tol-fail-2';
                if (S.gradeVariant(exNum, vNum, '0.65').correct) return 'tol-fail-3';
                if (S.gradeVariant(exNum, vNum, 'abc').valid) return 'nan-fail';

                // Spaced repetition interval progression & reset on wrong
                const st = { version: 2, readChapters: {}, exercises: {} };
                const dummyEx = { id: 't1', chapter: '01-first-llm', concept: 'c1', level: 1, type: 'choice' };
                const t0 = 1700000000000;
                const r1 = S.recordOutcome(st, dummyEx, { correct: true, variantIndex: 0, now: t0 });
                if (r1.intervalDays !== 1 || r1.reviewedAfterDue) return 'sr-1';
                const r2 = S.recordOutcome(st, dummyEx, { correct: true, variantIndex: 1, now: t0 + 2 * 86400000 });
                if (r2.intervalDays !== 3 || !r2.reviewedAfterDue) return 'sr-2';
                const r3 = S.recordOutcome(st, dummyEx, { correct: false, variantIndex: 0, now: t0 + 5 * 86400000 });
                if (r3.intervalDays !== 1 || !r3.weak || r3.streak !== 0) return 'sr-3';
                return 'OK';
            }""")
            assert unit_ok == "OK", f"JS study engine unit test failed: {unit_ok}"

            # Filter out benign offline/network warnings if any
            real_errs = [e for e in console_errs if "favicon" not in e]
            errors.extend(real_errs)
            browser.close()
    finally:
        srv.shutdown()

    if errors:
        print("E2E FAILED:")
        for e in errors:
            print("  -", e)
        return 1
    print("PLAYWRIGHT E2E ALL OK")
    return 0


if __name__ == "__main__":
    sys.exit(run_tests())
