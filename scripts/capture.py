"""Capture screenshots and a screen recording of the real app (headless Chromium).

Usage: python capture.py DIST_HTML OUT_DIR UPLOAD_JSON
"""
import asyncio, json, sys
from pathlib import Path
from playwright.async_api import async_playwright

html, out, upload = Path(sys.argv[1]).resolve(), Path(sys.argv[2]), Path(sys.argv[3]).resolve()
out.mkdir(parents=True, exist_ok=True)
URL = html.as_uri()


async def shot(pg, name, selector=None, clip=None):
    await pg.wait_for_timeout(400)
    if selector:
        await pg.locator(selector).first.screenshot(path=str(out / name))
    else:
        await pg.screenshot(path=str(out / name), clip=clip)


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=2)
        errors = []
        pg.on("pageerror", lambda e: errors.append(str(e)))
        await pg.goto(URL); await pg.wait_for_timeout(600)
        await shot(pg, "01_home.png", clip=dict(x=0, y=0, width=1440, height=900))
        await shot(pg, "02_case_svalbard.png", "#case")
        await shot(pg, "03_ledger_svalbard.png", ".lower")
        log = {}
        for i, j, name in [(1, 1, "04_demo2_amazon"), (2, 1, "05_demo3_delhi"), (3, 1, "06_demo4_sfbay")]:
            await pg.evaluate(f"TDApp.playDemo({i},{j})"); await pg.wait_for_timeout(500)
            await shot(pg, name + "_case.png", "#case")
            await shot(pg, name + "_ledger.png", ".lower")
            await shot(pg, name + "_tour.png", "#tour")
            log[name] = await pg.evaluate("({status: window.__lastResult.status, slope: window.__lastResult.res.slopeDecade, verdict: window.__lastResult.res.verdict})")
        await pg.evaluate("document.getElementById('tour-close').click(); TDApp.select({region:'svalbard', variable:'T2M', mode:'anom', custom:null})")
        await shot(pg, "07_matrix.png", ".lower > .panel:nth-child(2)")
        await shot(pg, "08_demos.png", "section.panel:has(#demos)")
        # Bring-your-own-data: load the freshly downloaded NASA POWER file through the real file input
        await pg.set_input_files("#b-file", str(upload)); await pg.wait_for_timeout(800)
        log["upload"] = await pg.evaluate("({msg: document.getElementById('b-msg').textContent, slope: window.__lastResult.res.slopeDecade, verdict: window.__lastResult.res.verdict, p: window.__lastResult.res.pTtest})")
        await shot(pg, "09_upload_case.png", "#case")
        await shot(pg, "10_upload_form.png", "section.panel:has(#drop)")
        await shot(pg, "11_graph_methods.png", ".bottom")
        await pg.screenshot(path=str(out / "00_full_page.png"), full_page=True)
        # mobile check
        m = await b.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=2)
        await m.goto(URL); await m.wait_for_timeout(500)
        await m.screenshot(path=str(out / "12_mobile.png"))
        sw = await m.evaluate("document.documentElement.scrollWidth")
        log["mobile_scrollWidth"] = sw
        # dark theme
        d = await b.new_page(viewport={"width": 1440, "height": 900}, color_scheme="dark", device_scale_factor=1)
        await d.goto(URL); await d.wait_for_timeout(500)
        await d.locator("#case").screenshot(path=str(out / "13_dark_case.png"))
        log["errors"] = errors
        (out / "capture_log.json").write_text(json.dumps(log, indent=1))
        print(json.dumps(log, indent=1))
        # screen recording of a guided demonstration
        ctx = await b.new_context(viewport={"width": 1280, "height": 800}, record_video_dir=str(out / "video"), record_video_size={"width": 1280, "height": 800})
        v = await ctx.new_page(); await v.goto(URL); await v.wait_for_timeout(1500)
        await v.locator(".demo").nth(1).click(); await v.wait_for_timeout(3500)
        for _ in range(2):
            await v.click("#tour-next"); await v.wait_for_timeout(3500)
        await v.click("#tour-next"); await v.wait_for_timeout(500)
        await v.locator(".demo").nth(2).click(); await v.wait_for_timeout(3500)
        for _ in range(2):
            await v.click("#tour-next"); await v.wait_for_timeout(3500)
        await v.click("#tour-next")
        await v.locator("#matrix").scroll_into_view_if_needed(); await v.wait_for_timeout(2000)
        await ctx.close()
        await b.close()


asyncio.run(main())
