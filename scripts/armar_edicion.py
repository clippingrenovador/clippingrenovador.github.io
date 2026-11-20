#!/usr/bin/env python3
"""Arma la edicion publicada a partir de la curaduria.

Claude escribe data/curaduria.json eligiendo notas, tuits y videos por su id.
Este script completa medio, titulo, link y fecha desde lo que junto el rastrillo,
y escribe data/edicion.json, la copia en data/ediciones/ y el indice del archivo.

Uso: python3 scripts/armar_edicion.py
"""
import json
import sys
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


def main():
    cur = json.loads((DATOS / "curaduria.json").read_text(encoding="utf-8"))
    notas = {n["id"]: n for n in cargar("crudo.json", "notas")}
    videos = {v["id"]: v for v in cargar("videos.json", "videos")}
    tuits = {t["id"]: t for t in cargar("tuits.json", "tuits")}
    faltan = []

    def nota(i):
        n = notas.get(i)
        if not n:
            faltan.append(i)
            return None
        return {"medio": n["medio"], "titulo": n["titulo"], "url": n.get("url_original") or n["url"],
                "fecha": n["fecha"]}

    temas = []
    for t in cur.get("temas", []):
        princ = [x for x in (nota(i) for i in t.get("principales", [])) if x]
        otras = [x for x in (nota(i) for i in t.get("otras", [])) if x]
        if not princ:
            continue
        temas.append({"titulo": t["titulo"], "resumen": t.get("resumen", ""), "tono": t.get("tono", "neutro"),
                      "dirigentes": t.get("dirigentes", []), "principales": princ,
                      "otras": [{"medio": o["medio"], "url": o["url"]} for o in otras],
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
        entrevistas.append({"youtube": e.get("video_id"), "titulo": e.get("titulo") or v.get("titulo", ""),
                            "canal": e.get("canal") or v.get("canal", ""), "fecha_txt": v.get("publicado", ""),
                            "url": v.get("url") or f"https://www.youtube.com/watch?v={e.get('video_id')}"})

    ahora = datetime.now(ART)
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

    print(f"Edicion {edicion['id']}: {len(temas)} temas, {len(redes)} tuits, {len(entrevistas)} videos")
    if faltan:
        print("IDs no encontrados (revisar):", faltan)
        sys.exit(2 if not temas else 0)


if __name__ == "__main__":
    main()
