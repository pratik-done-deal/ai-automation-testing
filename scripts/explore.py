"""Walk the live app as a role and capture what is on screen. Read-only.

The prd-analyzer and test-case-generator agents use this to learn how the platform behaves
*today*, before a feature exists in code. It asserts nothing and changes no test data: it
navigates, clicks to open things, and writes down what it saw.

    python scripts/explore.py buyer /buyer/browse
    python scripts/explore.py buyer /buyer/browse --click "View Listing" --name cue-card
    python scripts/explore.py seller /deals --out /tmp/walk --headed

For each capture it writes <out>/<name>.png and <out>/<name>.txt (url, title, visible text,
visible CTAs, and the API calls the screen made). Default --out is reports/explore/.

Never use it to submit a form or accept an interest: that consumes real test data. Open, read,
screenshot, and stop. Use --headed when you want to watch it.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from playwright.sync_api import sync_playwright  # noqa: E402

from config import settings  # noqa: E402
from utils.sessions import LOGIN_PATHS, STATE_BY_ROLE, VIEWPORT  # noqa: E402

CTA_SELECTOR = "button, a, [role=button], [class*=cta], [class*=btn]"


def capture(page, out_dir, name, requests):
    """Write a png plus a text dump of everything readable on the current page."""
    out_dir.mkdir(parents=True, exist_ok=True)
    page.wait_for_timeout(1200)  # let the last fetch paint
    png = out_dir / f"{name}.png"
    page.screenshot(path=str(png), full_page=True)

    ctas = []
    for el in page.locator(CTA_SELECTOR).all():
        try:
            if el.is_visible():
                text = " ".join(el.inner_text().split())
                if text and text not in ctas:
                    ctas.append(text)
        except Exception:
            continue  # detached during a re-render

    body = " ".join(page.locator("body").inner_text().split("\n"))
    lines = [
        f"# {name}",
        f"url:   {page.url}",
        f"title: {page.title()}",
        "",
        "## visible CTAs",
        *(f"- {c}" for c in ctas[:60]),
        "",
        "## API calls this screen made",
        *(f"- {r}" for r in sorted(set(requests))),
        "",
        "## visible text",
        body,
    ]
    (out_dir / f"{name}.txt").write_text("\n".join(lines), encoding="utf-8")
    print(f"{name}: {png}  +  {out_dir / f'{name}.txt'}  ({len(ctas)} CTAs, {len(set(requests))} API calls)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("role", choices=sorted(STATE_BY_ROLE), help="which saved session to use")
    ap.add_argument("path", help="app path, e.g. /buyer/browse (no session needed for login screens)")
    ap.add_argument("--click", action="append", default=[],
                    help="visible text to click after landing; repeatable, captured after each")
    ap.add_argument("--name", default="", help="base name for the capture files (default: from the path)")
    ap.add_argument("--out", default="", help="output directory (default: reports/explore)")
    ap.add_argument("--anon", action="store_true", help="ignore the saved session (logged-out screens)")
    ap.add_argument("--headed", action="store_true", help="show the browser")
    args = ap.parse_args()

    state = STATE_BY_ROLE[args.role]
    if not args.anon and not state.exists():
        sys.exit(f"No saved {args.role} session at {state}.\n"
                 f"Run: python scripts/save_auth_state.py {args.role}\n"
                 f"(or pass --anon for logged-out screens like /{LOGIN_PATHS[args.role]})")

    out = Path(args.out) if args.out else Path(__file__).resolve().parents[1] / "reports" / "explore"
    base = args.name or (args.path.strip("/").replace("/", "-") or "home")
    url = settings.app_url + args.path.lstrip("/")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not args.headed)
        ctx = browser.new_context(viewport=VIEWPORT,
                                  **({} if args.anon else {"storage_state": str(state)}))
        page = ctx.new_page()
        requests = []
        page.on("request", lambda r: requests.append(f"{r.method} {r.url.split('/v1/')[-1]}")
                if "/api/" in r.url else None)

        print(f"-> {url} as {'anonymous' if args.anon else args.role}")
        page.goto(url, wait_until="domcontentloaded")
        capture(page, out, base, requests)

        for i, text in enumerate(args.click, start=1):
            requests.clear()
            target = page.get_by_text(text, exact=False).first
            try:
                # many CTAs here open a new tab (target="_blank")
                with ctx.expect_page(timeout=4000) as popup:
                    target.click()
                page = popup.value
                page.wait_for_load_state("domcontentloaded")
                page.on("request", lambda r: requests.append(f"{r.method} {r.url.split('/v1/')[-1]}")
                        if "/api/" in r.url else None)
                print(f"-> clicked {text!r}, opened a new tab")
            except Exception:
                print(f"-> clicked {text!r} in place")
            capture(page, out, f"{base}-{i}-{text.lower().replace(' ', '-')[:30]}", requests)

        ctx.close()
        browser.close()


if __name__ == "__main__":
    main()
