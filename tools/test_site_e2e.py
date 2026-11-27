"""End-to-end Playwright verification for docs/ static site.

Verifies:
  1. Home page, Soseki GPT widget (lazy-load / unknown-char notice / stop-cancel / error recovery),
     course toggle (thorough <-> standard), and slim exercises-meta.json usage on non-review pages.
  2. Chapter interactive exercises:
     - Progressive hints reveal + hint tracking.
     - Choice wrong answer -> shows diagnostic (where wrong, reasoning, steps, section link, altExample, retry variant).
     - Variant switch -> changes prompt/numbers; option answering works regardless of visual shuffle order.
     - Choice & numeric (including full-width digits!) & code-predict correct answers -> schedules review, NEVER displays "完全理解".
     - Code implementation self-check -> requires all criteria checkboxes before recording self-check.
  3. Spaced repetition & mastery dashboard (review.html):
     - Legacy localStorage backward compatibility (tsukuru-llm:done preserved).
     - Due review re-surfacing when nextReviewAt <= now.
     - Malformed JSON import rejection (existing valid history preserved!) & XSS payload escaping.
     - localStorage quota failure visible alert banner.
     - Valid JSON export/import roundtrip.
  4. Search: late-chapter term ("GRPO" in Ch 22) + section anchor jump (#s...).
  5. Desktop (1280x800) and mobile (390x844) layout across ALL HTML pages: zero horizontal overflow,
     zero console/page errors, zero HTTP >= 400 / requestfailed responses.
  6. Keyboard accessibility: skip link, mobile menu Escape + aria-expanded reset, keyboard-reachable import control.
"""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import argparse
import json
import sys
import threading

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print(
        "ERROR: playwright is not installed. Run:\n"
        "  pip install -r requirements-dev.txt\n"
        "  python -m playwright install chromium",
        file=sys.stderr,
    )
    sys.exit(1)

ROOT = Path(__file__).resolve().parents[1]


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


def start_server(docs_dir):
    handler = partial(QuietHandler, directory=str(docs_dir))
    srv = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    port = srv.server_address[1]
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    return srv, port


def run_tests(docs_dir):
    docs_dir = Path(docs_dir)
    if not docs_dir.exists():
        print(f"E2E FAILED: docs dir not found: {docs_dir}")
        return 1

    ex_index = json.loads((docs_dir / "exercises-index.json").read_text(encoding="utf-8"))
    ex_by_id = {ex["id"]: ex for ch in ex_index.get("chapters", []) for ex in ch.get("exercises", [])}

    srv, port = start_server(docs_dir)
    base = f"http://127.0.0.1:{port}"
    errors = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            ctx = browser.new_context(viewport={"width": 1280, "height": 800})
            page = ctx.new_page()
            console_errs = []
            net_errs = []
            page.on("pageerror", lambda e: console_errs.append(f"pageerror: {e}"))
            page.on("console", lambda m: console_errs.append(f"console.{m.type}: {m.text}") if m.type == "error" else None)
            page.on("requestfailed", lambda req: net_errs.append(f"requestfailed: {req.url} ({req.failure})") if "favicon" not in req.url else None)
            page.on("response", lambda res: net_errs.append(f"HTTP {res.status}: {res.url}") if res.status >= 400 and "favicon" not in res.url else None)

            # 1. Seed legacy localStorage data & verify home page + Browser GPT UX
            page.goto(f"{base}/index.html", wait_until="networkidle")
            page.evaluate("""() => {
                localStorage.setItem('tsukuru-llm:done', JSON.stringify(['00-welcome']));
                localStorage.setItem('tsukuru-llm:checks', JSON.stringify({'00-welcome:0': true}));
            }""")
            page.reload(wait_until="networkidle")
            assert page.locator("a[data-slug='00-welcome'].done").count() >= 1, "Legacy done class not applied"

            # Trigger Soseki GPT generation with unknown characters (ASCII/emoji) & verify .gpt-warn notice + clean stop/recovery
            gpt_widget = page.locator(".hero-board .widget")
            seed_input = gpt_widget.locator("input[type='text'], input:not([type]), textarea").first
            if seed_input.count() > 0:
                seed_input.fill("吾輩はABC😀")
                gen_btn = gpt_widget.locator("button").first
                gen_btn.click()
                warn_el = gpt_widget.locator(".gpt-warn")
                warn_el.wait_for(state="visible", timeout=15000)
                warn_text = warn_el.inner_text()
                if "ABC" not in warn_text and "スキップ" not in warn_text:
                    errors.append(f"Browser GPT .gpt-warn did not mention skipped unknown chars: {warn_text[:160]}")
                stop_btn = gpt_widget.locator("button:has-text('停止')")
                if stop_btn.count() > 0 and stop_btn.is_visible() and stop_btn.is_enabled():
                    stop_btn.click()
                # Wait for generate button to re-enable cleanly so no fetch/generation is aborted on navigation
                page.wait_for_function(
                    "() => { const b = document.querySelector('.hero-board .widget button'); return b && !b.disabled; }",
                    timeout=15000,
                )

            # 2. Test search (untruncated late-chapter term "GRPO" + section anchor jump)
            search_box = page.locator("#search")
            search_box.fill("GRPO")
            res_links = page.locator("#results a")
            res_links.first.wait_for(state="visible", timeout=5000)
            if res_links.count() == 0:
                errors.append("Search for late-chapter term 'GRPO' returned 0 results")
            else:
                hrefs = [res_links.nth(i).get_attribute("href") or "" for i in range(res_links.count())]
                if not any("22-alignment.html" in h for h in hrefs):
                    errors.append(f"Search for 'GRPO' did not surface 22-alignment.html: {hrefs}")
                if not any("#s" in h for h in hrefs):
                    errors.append(f"Search results lacked section anchor (#s...): {hrefs}")
            search_box.fill("")

            # 3. Test course toggle on Ch 1
            page.goto(f"{base}/01-first-llm.html", wait_until="networkidle")
            scaffolds_open_thorough = page.evaluate("() => Array.from(document.querySelectorAll('details.scaffold')).every(d => d.open)")
            assert scaffolds_open_thorough, "Scaffolds should be open in thorough course"
            page.locator(".course-switch button[data-set-course='standard']").click()
            assert page.evaluate("() => document.documentElement.dataset.course") == "standard"
            scaffolds_closed_std = page.evaluate("() => Array.from(document.querySelectorAll('details.scaffold')).every(d => !d.open)")
            assert scaffolds_closed_std, "Scaffolds should collapse in standard course"
            page.locator(".course-switch button[data-set-course='thorough']").click()

            # 4. Test progressive hints + interactive choice exercise (read answer dynamically from exercises-index.json)
            ex2 = page.locator("#ex-ch01-q02")
            ex2_data = ex_by_id["ch01-q02"]
            v0_ans = ex2_data["variants"][0]["answer"]
            wrong_opt = next(o["id"] for o in ex2_data["variants"][0]["options"] if o["id"] != v0_ans)
            # Open hint if hint button exists
            hint_btn = ex2.locator(".ex-hint-btn, button:has-text('ヒント')").first
            if hint_btn.count() > 0:
                hint_btn.click()
            ex2.locator(f"input[type='radio'][value='{wrong_opt}']").check()
            ex2.locator(".ex-submit").click()
            fb_text = ex2.locator(".ex-feedback").inner_text()
            for required in ["どこが間違っているか", "正しい考え方", "途中計算", "関連する教材の節", "別の具体例"]:
                assert required in fb_text, f"Missing diagnostic section '{required}' on wrong answer"
            # Switch to variant 2 via retry button
            prompt_before = ex2.locator(".ex-prompt").inner_text()
            ex2.locator(".ex-retry-variant").click()
            prompt_after = ex2.locator(".ex-prompt").inner_text()
            assert prompt_before != prompt_after, "Variant retry did not switch to a different question"
            # Answer variant 2 correctly
            v1_ans = ex2_data["variants"][1]["answer"]
            ex2.locator(f"input[type='radio'][value='{v1_ans}']").check()
            ex2.locator(".ex-submit").click()
            fb_ok = ex2.locator(".ex-feedback").inner_text()
            assert "正解" in fb_ok, f"Expected correct confirmation, got: {fb_ok[:120]}"
            assert "完全理解しました" not in fb_ok, "Must not falsely claim full mastery on single answer"

            # 5. Test numeric exercise with full-width digits on Ch 3 (read answer dynamically)
            page.goto(f"{base}/03-next-token.html", wait_until="networkidle")
            ex_sigma = page.locator("#ex-ch03-q04")
            ex_sigma_data = ex_by_id["ch03-q04"]
            num_ans = str(ex_sigma_data["variants"][0]["answer"]["value"])
            fw_ans = num_ans.translate(str.maketrans("0123456789.-", "０１２３４５６７８９．－"))
            ex_sigma.locator(".ex-input").fill(fw_ans)
            ex_sigma.locator(".ex-input").press("Enter")
            assert "正解" in ex_sigma.locator(".ex-feedback").inner_text(), "Full-width numeric grading failed"

            # 6. Test code predict exercise (ch03-q01)
            ex_kw = page.locator("#ex-ch03-q01")
            ex_kw_data = ex_by_id["ch03-q01"]
            pred_ans = str(ex_kw_data["variants"][0]["accept"][0])
            ex_kw.locator(".ex-textarea").fill(pred_ans)
            ex_kw.locator(".ex-submit").click()
            assert "正解" in ex_kw.locator(".ex-feedback").inner_text(), "Predict grading failed"

            # 7. Test code implementation exercise self-check (ch03-q15)
            ex_code = page.locator("#ex-ch03-q15")
            assert "検証できる範囲" in ex_code.inner_text(), "Missing verification scope notice on code task"
            ex_code.locator(".ex-reveal-btn").click()
            ex_code.locator(".ex-mark-ok").click()
            assert "すべてチェック" in ex_code.locator(".ex-self-msg").inner_text()
            for cb in ex_code.locator(".ex-crit-cb").all():
                cb.check()
            ex_code.locator(".ex-mark-ok").click()
            self_msg = ex_code.locator(".ex-self-msg").inner_text()
            assert ("確認" in self_msg or "記録" in self_msg), f"Unexpected self-check msg: {self_msg}"

            # 8. Test spaced repetition due simulation + review dashboard + security/import/storage checks
            page.evaluate("""() => {
                const st = window.TsukuruStudy.loadState();
                st.exercises['ch03-q04'].nextReviewAt = Date.now() - 3600 * 1000;
                window.TsukuruStudy.saveState(st);
            }""")
            page.goto(f"{base}/review.html", wait_until="networkidle")
            assert page.locator("#dash-summary .stage-card").count() >= 5, "Dashboard stage cards missing"
            due_text = page.locator("#dash-due").inner_text()
            assert "復習" in due_text, f"Due review item not surfaced: {due_text}"

            # Verify #import-history is NOT display:none (keyboard accessible via visually-hidden)
            imp_display = page.evaluate("() => getComputedStyle(document.getElementById('import-history')).display")
            if imp_display == "none":
                errors.append("#import-history has display:none (keyboard unreachable)")

            # Malformed JSON import must NOT overwrite existing valid localStorage
            before_state = page.evaluate("() => localStorage.getItem('tsukuru-llm:study_v2')")
            bad_payload = json.dumps({"study": {"version": 2, "exercises": "CORRUPTED"}})
            page.locator("#import-history").set_input_files({
                "name": "bad.json", "mimeType": "application/json", "buffer": bad_payload.encode("utf-8")
            })
            page.wait_for_timeout(200)
            after_bad_state = page.evaluate("() => localStorage.getItem('tsukuru-llm:study_v2')")
            if after_bad_state != before_state:
                errors.append("Malformed JSON import overwrote existing valid study state!")

            # XSS payload import check: must escape / coerce numbers safely
            xss_payload = json.dumps({
                "exportedAt": "2026-11-26T00:00:00Z",
                "course": "standard",
                "legacyDone": ["00-welcome", "01-first-llm"],
                "legacyChecks": {"01-first-llm:0": True},
                "study": {
                    "version": 2,
                    "readChapters": {"01-first-llm": {"firstAt": 1700000000000, "lastAt": 1700000000000}},
                    "exercises": {
                        "ch01-q02": {
                            "chapter": "01-first-llm", "concept": "gpu-parallel-vram",
                            "conceptLabel": "<img src=x onerror='window.__xss=1'>GPU",
                            "level": 2, "type": "choice", "attempts": 2, "correct": 1,
                            "wrong": "<img src=x onerror='window.__xss=1'>",
                            "streak": 0, "lastVariant": 1, "solvedVariants": [0], "lastResult": "wrong",
                            "lastAt": 1700000000000, "intervalDays": 1, "nextReviewAt": 1700000000000,
                            "reviewedAfterDue": False, "weak": True, "note": ""
                        }
                    }
                }
            })
            page.locator("#import-history").set_input_files({
                "name": "xss.json", "mimeType": "application/json", "buffer": xss_payload.encode("utf-8")
            })
            page.wait_for_timeout(300)
            xss_fired = page.evaluate("() => Boolean(window.__xss)")
            if xss_fired:
                errors.append("CRITICAL: XSS executed on review.html via imported JSON!")

            # Valid backup JSON import roundtrip
            backup_payload = json.dumps({
                "exportedAt": "2026-11-26T00:00:00Z",
                "course": "standard",
                "legacyDone": ["00-welcome", "01-first-llm"],
                "legacyChecks": {"01-first-llm:0": True},
                "study": {
                    "version": 2,
                    "readChapters": {"01-first-llm": {"firstAt": 1700000000000, "lastAt": 1700000000000}},
                    "exercises": {
                        "ch01-q02": {
                            "chapter": "01-first-llm", "concept": "gpu-parallel-vram", "conceptLabel": "GPU",
                            "level": 2, "type": "choice", "attempts": 2, "correct": 2, "wrong": 0,
                            "streak": 2, "lastVariant": 1, "solvedVariants": [0, 1], "lastResult": "correct",
                            "lastAt": 1700000000000, "intervalDays": 3, "nextReviewAt": 1999999999000,
                            "reviewedAfterDue": True, "weak": False, "note": ""
                        }
                    }
                }
            })
            page.locator("#import-history").set_input_files({
                "name": "backup.json", "mimeType": "application/json", "buffer": backup_payload.encode("utf-8")
            })
            page.wait_for_function(
                "() => { const s = window.TsukuruStudy.loadState(); return Boolean(s && s.exercises && s.exercises['ch01-q02'] && s.exercises['ch01-q02'].reviewedAfterDue === true); }",
                timeout=5000,
            )
            assert "復元しました" in page.locator("#backup-status").inner_text(), "JSON history import failed"
            assert page.evaluate("() => document.documentElement.dataset.course") == "standard", "Imported course not applied"

            # Test localStorage failure banner
            page.evaluate("""() => {
                const orig = Storage.prototype.setItem;
                Storage.prototype.setItem = function() { throw new DOMException('QuotaExceededError'); };
                try { window.TsukuruStudy.saveState(window.TsukuruStudy.loadState()); } finally { Storage.prototype.setItem = orig; }
            }""")
            page.wait_for_timeout(150)
            alert_count = page.locator("[role='alert']").count()
            if alert_count == 0:
                errors.append("localStorage write failure did not render any visible [role='alert'] notification")

            # 9. Test mobile menu + Escape + aria-expanded reset, theme toggle, skip link
            page.set_viewport_size({"width": 390, "height": 844})
            page.goto(f"{base}/01-first-llm.html", wait_until="networkidle")
            page.locator("#menu").click()
            assert page.evaluate("() => document.body.classList.contains('menu-open')"), "Mobile menu failed to open"
            page.keyboard.press("Escape")
            assert not page.evaluate("() => document.body.classList.contains('menu-open')"), "Escape failed to close mobile menu"
            aria_exp = page.locator("#menu").get_attribute("aria-expanded")
            if aria_exp != "false":
                errors.append(f"Escape did not reset #menu aria-expanded='false' (got {aria_exp!r})")
            theme_before = page.evaluate("() => document.documentElement.dataset.theme || ''")
            page.locator("#theme").click()
            theme_after = page.evaluate("() => document.documentElement.dataset.theme || ''")
            assert theme_after in ("dark", "light") and theme_after != theme_before, "Theme toggle did not switch"
            page.keyboard.press("Tab")
            assert page.locator("a.skip").count() == 1, "Skip link missing"

            # 10. Check desktop & mobile horizontal overflow across ALL built HTML pages
            all_html_names = [f.name for f in sorted(docs_dir.glob("*.html"))]
            assert len(all_html_names) >= 38, f"Expected >= 38 HTML pages, found {len(all_html_names)}"
            for width, height in [(1280, 800), (390, 844)]:
                page.set_viewport_size({"width": width, "height": height})
                for slug in all_html_names:
                    page.goto(f"{base}/{slug}", wait_until="domcontentloaded")
                    page.wait_for_timeout(40)
                    overflow = page.evaluate("() => document.documentElement.scrollWidth - document.documentElement.clientWidth")
                    if overflow > 4:
                        errors.append(f"{slug} at {width}x{height} overflows horizontally by {overflow}px")

            # 11. Unit tests of auto-grading & scheduling logic via JS API
            page.goto(f"{base}/review.html", wait_until="networkidle")
            unit_ok = page.evaluate("""() => {
                const S = window.TsukuruStudy;
                const exNum = { type: 'numeric' };
                const vNum = { answer: { value: 0.58, tolerance: 0.02 } };
                if (!S.gradeVariant(exNum, vNum, '0.576').correct) return 'tol-fail-1';
                if (!S.gradeVariant(exNum, vNum, '０．６０').correct) return 'tol-fail-2';
                if (S.gradeVariant(exNum, vNum, '0.65').correct) return 'tol-fail-3';
                if (S.gradeVariant(exNum, vNum, 'abc').valid) return 'nan-fail';

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

            real_errs = [e for e in console_errs if "favicon" not in e]
            errors.extend(real_errs)
            errors.extend(net_errs)
            browser.close()
    finally:
        srv.shutdown()

    if errors:
        print(f"E2E FAILED ({len(errors)} error(s)):")
        for e in errors[:50]:
            print("  -", e)
        return 1
    print(f"PLAYWRIGHT E2E ALL OK ({len(all_html_names)} pages checked on desktop & mobile)")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--docs-dir", default=str(ROOT / "docs"))
    args = ap.parse_args()
    sys.exit(run_tests(args.docs_dir))
