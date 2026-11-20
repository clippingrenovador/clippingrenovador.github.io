"""Prueba de vias gratuitas para leer los ultimos tuits de una cuenta. Escribe data/prueba_x.json."""
import json
import re
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CUENTA = "SergioMassa"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

VIAS = {
    "syndication_profile": f"https://syndication.twitter.com/srv/timeline-profile/screen-name/{CUENTA}",
    "syndication_profile_cdn": f"https://cdn.syndication.twimg.com/timeline/profile?screen_name={CUENTA}",
    "nitter_net": f"https://nitter.net/{CUENTA}/rss",
    "xcancel": f"https://xcancel.com/{CUENTA}/rss",
    "nitter_poast": f"https://nitter.poast.org/{CUENTA}/rss",
    "nitter_privacyredirect": f"https://nitter.privacyredirect.com/{CUENTA}/rss",
    "nitter_tiekoetter": f"https://nitter.tiekoetter.com/{CUENTA}/rss",
    "rsshub": f"https://rsshub.app/twitter/user/{CUENTA}",
    "twstalker": f"https://twstalker.com/{CUENTA}",
    "bing_news": "https://www.bing.com/news/search?q=%22SergioMassa%2Fstatus%22&format=rss",
    "ddg": f"https://html.duckduckgo.com/html/?q=site%3Ax.com%2F{CUENTA}%2Fstatus",
}

salida = {}
for nombre, url in VIAS.items():
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "es-AR,es;q=0.9"})
        with urllib.request.urlopen(req, timeout=25) as r:
            cuerpo = r.read().decode("utf-8", "replace")
            ids = sorted(set(re.findall(r"(?:status(?:es)?/|\"id_str\":\")(\d{15,20})", cuerpo)), reverse=True)
            salida[nombre] = {"estado": r.status, "largo": len(cuerpo), "ids": ids[:15], "muestra": cuerpo[:300]}
    except Exception as e:
        salida[nombre] = {"error": str(e)[:200]}

(RAIZ / "data" / "prueba_x.json").write_text(json.dumps(salida, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps({k: (v.get("estado"), len(v.get("ids", [])), v.get("error")) for k, v in salida.items()}, indent=1))
