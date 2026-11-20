"""Prueba: leer perfiles de X con un navegador real (Playwright) sin iniciar sesion."""
import json
import re
from pathlib import Path
from playwright.sync_api import sync_playwright

RAIZ = Path(__file__).resolve().parent.parent
CUENTAS = ["SergioMassa", "MalenaGalmarini", "CeciliaMoreau"]
salida = {}
with sync_playwright() as p:
    nav = p.chromium.launch()
    ctx = nav.new_context(locale="es-AR", user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36", viewport={"width": 1280, "height": 2000})
    for c in CUENTAS:
        pg = ctx.new_page()
        try:
            pg.goto(f"https://x.com/{c}", timeout=45000)
            pg.wait_for_selector("article", timeout=25000)
            pg.wait_for_timeout(2500)
            datos = pg.evaluate("""() => [...document.querySelectorAll('article')].map(a => {
                const l = [...a.querySelectorAll('a[href*="/status/"]')].map(x => x.getAttribute('href')).find(h => /\\/status\\/\\d+$/.test(h));
                const t = a.querySelector('time');
                const tx = a.querySelector('[data-testid="tweetText"]');
                return {url: l, fecha: t && t.getAttribute('datetime'), texto: tx ? tx.innerText.slice(0, 200) : ''};
            })""")
            salida[c] = {"ok": True, "tuits": datos}
        except Exception as e:
            salida[c] = {"ok": False, "error": str(e)[:300], "titulo": pg.title(), "texto": pg.inner_text("body")[:300] if pg else ""}
        pg.close()
    nav.close()
(RAIZ / "data" / "prueba_x.json").write_text(json.dumps(salida, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(salida, ensure_ascii=False)[:1500])
