"""Re-apply map_template.html to demo/index.html without changing the demo's data.

The demo is a built page (python build.py) copied to demo/. When only the page code changes (layout, scripts, styles),
run this instead of rebuilding from fresh downloads: it takes the DATA payload already embedded in demo/index.html and
wraps it in the current template with the same substitutions build.py makes. The payload is packed the way build.py
packs it (findit/pack.py: shared text table, index arrays); packing is lossless, so the demo's data does not change.

    python refresh_demo.py            # rewrite demo/index.html in place
    python refresh_demo.py --check    # exit 1 if the demo is not up to date with the template
"""
import json
import pathlib
import sys

from findit.pack import pack_payload

ROOT = pathlib.Path(__file__).parent
DEMO = ROOT / "demo" / "index.html"
PREFIX = "const DATA = "


def render():
    old = DEMO.read_text(encoding="utf-8")
    line = next((l for l in old.splitlines() if l.startswith(PREFIX)), None)
    if line is None:
        raise SystemExit("demo/index.html has no embedded DATA line; rebuild it with build.py and copy site/index.html.")
    payload = line[len(PREFIX):].rstrip()
    if not payload.endswith(";"):
        raise SystemExit("unexpected DATA line ending in demo/index.html")
    page = (ROOT / "map_template.html").read_text(encoding="utf-8")
    page = page.replace("/*__LEAFLET_CSS__*/", (ROOT / "findit" / "leaflet.css").read_text(encoding="utf-8"))
    if "/*__DATA__*/null" not in page:
        raise SystemExit("map_template.html has no /*__DATA__*/null placeholder")
    data = pack_payload(json.loads(payload[:-1].replace("<\\/", "</")))
    return old, page.replace("/*__DATA__*/null", json.dumps(data, separators=(",", ":")).replace("</", "<\\/"))


def main():
    old, new = render()
    if "--check" in sys.argv:
        print("demo is up to date" if old == new else "demo is out of date: run python refresh_demo.py")
        raise SystemExit(0 if old == new else 1)
    DEMO.write_text(new, encoding="utf-8")
    print(f"wrote {DEMO} ({len(new.encode()) / 1e6:.1f} MB); data unchanged")


if __name__ == "__main__":
    main()
