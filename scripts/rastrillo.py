#!/usr/bin/env python3
"""Rastrillo: junta notas de Google Noticias sobre Massa y el Frente Renovador.

Corre cada hora en GitHub Actions. No usa IA ni librerias externas.
Escribe data/crudo.json con las notas de los ultimos 7 dias, sin duplicados.
La curaduria (agrupar, elegir las mejores, resumir) la hace Claude 3 veces por dia.
"""
import email.utils
import hashlib
import json
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CRUDO = RAIZ / "data" / "crudo.json"
DIAS_GUARDADOS = 7
ART = timezone(timedelta(hours=-3))

# Cada busqueda es una consulta a Google Noticias Argentina (ultimas 24 h).
BUSQUEDAS = [
    '"Sergio Massa"',
    '"Frente Renovador"',
    'massismo',
    '"Malena Galmarini"',
    '"Sebastián Galmarini"',
    '"Cecilia Moreau"',
    '"Diego Giuliano"',
    '"Juan Andreotti"',
    '"Katia Blanc"',
    '"Juan Malpeli"',
    '"Roberto Vázquez" diputado',
    '"Javier Gastón"',
    '"Ramiro Gutiérrez"',
    '"Micaela Morán"',
    '"Germán Di Cesare"',
    '"Guillermo Michel"',
    '"Pablo Garate"',
    '"Darío Golía"',
    'Eslaiman diputado',
    '"Felipe Romero" Frente Renovador',
    '"Felipe Romero" juventud',
    '"Feli Romero"',
    '"Jóvenes FR"',
    '"Juventud del Frente Renovador"',
    'encuesta Massa',
    'encuesta "Frente Renovador"',
]

UA = "Mozilla/5.0 (compatible; ClippingRenovador/1.0; +https://github.com/renzocanch2003-ops/clipping-renovador)"


def normaliza(texto):
    texto = unicodedata.normalize("NFD", texto or "").lower()
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9 ]+", " ", texto).split()


def clave_titulo(titulo):
    return hashlib.sha1(" ".join(normaliza(titulo)).encode()).hexdigest()[:12]


def leer_feed(consulta):
    q = urllib.parse.quote(consulta + " when:1d")
    url = f"https://news.google.com/rss/search?q={q}&hl=es-419&gl=AR&ceid=AR:es-419"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        raiz = ET.fromstring(r.read())
    for item in raiz.iter("item"):
        titulo = (item.findtext("title") or "").strip()
        fuente_el = item.find("source")
        medio = (fuente_el.text or "").strip() if fuente_el is not None else ""
        medio_url = fuente_el.get("url", "") if fuente_el is not None else ""
        # Google agrega " - Medio" al final del titulo.
        if medio and titulo.endswith(" - " + medio):
            titulo = titulo[: -len(" - " + medio)].strip()
        fecha_txt = item.findtext("pubDate") or ""
        try:
            fecha = email.utils.parsedate_to_datetime(fecha_txt).astimezone(ART)
        except Exception:
            fecha = datetime.now(ART)
        yield {
            "id": clave_titulo(titulo),
            "titulo": titulo,
            "medio": medio,
            "medio_url": medio_url,
            "url": (item.findtext("link") or "").strip(),
            "fecha": fecha.isoformat(timespec="minutes"),
            "busqueda": consulta,
        }


VIDEOS = RAIZ / "data" / "videos.json"
BUSQUEDAS_YT = [
    "Sergio Massa", "Frente Renovador", "Malena Galmarini", "Sebastián Galmarini",
    "Cecilia Moreau", "Diego Giuliano", "Juan Andreotti", "Natalia de la Sota",
    "Marina Salzmann", "Katia Blanc", "Rubén Eslaiman", "Micaela Morán",
    "Felipe Romero", "Feli Romero", "Jóvenes FR",
]


def _texto(nodo):
    if not nodo:
        return ""
    if "simpleText" in nodo:
        return nodo["simpleText"]
    return "".join(r.get("text", "") for r in nodo.get("runs", []))


def _buscar_videos(dato, salida):
    if isinstance(dato, dict):
        if "videoRenderer" in dato:
            salida.append(dato["videoRenderer"])
        for v in dato.values():
            _buscar_videos(v, salida)
    elif isinstance(dato, list):
        for v in dato:
            _buscar_videos(v, salida)


def leer_youtube(consulta):
    # Filtro "subidos hoy" de la busqueda de YouTube.
    url = ("https://www.youtube.com/results?search_query="
           + urllib.parse.quote(consulta) + "&sp=EgIIAg%253D%253D&hl=es-419&gl=AR")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept-Language": "es-AR,es;q=0.9"})
    with urllib.request.urlopen(req, timeout=30) as r:
        html = r.read().decode("utf-8", "replace")
    m = re.search(r"var ytInitialData = (\{.*?\});</script>", html, re.S)
    if not m:
        return []
    encontrados = []
    _buscar_videos(json.loads(m.group(1)), encontrados)
    salida = []
    for v in encontrados:
        titulo = _texto(v.get("title"))
        canal = _texto(v.get("ownerText")) or _texto(v.get("longBylineText"))
        # Solo videos que nombran a la persona o al espacio buscado.
        if not set(normaliza(consulta)[-1:]) & set(normaliza(titulo + " " + canal)):
            continue
        salida.append({
            "id": v.get("videoId"),
            "titulo": titulo,
            "canal": canal,
            "publicado": _texto(v.get("publishedTimeText")),
            "duracion": _texto(v.get("lengthText")),
            "busqueda": consulta,
            "url": "https://www.youtube.com/watch?v=" + v.get("videoId", ""),
        })
    return salida


def rastrillar_videos():
    previos = []
    if VIDEOS.exists():
        previos = json.loads(VIDEOS.read_text(encoding="utf-8")).get("videos", [])
    por_id = {v["id"]: v for v in previos}
    errores, nuevos = [], 0
    ahora = datetime.now(ART).isoformat(timespec="minutes")
    for consulta in BUSQUEDAS_YT:
        try:
            for v in leer_youtube(consulta):
                if v["id"] and v["id"] not in por_id:
                    v["visto"] = ahora
                    por_id[v["id"]] = v
                    nuevos += 1
        except Exception as e:
            errores.append(f"YouTube {consulta}: {e}")
        time.sleep(2)
    limite = (datetime.now(ART) - timedelta(days=DIAS_GUARDADOS)).isoformat()
    videos = sorted((v for v in por_id.values() if v.get("visto", "") >= limite[:16]),
                    key=lambda v: v.get("visto", ""), reverse=True)
    VIDEOS.write_text(json.dumps({"generado": ahora, "total": len(videos), "errores": errores,
                                  "videos": videos}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"YouTube: {nuevos} videos nuevos, {len(videos)} en total, {len(errores)} errores")


TUITS = RAIZ / "data" / "tuits.json"
RE_TUIT = re.compile(r"https?://(?:www\.|mobile\.)?(?:twitter|x)\.com/([A-Za-z0-9_]{1,15})/status(?:es)?/(\d{6,25})")


def resolver_google(url):
    """Convierte el link de Google Noticias en el link real de la nota."""
    m = re.search(r"/articles/([A-Za-z0-9_\-]+)", url)
    if not m:
        return url
    art = m.group(1)
    req = urllib.request.Request(f"https://news.google.com/rss/articles/{art}", headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        html = r.read().decode("utf-8", "replace")
    sg = re.search(r'data-n-a-sg="([^"]+)"', html)
    ts = re.search(r'data-n-a-ts="([^"]+)"', html)
    if not (sg and ts):
        return url
    interno = ('["garturlreq",[["X","X",["X","X"],null,null,1,1,"US:en",null,1,null,null,null,null,null,0,1],'
               '"X","X",1,[1,1,1],1,1,null,0,0,null,0],"%s",%s,"%s"]') % (art, ts.group(1), sg.group(1))
    cuerpo = urllib.parse.urlencode({"f.req": json.dumps([[["Fbv4je", interno, None, "generic"]]])}).encode()
    req = urllib.request.Request("https://news.google.com/_/DotsSplashUi/data/batchexecute", data=cuerpo,
                                 headers={"User-Agent": "Mozilla/5.0",
                                          "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"})
    with urllib.request.urlopen(req, timeout=20) as r:
        texto = r.read().decode("utf-8", "replace")
    datos = json.loads(texto.split("\n\n", 1)[1])[:-2]
    return json.loads(datos[0][2])[1]


def tuits_en_nota(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept-Language": "es-AR,es;q=0.9"})
    with urllib.request.urlopen(req, timeout=20) as r:
        html = r.read(3_000_000).decode("utf-8", "replace")
    vistos = {}
    for usuario, id_ in RE_TUIT.findall(html):
        if usuario.lower() in ("intent", "share", "i", "home", "search"):
            continue
        vistos[id_] = usuario
    return vistos


def rastrillar_tuits(notas_nuevas):
    previos = []
    if TUITS.exists():
        previos = json.loads(TUITS.read_text(encoding="utf-8")).get("tuits", [])
    por_id = {t["id"]: t for t in previos}
    ahora = datetime.now(ART).isoformat(timespec="minutes")
    revisadas, errores = 0, 0
    for nota in notas_nuevas[:80]:
        try:
            real = resolver_google(nota["url"])
            if real and real != nota["url"]:
                nota["url_original"] = real
            for id_, usuario in tuits_en_nota(real).items():
                t = por_id.setdefault(id_, {"id": id_, "usuario": usuario, "visto": ahora,
                                             "url": f"https://twitter.com/{usuario}/status/{id_}", "citado_en": []})
                if len(t["citado_en"]) < 8:
                    t["citado_en"].append({"medio": nota["medio"], "titulo": nota["titulo"], "nota_id": nota["id"]})
            revisadas += 1
        except Exception:
            errores += 1
        nota["revisada"] = True
        time.sleep(0.8)
    limite = (datetime.now(ART) - timedelta(days=DIAS_GUARDADOS)).isoformat()[:16]
    tuits = sorted((t for t in por_id.values() if t["visto"] >= limite), key=lambda t: t["visto"], reverse=True)
    TUITS.write_text(json.dumps({"generado": ahora, "total": len(tuits), "tuits": tuits},
                                ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Tuits: {revisadas} notas revisadas, {errores} sin poder abrir, {len(tuits)} tuits guardados")


def main():
    try:
        rastrillar_videos()
    except Exception as e:
        print("YouTube fallo:", e)
    previas = []
    if CRUDO.exists():
        previas = json.loads(CRUDO.read_text(encoding="utf-8")).get("notas", [])
    por_id = {n["id"]: n for n in previas}

    nuevas, errores, lista_nuevas = 0, [], []
    for consulta in BUSQUEDAS:
        try:
            for nota in leer_feed(consulta):
                if not nota["titulo"]:
                    continue
                if nota["id"] in por_id:
                    previa = por_id[nota["id"]]
                    if nota["busqueda"] not in previa.get("busquedas", []):
                        previa.setdefault("busquedas", []).append(nota["busqueda"])
                    continue
                nota["busquedas"] = [nota.pop("busqueda")]
                nota["visto"] = datetime.now(ART).isoformat(timespec="minutes")
                por_id[nota["id"]] = nota
                lista_nuevas.append(nota)
                nuevas += 1
        except Exception as e:  # una busqueda caida no frena al resto
            errores.append(f"{consulta}: {e}")
        time.sleep(1.5)

    try:
        rastrillar_tuits(sorted((n for n in por_id.values() if not n.get("revisada")), key=lambda n: n["fecha"], reverse=True))
    except Exception as e:
        print("Tuits fallo:", e)

    limite = datetime.now(ART) - timedelta(days=DIAS_GUARDADOS)
    notas = [n for n in por_id.values() if datetime.fromisoformat(n["fecha"]) >= limite]
    notas.sort(key=lambda n: n["fecha"], reverse=True)

    CRUDO.parent.mkdir(parents=True, exist_ok=True)
    CRUDO.write_text(json.dumps({
        "generado": datetime.now(ART).isoformat(timespec="minutes"),
        "total": len(notas),
        "nuevas_ultima_corrida": nuevas,
        "errores": errores,
        "notas": notas,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{nuevas} notas nuevas, {len(notas)} en total, {len(errores)} errores")
    if errores and nuevas == 0 and not previas:
        sys.exit(1)


if __name__ == "__main__":
    main()
