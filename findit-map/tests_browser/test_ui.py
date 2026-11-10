"""Browser tests for the Find It page (Playwright, real Chrome or Chromium).

    pip install -r requirements-dev.txt
    python -m unittest discover -s tests_browser -t .          # uses installed Google Chrome
    FINDIT_BROWSER=chromium python -m unittest ...              # after `playwright install chromium`
    FINDIT_PAGE=site/index.html python -m unittest ...          # test your own build instead of the demo
    FINDIT_URL=https://tonyshu114514.github.io/hackathon-project/findit-map/demo/index.html python -m unittest ...
                                                                # test a deployed copy (the file:// test still uses PAGE)

The page is served from a local HTTP server started by the tests (and once from file://). Map tiles are answered with a
1x1 PNG so results never depend on tile servers; one test blocks the default basemap on purpose to check the fallback.
Leaflet itself loads from cdnjs, so the machine needs internet access. Skipped when Playwright is not installed.
"""
import base64
import functools
import http.server
import json
import os
import pathlib
import threading
import time
import unittest

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover - optional dev dependency
    sync_playwright = None

ROOT = pathlib.Path(__file__).resolve().parents[1]
PAGE = os.environ.get("FINDIT_PAGE", "demo/index.html")
URL = os.environ.get("FINDIT_URL")  # a deployed page to test instead of the local server
BROWSER = os.environ.get("FINDIT_BROWSER", "chrome")  # "chrome" = installed Google Chrome; "chromium" = Playwright's
PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")
TILE_HOSTS = ("basemap.nationalmap.gov", "server.arcgisonline.com", "tile.openstreetmap.org")


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


@unittest.skipIf(sync_playwright is None, "Playwright is not installed (pip install -r requirements-dev.txt)")
class FindItBrowser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (ROOT / PAGE).exists():
            raise unittest.SkipTest(f"{PAGE} not found; run build.py or set FINDIT_PAGE")
        cls.httpd = None
        if URL:
            cls.url = URL
        else:
            handler = functools.partial(_Quiet, directory=str(ROOT))
            cls.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
            threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()
            cls.url = f"http://127.0.0.1:{cls.httpd.server_address[1]}/{PAGE}"
        cls.pw = sync_playwright().start()
        try:
            cls.browser = cls.pw.chromium.launch(channel="chrome" if BROWSER == "chrome" else None, headless=True)
        except Exception as e:  # pragma: no cover - environment without a browser
            cls.pw.stop()
            if cls.httpd:
                cls.httpd.shutdown()
            raise unittest.SkipTest(f"no browser available ({e}); install Chrome or run `playwright install chromium`")

    @classmethod
    def tearDownClass(cls):
        cls.browser.close(); cls.pw.stop()
        if cls.httpd:
            cls.httpd.shutdown()

    # ------------------------------------------------------------------ helpers
    def open(self, url=None, width=1440, height=900, block=(), context=None, scheme="dark"):
        ctx = context or self.browser.new_context(viewport={"width": width, "height": height}, color_scheme=scheme,
                                                   accept_downloads=True)
        if context is None:
            self.addCleanup(ctx.close)
        errors = []

        def tiles(route):
            host = route.request.url.split("/")[2]
            if any(h in host for h in block):
                route.abort()
            else:
                route.fulfill(status=200, content_type="image/png", body=PNG)
        for h in TILE_HOSTS:
            ctx.route(f"https://{h}/**", tiles)
        page = ctx.new_page()
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.goto(url or self.url)
        page.wait_for_function("() => document.querySelectorAll('#top10 > li[data-id]').length > 0", timeout=20000)
        page.wait_for_timeout(300)
        return page, errors

    def overlaps(self, page):
        """Pairs of visible floating controls on the map (or the panels' own buttons) whose boxes overlap."""
        return page.evaluate("""() => {
          const sel = ['.leaflet-control-zoom', '.leaflet-control-layers', '.leaflet-top .leaflet-bar:not(.leaflet-control-zoom)',
                       '#bmStatus', '#maptools .pill', '#maptools .btn', '#sideOpenWrap', '#detailOpenWrap', '.legend', '#compareBar',
                       '.leaflet-control-attribution'];
          const els = sel.flatMap(s => [...document.querySelectorAll(s)]).filter(e => {
            const r = e.getBoundingClientRect(), cs = getComputedStyle(e);
            return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none' && !e.closest('[hidden]');
          });
          const out = [];
          for (let i = 0; i < els.length; i++) for (let j = i + 1; j < els.length; j++) {
            const a = els[i], b = els[j]; if (a.contains(b) || b.contains(a)) continue;
            const r = a.getBoundingClientRect(), q = b.getBoundingClientRect();
            const w = Math.min(r.right, q.right) - Math.max(r.left, q.left), h = Math.min(r.bottom, q.bottom) - Math.max(r.top, q.top);
            if (w > 2 && h > 2) out.push([a.id || a.className, b.id || b.className]);
          }
          return out;
        }""")

    # ------------------------------------------------------------------ page and map
    def test_page_loads_with_sites_basemap_and_no_errors(self):
        page, errors = self.open()
        r = page.evaluate("""() => ({cards: document.querySelectorAll('#top10 > li[data-id]').length,
          kpis: document.querySelectorAll('#stats .kpi').length, basemap: basemapName(),
          options: Object.keys(BASEMAPS), polys: Object.keys(byId).length,
          tiles: document.querySelectorAll('.leaflet-tile-pane img').length,
          attribution: document.querySelector('.leaflet-control-attribution').textContent})""")
        self.assertEqual(r["cards"], 10)
        self.assertEqual(r["kpis"], 4)
        self.assertGreater(r["polys"], 100)
        self.assertEqual(r["basemap"], "USGS Topo")
        self.assertIn("USGS", r["attribution"])
        self.assertGreater(r["tiles"], 0)
        self.assertIn("OpenStreetMap", r["options"])  # served over http: offered, not default
        self.assertEqual(errors, [])

    def test_basemap_falls_back_when_default_tiles_fail(self):
        page, _ = self.open(block=("basemap.nationalmap.gov",))
        page.wait_for_function("() => basemapName() !== 'USGS Topo'", timeout=10000)
        r = page.evaluate("() => ({name: basemapName(), pill: document.getElementById('bmStatus').textContent})")
        self.assertEqual(r["name"], "Esri streets")
        self.assertIn("fallback", r["pill"])

    def test_file_url_omits_openstreetmap(self):
        ctx = self.browser.new_context(viewport={"width": 1280, "height": 800})
        self.addCleanup(ctx.close)
        page, errors = self.open(url=(ROOT / PAGE).as_uri(), context=ctx)
        opts = page.evaluate("() => Object.keys(BASEMAPS)")
        self.assertNotIn("OpenStreetMap", opts)  # no Referer from file://, so OSM would serve "Access blocked" tiles
        self.assertEqual(page.evaluate("() => basemapName()"), "USGS Topo")
        self.assertEqual(errors, [])

    # ------------------------------------------------------------------ cities and filters
    def test_city_selection_changes_the_ranking(self):
        page, _ = self.open()
        page.click("#cityBtn")
        page.click("#cityNone")
        first = page.evaluate("() => CITY_ORDER[1]")
        page.check(f"#cityList input[value='{first}']")
        page.click("#cityDone")
        r = page.evaluate(f"""() => ({{sites: +document.querySelector('#stats .kpi b').textContent,
          expected: DATA.cities['{first}'].sites.length,
          cities: [...new Set([...document.querySelectorAll('#top10 > li[data-id]')].map(li => slugOf[li.dataset.id]))]}})""")
        self.assertEqual(r["sites"], r["expected"])
        self.assertEqual(r["cities"], [first])

    def test_quick_filter_pill_and_reset(self):
        page, _ = self.open()
        total = page.evaluate("() => +document.querySelector('#stats .kpi b').textContent")
        page.click(".qchip[data-q=nohazard]")
        shown = page.evaluate("() => +document.querySelector('#stats .kpi b').textContent")
        self.assertLess(shown, total)
        self.assertIn("of", page.inner_text("#fCount"))
        self.assertEqual(page.get_attribute(".qchip[data-q=nohazard]", "aria-pressed"), "true")
        page.click("#maptools [data-clear=all]")
        self.assertEqual(page.evaluate("() => +document.querySelector('#stats .kpi b').textContent"), total)

    def test_no_reported_activity_wording(self):
        page, _ = self.open()
        text = page.evaluate("() => document.getElementById('side').innerText + document.getElementById('legend').innerText")
        self.assertIn("no reported activity", text.lower())
        self.assertNotRegex(text, r"\bAvailable\b")

    # ------------------------------------------------------------------ site detail, compare, reports, exports
    def test_site_detail_tabs_and_provisional_rating(self):
        page, _ = self.open()
        page.click("#top10 > li:nth-child(1) .head")
        for tab in ("overview", "score", "pathways", "risks", "checklist", "report"):
            page.click(f"#dtabs [data-tab={tab}]")
            self.assertTrue(page.is_visible(f"#dbody .tabpanel[data-tab={tab}]"), tab)
        self.assertIn("status", page.inner_text("#siteHero").lower())
        # A site with no listed capacity is rated "provisional", and the Score tab names the gap.
        sid = page.evaluate("""() => { for (const k of CITY_ORDER) { const s = DATA.cities[k].sites.find(x => !likelyUsed(x) && x.lower == null);
          if (s) return s.id; } return null; }""")
        if sid is not None:
            page.evaluate("id => openSiteAnywhere(id)", sid)
            page.click("#dtabs [data-tab=score]")
            self.assertIn("not scored", page.inner_text("#dbody .tabpanel.on"))
            self.assertIn("Provisional", page.inner_text("#siteHero"))

    def test_compare_two_sites(self):
        page, _ = self.open()
        for n in (1, 2):
            page.click(f"#top10 > li:nth-child({n}) .head")
            page.click("#siteHero .cmp-toggle")
            page.click("#detailBack")
        page.click("#cmpTop")
        self.assertTrue(page.is_visible("#compareModal"))
        self.assertGreater(page.locator("#cmpTable tbody tr").count(), 10)
        page.click("#cmpClose")

    def test_site_report_opens(self):
        page, _ = self.open()
        page.click("#top10 > li:nth-child(1) .head")
        with page.context.expect_page() as pop:
            page.click("#siteHero .rep-open")
        report = pop.value
        report.wait_for_load_state()
        self.assertIn("Find It site report", report.title())
        self.assertIn("Prototype for screening only", report.inner_text("body"))

    def test_csv_export(self):
        page, _ = self.open()
        with page.expect_download() as dl:
            page.click("#exportCsv")
        text = pathlib.Path(dl.value.path()).read_text(encoding="utf-8-sig").splitlines()
        cols = text[1].split(",")
        for c in ("status", "rating_provisional", "missing_score_terms", "data_confidence"):
            self.assertIn(c, cols)
        self.assertEqual(len(text) - 2, page.evaluate("() => +document.querySelector('#stats .kpi b').textContent"))

    # ------------------------------------------------------------------ shortlist and checklist
    def test_shortlist_persists_and_shares(self):
        page, _ = self.open()
        page.click("#top10 > li:nth-child(1) .save-btn")
        page.click("#top10 > li:nth-child(2) .save-btn")
        self.assertEqual(page.inner_text("#slCount"), "2")
        page.reload()
        page.wait_for_function("() => document.querySelectorAll('#top10 > li[data-id]').length > 0")
        self.assertEqual(page.inner_text("#slCount"), "2")
        link = page.evaluate("() => shareLink()")
        page.click("#listTabs [data-view=saved]")
        self.assertEqual(page.locator("#slList > li[data-id]").count(), 2)
        with page.expect_download() as dl:
            page.click("#slCsv")
        rows = pathlib.Path(dl.value.path()).read_text(encoding="utf-8-sig").splitlines()
        self.assertIn("your_checklist_done", rows[1])
        self.assertEqual(len(rows) - 2, 2)
        # A colleague with an empty browser opens the link.
        other, _ = self.open(url=link)
        self.assertTrue(other.is_visible("#slShared"))
        self.assertIn("2 sites", other.inner_text("#slShared"))
        other.click("#slAcceptShared")
        self.assertEqual(other.inner_text("#slCount"), "2")

    def test_checklist_persists_and_is_labelled_as_user_input(self):
        page, _ = self.open()
        page.click("#top10 > li:nth-child(3) .head")
        page.click("#dtabs [data-tab=checklist]")
        page.select_option("#dbody [data-dd=owner]", "done")
        page.select_option("#dbody [data-dd=utilities]", "issue")
        page.click("#dbody .ck-item:has([data-dd-note=agency]) summary")
        page.fill("#dbody [data-dd-note=agency]", "Called the planning counter")
        page.wait_for_timeout(500)
        self.assertIn("1 of", page.inner_text("#dbody .ck-head"))
        self.assertIn("Public data", page.inner_text("#dbody"))
        sid = page.evaluate("() => currentId")
        page.reload()
        page.wait_for_function("() => document.querySelectorAll('#top10 > li[data-id]').length > 0")
        page.evaluate("id => openSiteAnywhere(id)", sid)
        page.click("#dtabs [data-tab=checklist]")
        self.assertEqual(page.input_value("#dbody [data-dd=owner]"), "done")
        self.assertEqual(page.input_value("#dbody [data-dd=utilities]"), "issue")
        self.assertEqual(page.input_value("#dbody [data-dd-note=agency]"), "Called the planning counter")
        self.assertIn("entered by you", page.evaluate("id => reportHtml(siteById(id))", sid))
        self.assertEqual(page.inner_text("#slCount"), "1")  # starting a checklist saves the site

    def test_backup_file_round_trip(self):
        page, _ = self.open()
        page.click("#top10 > li:nth-child(1) .save-btn")
        backup = page.evaluate("() => backupJson()")
        self.assertEqual(json.loads(backup)["format"], "findit-shortlist")
        fresh, _ = self.open()
        fresh.click("#listTabs [data-view=saved]")
        fresh.set_input_files("#slImport", files=[{"name": "b.json", "mimeType": "application/json", "buffer": backup.encode()}])
        fresh.wait_for_function("() => document.getElementById('slCount').textContent === '1'")

    # ------------------------------------------------------------------ layout
    def test_no_overlapping_controls_in_any_panel_state(self):
        for w, h in ((1440, 900), (1280, 640), (1024, 700)):
            page, _ = self.open(width=w, height=h)
            for side, detail in ((True, True), (False, True), (True, False), (False, False)):
                page.evaluate(f"() => {{ setSide({str(side).lower()}); setDetail({str(detail).lower()}); }}")
                page.wait_for_timeout(350)
                self.assertEqual(self.overlaps(page), [], f"{w}x{h} side={side} detail={detail}")
                self.assertLessEqual(page.evaluate("() => document.documentElement.scrollWidth"), w)
            page.click("#discBtn")
            r = page.evaluate("""() => { const x = document.getElementById('discClose').getBoundingClientRect(),
              l = document.querySelector('#discModal .lead').getBoundingClientRect(); return x.bottom <= l.top; }""")
            self.assertTrue(r, f"disclosures close button overlaps the disclaimer at {w}x{h}")
            page.context.close()

    def test_mobile_drawer_sheet_and_detail(self):
        page, errors = self.open(width=390, height=844)
        self.assertEqual(self.overlaps(page), [])
        page.click("#menuBtn")
        page.wait_for_timeout(300)
        box = page.evaluate("() => document.getElementById('side').getBoundingClientRect().toJSON()")
        self.assertGreaterEqual(box["left"], 0)
        self.assertLessEqual(box["right"], 390)
        page.click("#scrim", position={"x": 375, "y": 400})  # the visible strip beside the drawer
        page.wait_for_timeout(300)
        page.evaluate("() => document.getElementById('shell').classList.add('sheet-open')")
        page.click("#top10 > li:nth-child(1) .head")
        page.wait_for_timeout(300)
        self.assertTrue(page.is_visible("#siteHero"))
        self.assertLessEqual(page.evaluate("() => document.documentElement.scrollWidth"), 390)
        page.click("#dtabs [data-tab=checklist]")
        self.assertTrue(page.is_visible("#dbody .ck-list"))
        self.assertEqual(errors, [])

    # ------------------------------------------------------------------ performance
    def test_load_and_redraw_performance(self):
        page, _ = self.open()
        r = page.evaluate("""() => { const nav = performance.getEntriesByType('navigation')[0];
          const t0 = performance.now(); draw(); const one = performance.now() - t0;
          return {dcl: nav.domContentLoadedEventEnd, redraw: one}; }""")
        # Generous ceilings: the point is to catch regressions (seconds), not to benchmark.
        self.assertLess(r["dcl"], 5000, r)
        self.assertLess(r["redraw"], 1500, r)


if __name__ == "__main__":
    unittest.main()
