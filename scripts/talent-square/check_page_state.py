"""
Page State Diagnostic Script for 微信小店达人广场

Quickly checks the current page structure and reports key findings.
Use this FIRST when the page doesn't behave as expected (e.g., no data loaded,
old selectors failing, pagination missing).

Usage:
    python3 check_page_state.py

Run from any directory. Outputs structured JSON with page state.
"""
import asyncio, json, sys
from playwright.async_api import async_playwright

STATE_PATH = "/tmp/weixin_store_state.json"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(storage_state=STATE_PATH, viewport={"width":1920,"height":1080})
        page = await ctx.new_page()
        await page.goto("https://store.weixin.qq.com/shop/findersquare/find",
                         wait_until="domcontentloaded", timeout=30_000)
        await asyncio.sleep(8)

        sr = "document.querySelector('micro-app')?.shadowRoot"

        report = {}

        # 1. Session check
        body = await page.text_content("body") or ""
        report["session_expired"] = "登录" in body and "扫码" in body

        # 2. Shadow DOM existence
        sr_exists = await page.evaluate(f"!!({sr})")
        report["shadow_dom_exists"] = sr_exists

        if not sr_exists:
            report["error"] = "No micro-app shadow DOM found"
            print(json.dumps(report, ensure_ascii=False, indent=2))
            await browser.close()
            return

        # 3. Check for table structure (old format)
        has_table = await page.evaluate(f"""
            !!({sr}.querySelector('table'))
        """)
        report["has_table_structure"] = has_table

        # 4. Check for card grid structure (new format)
        has_grid = await page.evaluate(f"""
            !!({sr}.querySelector('[class*="grid"][class*="grid-cols"]'))
        """)
        report["has_card_grid"] = has_grid

        # 5. Check for pagination (old format)
        has_pagination = await page.evaluate(f"""
            !!({sr}.querySelector('[class*="pagination"]'))
        """)
        report["has_pagination"] = has_pagination

        # 6. Check checkbox visibility
        checkbox_data = await page.evaluate(f"""() => {{
            const sr = {sr};
            const catLabel = sr.querySelector('.hide-cate');
            if (!catLabel) return {{hide_cate_exists: false}};
            const style = getComputedStyle(catLabel);
            return {{
                hide_cate_exists: true,
                display: style.display,
                visibility: style.visibility,
                checkbox_count: catLabel.querySelectorAll('input[type=checkbox]').length
            }};
        }}""")
        report["checkbox_visibility"] = checkbox_data

        # 7. Data rows count
        data = await page.evaluate(f"""() => {{
            const sr = {sr};
            const trs = sr.querySelectorAll('tr');
            const dataRows = Array.from(trs).filter(tr => {{
                const t = tr.textContent.trim();
                return t && !t.includes('达人昵称') && tr.querySelectorAll('td').length >= 3;
            }});
            const grids = sr.querySelectorAll('[class*="grid"]');
            const cardCounts = Array.from(grids).map(g => g.children.length);
            const cards = sr.querySelectorAll('[class*="cursor-pointer"]');
            const talentCards = Array.from(cards).filter(c => c.querySelector('img') && c.textContent.length > 30);
            return {{
                table_data_rows: dataRows.length,
                grids_found: grids.length,
                cards_per_grid: cardCounts,
                talent_cards: talentCards.length,
                sample_card: talentCards.length > 0 ? talentCards[0].textContent.trim().slice(0, 150) : 'none'
            }};
        }}""")
        report["data_state"] = data

        # 8. Tabs
        tabs = await page.evaluate(f"""() => {{
            const sr = {sr};
            const tabLinks = sr.querySelectorAll('.weui-desktop-tab a');
            return Array.from(tabLinks).map(a => a.textContent.trim());
        }}""")
        report["tabs_found"] = tabs

        # 9. Determine page version
        if report["has_table_structure"]:
            report["page_version"] = "old (table-based)"
        elif report["has_card_grid"] and not report["has_table_structure"]:
            report["page_version"] = "new (card grid)"
        else:
            report["page_version"] = "unknown"

        report["verdict"] = (
            "PAGE REDESIGNED — old scraper will not work" if report.get("page_version") == "new (card grid)"
            else "PAGE LOOKS OK (old structure)" if report.get("page_version") == "old (table-based)"
            else "UNRECOGNIZED STRUCTURE — manual investigation needed"
        )

        print(json.dumps(report, ensure_ascii=False, indent=2))

        await browser.close()

asyncio.run(main())
