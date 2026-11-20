#!/usr/bin/env python3
"""Arma la edicion publicada a partir de la curaduria.

Claude escribe data/curaduria.json eligiendo notas, tuits y videos por su id.
Este script completa medio, titulo, link y fecha desde lo que junto el rastrillo,
y escribe data/edicion.json, la copia en data/ediciones/ y el indice del archivo.

Uso: python3 scripts/armar_edicion.py            (edicion diaria)
     python3 scripts/armar_edicion.py --semanal  (Clipping Semanal: lee data/semanal/curaduria.json)
"""
import json
import re
import sys
import urllib.parse
from datetime import datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DATOS = RAIZ / "data"
ART = timezone(timedelta(hours=-3))
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]


def cargar(nombre, clave):
    p = DATOS / nombre
    return json.loads(p.read_text(encoding="utf-8")).get(clave, []) if p.exists() else []


MIN_SEGUNDOS_ENTREVISTA = 5 * 60


def segundos(duracion):
    try:
        total = 0
        for parte in (duracion or "").split(":"):
            total = total * 60 + int(parte)
        return total
    except ValueError:
        return 0


VIGENCIA_HORAS = 24
TOPES = {"temas": 12, "redes": 12, "entrevistas": 8}


def _clave(seccion, x):
    if seccion == "temas":
        return x.get("id") or " ".join(re.sub(r"[^a-z0-9 ]", " ", x.get("titulo", "").lower()).split())[:60]
    return x.get("url") or x.get("youtube") or ""


def edicion_anterior(nuevo_id):
    """La ultima edicion publicada con otro id (si se rearma la misma edicion, se compara con la previa)."""
    ix = DATOS / "ediciones" / "indice.json"
    if not ix.exists():
        return None
    for e in json.loads(ix.read_text(encoding="utf-8")).get("ediciones", []):
        if e["id"] != nuevo_id:
            f = DATOS / "ediciones" / f"{e['id']}.json"
            if f.exists():
                return json.loads(f.read_text(encoding="utf-8"))
    return None


def continuidad(nuevo, anterior, ahora, retirar=()):
    """Lo que el curador incluye queda vigente 24 h desde ahora. Lo de la edicion anterior que no se
    repitio sigue publicado hasta cumplir 24 h desde la ultima vez que se sumo o actualizo."""
    for seccion in ("temas", "redes", "entrevistas"):
        previos = {_clave(seccion, x): x for x in (anterior or {}).get(seccion, [])}
        urls_nuevas = set()
        for x in nuevo[seccion]:
            x["vigente_desde"] = ahora.isoformat(timespec="minutes")
            x["desde_hora"] = nuevo.get("hora", "")
            previo = previos.get(_clave(seccion, x))
            x["sumado"] = (previo or {}).get("sumado") or x["vigente_desde"]
            urls_nuevas.update(n["url"] for n in x.get("principales", []))
        claves_nuevas = {_clave(seccion, x) for x in nuevo[seccion]}
        arrastre = []
        for k, x in previos.items():
            if k in claves_nuevas or k in retirar or x.get("titulo") in retirar:
                continue
            if seccion == "temas" and urls_nuevas & {n["url"] for n in x.get("principales", [])}:
                continue  # el mismo tema, reescrito con otro titulo
            desde = datetime.fromisoformat(x.get("vigente_desde") or (anterior or {}).get("generado"))
            if ahora - desde < timedelta(hours=VIGENCIA_HORAS):
                x.pop("destacado", None)
                arrastre.append(x)
        arrastre.sort(key=lambda x: x.get("vigente_desde", ""), reverse=True)
        nuevo[seccion] = (nuevo[seccion] + arrastre)[:TOPES[seccion]]


def main():
    semanal = "--semanal" in sys.argv
    origen = DATOS / "semanal" / "curaduria.json" if semanal else DATOS / "curaduria.json"
    cur = json.loads(origen.read_text(encoding="utf-8"))
    notas = {n["id"]: n for n in cargar("crudo.json", "notas")}
    videos = {v["id"]: v for v in cargar("videos.json", "videos")}
    tuits = {t["id"]: t for t in cargar("tuits.json", "tuits")}
    faltan = []

    def nota(i):
        n = notas.get(i)
        if not n:
            faltan.append(i)
            return None
        url = n.get("url_original") or n["url"]
        base = n.get("url_original") or n.get("medio_url") or ""
        dominio = urllib.parse.urlparse(base).netloc.lower().removeprefix("www.")
        return {"medio": n["medio"], "titulo": n["titulo"], "url": url, "fecha": n["fecha"], "dominio": dominio}

    temas = []
    for t in cur.get("temas", []):
        princ = [x for x in (nota(i) for i in t.get("principales", [])) if x]
        otras = [x for x in (nota(i) for i in t.get("otras", [])) if x]
        if not princ:
            continue
        temas.append({"id": t.get("id", ""), "titulo": t["titulo"], "resumen": t.get("resumen", ""), "tono": t.get("tono", "neutro"),
                      "dirigentes": t.get("dirigentes", []), "principales": princ,
                      "otras": [{"medio": o["medio"], "url": o["url"], "dominio": o["dominio"]} for o in otras],
                      "cantidad_notas": len(princ) + len(otras)})

    redes = []
    for r in cur.get("redes", []):
        t = tuits.get(str(r.get("tuit_id", "")))
        url = r.get("url") or (t and t["url"])
        if not url:
            faltan.append(r.get("tuit_id"))
            continue
        redes.append({"url": url, "autor": r.get("autor") or (t and "@" + t["usuario"]) or "", "nota": r.get("nota", "")})

    entrevistas = []
    for e in cur.get("entrevistas", []):
        v = videos.get(e.get("video_id", ""))
        if not v and not e.get("titulo"):
            faltan.append(e.get("video_id"))
            continue
        v = v or {}
        if v and segundos(v.get("duracion")) < MIN_SEGUNDOS_ENTREVISTA:
            print("Descartado por corto:", v.get("titulo", "")[:70], v.get("duracion"))
            continue
        entrevistas.append({"youtube": e.get("video_id"), "titulo": e.get("titulo") or v.get("titulo", ""),
                            "canal": e.get("canal") or v.get("canal", ""), "fecha_txt": v.get("publicado", ""),
                            "duracion": v.get("duracion", ""),
                            "url": v.get("url") or f"https://www.youtube.com/watch?v={e.get('video_id')}"})

    ahora = datetime.now(ART)
    if semanal:
        armar_semanal(cur, temas, redes, entrevistas, notas, ahora)
        return
    hora = cur.get("hora") or ahora.strftime("%H")
    medios = {n["medio"] for n in notas.values()
              if datetime.fromisoformat(n["fecha"]) >= ahora - timedelta(hours=24)}
    en_24h = sum(1 for n in notas.values() if datetime.fromisoformat(n["fecha"]) >= ahora - timedelta(hours=24))
    edicion = {
        "id": ahora.strftime("%Y-%m-%d-") + hora,
        "generado": ahora.isoformat(timespec="minutes"),
        "hora": hora,
        "claves": cur.get("claves", []),
        "temas": temas,
        "redes": redes,
        "entrevistas": entrevistas,
        "metricas": {"notas_analizadas": en_24h, "medios": len(medios), "temas": len(temas)},
    }
    continuidad(edicion, edicion_anterior(edicion["id"]), ahora, set(cur.get("retirar", [])))
    temas, redes, entrevistas = edicion["temas"], edicion["redes"], edicion["entrevistas"]
    edicion["metricas"]["temas"] = len(temas)
    (DATOS / "ediciones").mkdir(exist_ok=True)
    texto = json.dumps(edicion, ensure_ascii=False, indent=1)
    (DATOS / "edicion.json").write_text(texto, encoding="utf-8")
    (DATOS / "ediciones" / f"{edicion['id']}.json").write_text(texto, encoding="utf-8")

    ix_p = DATOS / "ediciones" / "indice.json"
    indice = json.loads(ix_p.read_text(encoding="utf-8")) if ix_p.exists() else {"ediciones": []}
    indice["ediciones"] = [e for e in indice["ediciones"] if e["id"] != edicion["id"]]
    indice["ediciones"].insert(0, {"id": edicion["id"], "temas": len(temas),
                                   "titulo": f"{ahora.day} de {MESES[ahora.month - 1]}, {hora} h"})
    indice["ediciones"] = indice["ediciones"][:270]
    ix_p.write_text(json.dumps(indice, ensure_ascii=False, indent=1), encoding="utf-8")

    # Indice del buscador: un registro por tema de cada edicion
    bus_p = DATOS / "buscador.json"
    buscador = json.loads(bus_p.read_text(encoding="utf-8")) if bus_p.exists() else {"temas": []}
    buscador["temas"] = [b for b in buscador["temas"] if b["e"] != edicion["id"]]
    nuevos = [{"e": edicion["id"], "f": edicion["generado"][:10], "t": t["titulo"], "r": t["resumen"],
               "d": t["dirigentes"], "o": t["tono"],
               "n": [{"m": n["medio"], "ti": n["titulo"], "u": n["url"]} for n in t["principales"]]}
              for t in temas]
    buscador["temas"] = (nuevos + buscador["temas"])[:4000]
    bus_p.write_text(json.dumps(buscador, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    copiar_pagina_semanal()
    print(f"Edicion {edicion['id']}: {len(temas)} temas, {len(redes)} tuits, {len(entrevistas)} videos")
    if faltan:
        print("IDs no encontrados (revisar):", faltan)
        sys.exit(2 if not temas else 0)


def armar_semanal(cur, temas, redes, entrevistas, notas, ahora):
    hasta = datetime.fromisoformat(cur.get("hasta", ahora.date().isoformat()))
    desde = datetime.fromisoformat(cur.get("desde", (hasta - timedelta(days=6)).date().isoformat()))
    en_semana = [n for n in notas.values() if desde.date() <= datetime.fromisoformat(n["fecha"]).date() <= hasta.date()]
    mes = MESES[hasta.month - 1][:3]
    rango = f"{desde.day}–{hasta.day}" if desde.month == hasta.month else f"{desde.day}/{desde.month}–{hasta.day}/{hasta.month}"
    sid = hasta.strftime("%Y-%m-%d")
    semana = {
        "id": sid, "generado": ahora.isoformat(timespec="minutes"),
        "titulo_semana": f"Semana del {desde.day} de {MESES[desde.month - 1]} al {hasta.day} de {MESES[hasta.month - 1]}",
        "rango_dias": rango, "rango_mes": mes if desde.month == hasta.month else "",
        "claves": cur.get("claves", []), "temas": temas, "redes": redes, "entrevistas": entrevistas,
        "metricas": {"notas_analizadas": len(en_semana), "medios": len({n["medio"] for n in en_semana}),
                     "temas": len(temas)},
    }
    carpeta = DATOS / "semanal"
    texto = json.dumps(semana, ensure_ascii=False, indent=1)
    (carpeta / f"{sid}.json").write_text(texto, encoding="utf-8")
    (carpeta / "ultimo.json").write_text(texto, encoding="utf-8")
    ix_p = carpeta / "indice.json"
    indice = json.loads(ix_p.read_text(encoding="utf-8")) if ix_p.exists() else {"ediciones": []}
    indice["ediciones"] = [e for e in indice["ediciones"] if e["id"] != sid]
    indice["ediciones"].insert(0, {"id": sid, "temas": len(temas), "titulo": semana["titulo_semana"]})
    ix_p.write_text(json.dumps(indice, ensure_ascii=False, indent=1), encoding="utf-8")
    copiar_pagina_semanal()
    print(f"Clipping Semanal {sid}: {len(temas)} temas, {len(redes)} tuits, {len(entrevistas)} videos")


def copiar_pagina_semanal():
    html = (RAIZ / "index.html").read_text(encoding="utf-8")
    html = html.replace("<body>", '<body data-modo="semanal">', 1)
    html = html.replace("<title>Clipping Renovador · Lo que se dice del Frente Renovador hoy</title>",
                        "<title>Clipping Semanal Renovador</title>")
    html = html.replace('<meta property="og:title" content="Clipping Renovador">',
                        '<meta property="og:title" content="CLIPPING SEMANAL RENOVADOR">')
    (RAIZ / "semanal.html").write_text(html, encoding="utf-8")


if __name__ == "__main__":
    main()
