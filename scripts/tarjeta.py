#!/usr/bin/env python3
"""Genera la tarjeta diaria para estados de WhatsApp (1080 x 1920) a partir de data/edicion.json.

Escribe tarjeta.png en la raiz del sitio. Usa Archivo y Newsreader si estan en fuentes/,
y si no, DejaVu (viene con Ubuntu).
"""
import json
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

RAIZ = Path(__file__).resolve().parent.parent
W, H = 1080, 1920
CELESTE, CELESTE_OSC, ORO, SOL = "#74ACDF", "#3F86C6", "#C8961E", "#E2B230"
TINTA, TINTA2 = "#12395E", "#4A6680"
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]


def fuente(nombre, tam, peso=None, ancho=None):
    ruta = RAIZ / "fuentes" / nombre
    try:
        f = ImageFont.truetype(str(ruta), tam)
        ejes = []
        for eje in f.get_variation_axes():
            n = eje.get("name", b"")
            n = n.decode() if isinstance(n, bytes) else n
            if n.lower().startswith("weight"):
                ejes.append(peso or eje["default"])
            elif n.lower().startswith("width"):
                ejes.append(ancho or eje["default"])
            else:
                ejes.append(eje["default"])
        if ejes:
            f.set_variation_by_axes(ejes)
        return f
    except Exception:
        base = "/usr/share/fonts/truetype/dejavu/"
        if nombre.startswith("Newsreader"):
            return ImageFont.truetype(base + "DejaVuSerif.ttf", tam)
        if (peso or 400) >= 650:
            return ImageFont.truetype(base + "DejaVuSansCondensed-Bold.ttf", tam)
        return ImageFont.truetype(base + "DejaVuSans.ttf", tam)


def partir(draw, texto, f, ancho):
    lineas, actual = [], ""
    for palabra in texto.split():
        prueba = (actual + " " + palabra).strip()
        if draw.textlength(prueba, font=f) <= ancho:
            actual = prueba
        else:
            lineas.append(actual)
            actual = palabra
    if actual:
        lineas.append(actual)
    return lineas


def main():
    ed = json.loads((RAIZ / "data" / "edicion.json").read_text(encoding="utf-8"))
    fecha = datetime.fromisoformat(ed["generado"])
    img = Image.new("RGB", (W, H), "#FFFFFF")
    d = ImageDraw.Draw(img)

    # Sol detras de la franja celeste
    d.ellipse((760, -120, 1240, 360), fill="#F6E3A8")
    d.ellipse((840, -40, 1160, 280), fill=SOL)
    d.rectangle((0, 0, W, 150), fill=CELESTE)
    d.text((72, 48), "Clipping Renovador", font=fuente("Archivo.ttf", 56, 800, 115), fill="#FFFFFF")

    hora = ed.get("hora", "")
    f_hora = fuente("Archivo.ttf", 210, 900, 62)
    d.text((64, 200), hora, font=f_hora, fill=CELESTE_OSC)
    x_h = 64 + d.textlength(hora, font=f_hora) + 8
    d.text((x_h, 300), "h", font=fuente("Archivo.ttf", 90, 800), fill=ORO)
    fecha_txt = f"{DIAS[fecha.weekday()].capitalize()} {fecha.day} de {MESES[fecha.month - 1]}"
    d.text((72, 440), fecha_txt, font=fuente("Archivo.ttf", 52, 700), fill=TINTA)
    d.text((72, 506), "Lo que tenés que saber", font=fuente("Archivo.ttf", 40, 600), fill=CELESTE_OSC)
    d.rectangle((72, 574, W - 72, 578), fill=ORO)

    claves = ed.get("claves", [])[:4]
    ancho = W - 72 - 160
    limite = H - 240
    for tam in range(40, 27, -1):
        f_texto = fuente("Newsreader.ttf", tam, 450)
        paso = int(tam * 1.38)
        bloques = [partir(d, c, f_texto, ancho) for c in claves]
        total = sum(len(b) * paso for b in bloques) + 34 * (len(bloques) - 1)
        if 616 + total <= limite:
            break
    f_num = fuente("Archivo.ttf", 34, 800)
    y = 616
    for i, lineas in enumerate(bloques, 1):
        d.ellipse((72, y + 2, 126, y + 56), fill=CELESTE_OSC)
        d.text((99, y + 29), str(i), font=f_num, fill="#FFFFFF", anchor="mm")
        for j, linea in enumerate(lineas):
            d.text((160, y + j * paso), linea, font=f_texto, fill=TINTA)
        y += len(lineas) * paso + 34

    d.rectangle((0, H - 190, W, H), fill="#F3F8FD")
    d.rectangle((0, H - 194, W, H - 190), fill=ORO)
    d.text((72, H - 150), "Leé el clipping completo en", font=fuente("Archivo.ttf", 36, 500), fill=TINTA2)
    sitio = (RAIZ / "CNAME").read_text().strip() if (RAIZ / "CNAME").exists() else \
        "renzocanch2003-ops.github.io/clipping-renovador"
    tam = 40
    while tam > 22 and d.textlength(sitio, font=fuente("Archivo.ttf", tam, 700)) > W - 144:
        tam -= 2
    d.text((72, H - 100), sitio, font=fuente("Archivo.ttf", tam, 700), fill=CELESTE_OSC)

    img.save(RAIZ / "tarjeta.png", optimize=True)
    print("tarjeta.png lista")


if __name__ == "__main__":
    main()
