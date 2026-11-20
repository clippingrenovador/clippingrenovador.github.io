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


def main():
    previas = []
    if CRUDO.exists():
        previas = json.loads(CRUDO.read_text(encoding="utf-8")).get("notas", [])
    por_id = {n["id"]: n for n in previas}

    nuevas, errores = 0, []
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
                nuevas += 1
        except Exception as e:  # una busqueda caida no frena al resto
            errores.append(f"{consulta}: {e}")
        time.sleep(1.5)

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
