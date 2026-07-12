"""
美食地圖產生器：places.json → map.html（手機可開）+ places.csv（Google My Maps 匯入用）

用法：
  python3 build_map.py                # 重建 map.html + places.csv
  python3 build_map.py --check 店名   # 新增前查重（比對 name / name_official，模糊比對）

新店來源：貼 IG / YouTube / FB 影片連結給 Claude 說「加進美食地圖」，
流程見 WORKFLOW.md。
"""
import sys, json, html, csv, re, unicodedata
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).parent
DATA = ROOT / "places.json"


def norm(s: str) -> str:
    """正規化店名：全形轉半形、去空白符號、轉小寫，供查重比對"""
    s = unicodedata.normalize("NFKC", s or "").lower()
    return re.sub(r"[\s\-_・･.,、。()（）「」『』]", "", s)


def load() -> list[dict]:
    return json.loads(DATA.read_text())["places"]


def check(query: str) -> int:
    q = norm(query)
    hits = [p for p in load()
            if q in norm(p["name"]) or norm(p["name"]) in q
            or (p.get("name_official") and (q in norm(p["name_official"]) or norm(p["name_official"]) in q))]
    if hits:
        print(f"⚠️ 可能重複（{len(hits)} 筆）：")
        for p in hits:
            print(f"  - {p['name']}（{p.get('name_official') or '原名待確認'}）{p['area']}｜{p['source_title']}")
        return 1
    print("✅ 沒有重複，可以新增")
    return 0


def maps_query(p: dict) -> str:
    """有地址用「店名 地址」最準，沒有就「店名 區域」"""
    name = p.get("name_official") or p["name"]
    loc = p.get("address") or p["area"].split("・")[-1]
    return f"{name} {loc}"


def maps_url(p: dict) -> str:
    return "https://www.google.com/maps/search/?api=1&query=" + quote(maps_query(p))


def build_csv(places: list[dict]):
    """Google My Maps 匯入用：新增圖層 → 匯入 → 選這個 CSV → 定位欄選「搜尋關鍵字」"""
    with open(ROOT / "places.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["名稱", "搜尋關鍵字", "類型", "區域", "備註", "來源影片"])
        for p in places:
            name = p.get("name_official") or p["name"]
            w.writerow([name, maps_query(p), p["type"], p["area"], p["note"], p["source"]])


CSS = """
:root{--surface:#fcfcfb;--page:#f9f9f7;--ink:#0b0b0b;--ink2:#52514e;--muted:#898781;
--ring:rgba(11,11,11,.10);--s1:#2a78d6;--s3:#eda100;--warnbg:#fff6e2}
@media (prefers-color-scheme:dark){:root{--surface:#1a1a19;--page:#0d0d0d;--ink:#fff;
--ink2:#c3c2b7;--muted:#898781;--ring:rgba(255,255,255,.10);--s1:#3987e5;--s3:#c98500;--warnbg:#2a230f}}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;background:var(--page);
color:var(--ink);padding:14px;max-width:720px;margin:0 auto;font-size:15px;line-height:1.55}
h1{font-size:19px;margin-bottom:2px}.sub{color:var(--muted);font-size:12px;margin-bottom:12px}
#q{width:100%;padding:10px 12px;font-size:15px;border:1px solid var(--ring);border-radius:10px;
background:var(--surface);color:var(--ink);margin-bottom:14px}
h2{font-size:14px;color:var(--ink2);margin:18px 0 8px}
.card{background:var(--surface);border:1px solid var(--ring);border-radius:12px;
padding:12px 14px;margin-bottom:10px}
.nm{font-weight:700;font-size:16px}
.alias{color:var(--muted);font-size:12px;font-weight:400}
.badge{display:inline-block;font-size:11px;padding:1px 8px;border-radius:999px;
border:1px solid var(--ring);color:var(--ink2);margin-left:6px;vertical-align:2px}
.badge.unc{background:var(--warnbg)}
.note{color:var(--ink2);font-size:13px;margin:6px 0 8px}
.acts a{display:inline-block;font-size:13px;text-decoration:none;color:var(--s1);
border:1px solid var(--ring);border-radius:9px;padding:6px 12px;margin-right:8px;background:var(--page)}
.acts a.map{font-weight:700}
.hide{display:none}
.footer{color:var(--muted);font-size:11px;text-align:center;margin:18px 0 8px}
"""

JS = """
document.getElementById('q').addEventListener('input', e => {
  const q = e.target.value.trim().toLowerCase();
  document.querySelectorAll('.card').forEach(c => {
    c.classList.toggle('hide', q && !c.dataset.text.includes(q));
  });
  document.querySelectorAll('h2[data-area]').forEach(h => {
    const anyVisible = [...document.querySelectorAll(`.card[data-area="${h.dataset.area}"]`)]
      .some(c => !c.classList.contains('hide'));
    h.classList.toggle('hide', !anyVisible);
  });
});
"""


def build_html(places: list[dict]):
    areas = {}
    for p in places:
        areas.setdefault(p["area"], []).append(p)

    body = []
    for area in sorted(areas):
        body.append(f"<h2 data-area='{html.escape(area)}'>📍 {html.escape(area)}（{len(areas[area])} 家）</h2>")
        for p in sorted(areas[area], key=lambda x: x["type"]):
            name = p.get("name_official") or p["name"]
            alias = "" if name == p["name"] else f"<span class='alias'>（影片叫法：{html.escape(p['name'])}）</span>"
            unc = "" if p.get("confirmed") else "<span class='badge unc'>店名待確認</span>"
            text = norm(f"{p['name']}{p.get('name_official') or ''}{p['type']}{p['area']}{p['note']}")
            body.append(
                f"<div class='card' data-area='{html.escape(area)}' data-text='{html.escape(text)}'>"
                f"<div class='nm'>{html.escape(name)} <span class='badge'>{html.escape(p['type'])}</span>{unc}</div>"
                f"{alias}<div class='note'>{html.escape(p['note'])}</div>"
                f"<div class='acts'><a class='map' href='{maps_url(p)}' target='_blank'>🗺️ 開 Google Maps</a>"
                f"<a href='{html.escape(p['source'])}' target='_blank'>▶ 來源影片</a></div></div>")

    doc = (f"<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'>"
           f"<meta name='viewport' content='width=device-width, initial-scale=1'>"
           f"<title>我的美食地圖</title><style>{CSS}</style></head><body>"
           f"<h1>🍜 我的美食地圖</h1>"
           f"<div class='sub'>共 {len(places)} 家｜來自影片筆記｜點「開 Google Maps」直接導航</div>"
           f"<input id='q' type='search' placeholder='搜尋：拉麵、池袋、餃子…'>"
           + "".join(body)
           + f"<div class='footer'>build_map.py 自動產生｜資料：places.json</div>"
           f"<script>{JS}</script></body></html>")
    (ROOT / "map.html").write_text(doc)


def build_md(places: list[dict]):
    """Obsidian 用的 Markdown 清單（symlink 進 vault 後自動同步）"""
    areas = {}
    for p in places:
        areas.setdefault(p["area"], []).append(p)
    lines = ["# 🍜 美食清單", "",
             f"> 共 {len(places)} 家｜資料來源 places.json｜"
             f"手機導航用 [map.html](map.html)｜新增：貼影片連結給 Claude 說「加進美食地圖」", ""]
    for area in sorted(areas):
        lines.append(f"## 📍 {area}")
        for p in sorted(areas[area], key=lambda x: x["type"]):
            name = p.get("name_official") or p["name"]
            unc = "" if p.get("confirmed") else "（店名待確認）"
            lines.append(f"- **{name}**{unc}｜{p['type']}｜{p['note']}")
            lines.append(f"  [Google Maps]({maps_url(p)})｜[來源影片]({p['source']})")
        lines.append("")
    (ROOT / "美食清單.md").write_text("\n".join(lines))


def main():
    if len(sys.argv) >= 3 and sys.argv[1] == "--check":
        sys.exit(check(" ".join(sys.argv[2:])))
    places = load()
    dup = {}
    for p in places:  # 存檔內部自我查重
        k = norm(p.get("name_official") or p["name"])
        if k in dup:
            print(f"⚠️ places.json 內有重複：{p['name']} vs {dup[k]['name']}")
        dup[k] = p
    build_html(places)
    build_csv(places)
    build_md(places)
    print(f"🗺️ 已重建 map.html + places.csv + 美食清單.md（共 {len(places)} 家）")


if __name__ == "__main__":
    main()
