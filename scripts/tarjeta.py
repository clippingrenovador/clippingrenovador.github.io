#!/usr/bin/env python3
"""Genera la tarjeta diaria para estados de WhatsApp (1080 x 1920) a partir de data/edicion.json.

Escribe tarjeta.jpg en la raiz del sitio. Usa Archivo y Newsreader si estan en fuentes/,
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


AZUL, NEGRO, CREMA, PAPEL = (24, 140, 232), (14, 18, 26), (244, 240, 228), (243, 239, 229)


def ancho_tinta(d, texto, f, esp):
    x, izq, der = 0, None, 0
    for c in texto:
        b = d.textbbox((x, 0), c, font=f)
        izq = b[0] if izq is None else izq
        der = b[2]
        x += d.textlength(c, font=f) + esp
    return der - izq, izq


def escribir(d, texto, f, esp, x0, y, color):
    _, izq = ancho_tinta(d, texto, f, esp)
    x = x0 - izq
    for c in texto:
        d.text((x, y), c, font=f, fill=color)
        x += d.textlength(c, font=f) + esp


def main():
    import og
    ed = json.loads((RAIZ / "data" / "edicion.json").read_text(encoding="utf-8"))
    fecha = datetime.fromisoformat(ed["generado"])
    M = 72
    ancho_util = W - 2 * M
    ALTO_AFICHE = 690

    img = Image.new("RGB", (W, H), PAPEL)
    fondo = og.fondo_semitono(W, ALTO_AFICHE, semilla=1945, paso_px=7)
    img.paste(fondo.resize((W, ALTO_AFICHE)), (0, 0))
    d = ImageDraw.Draw(img)

    # Titulo: RENOVADOR ocupa el ancho de los filetes; CLIPPING entre dos soles
    tam = 200
    while tam > 60:
        f = fuente("Archivo.ttf", tam, 900, 125)
        if ancho_tinta(d, "RENOVADOR", f, 2)[0] <= ancho_util:
            break
        tam -= 2
    w_ren, _ = ancho_tinta(d, "RENOVADOR", f, 0)
    esp_ren = (ancho_util - w_ren) / 8
    w_cli, _ = ancho_tinta(d, "CLIPPING", f, 2)
    caja = d.textbbox((0, 0), "RENOVADOR", font=f)
    alto = caja[3] - caja[1]
    g, entre, aire, gap = 9, 8, 40, int(alto * 0.36)

    def filetes(y0):
        d.rectangle([M, y0, W - M, y0 + g], fill=CREMA)
        d.rectangle([M, y0 + g + entre, W - M, y0 + 2 * g + entre], fill=CREMA)

    y = 120
    filetes(y)
    y_cli = y + 2 * g + entre + aire
    escribir(d, "CLIPPING", f, 2, (W - w_cli) / 2, y_cli - caja[1], CREMA)
    y_ren = y_cli + alto + gap
    escribir(d, "RENOVADOR", f, esp_ren, M, y_ren - caja[1], CREMA)
    y_fin = y_ren + alto + aire
    filetes(y_fin)
    r_sol = min(alto * 0.46, (ancho_util - w_cli) / 2 * 0.36)
    og.sol_grande(d, M + r_sol, y_cli + alto / 2, r_sol, CREMA)
    og.sol_grande(d, W - M - r_sol, y_cli + alto / 2, r_sol, CREMA)

    # Linea de fecha como en los afiches: fecha en italica, hilo y hora
    y_fecha = y_fin + 2 * g + entre + 44
    fecha_txt = f"{DIAS[fecha.weekday()]} {fecha.day} de {MESES[fecha.month - 1]}"
    f_fecha = fuente("Newsreader.ttf", 46, 400)
    try:
        f_fecha = ImageFont.truetype(str(RAIZ / "fuentes" / "Newsreader-Italic.ttf"), 46)
    except OSError:
        pass
    d.text((M, y_fecha), fecha_txt, font=f_fecha, fill=CREMA)
    hora = (ed.get("hora") or "") + " h"
    f_hora = fuente("Archivo.ttf", 52, 900, 125)
    w_hora = d.textlength(hora, font=f_hora)
    d.text((W - M - w_hora, y_fecha - 6), hora, font=f_hora, fill=CREMA)
    x_hilo = M + d.textlength(fecha_txt, font=f_fecha) + 24
    d.rectangle([x_hilo, y_fecha + 30, W - M - w_hora - 24, y_fecha + 32], fill=CREMA)

    # Lo que tenes que saber
    y = ALTO_AFICHE + 70
    f_tit = fuente("Archivo.ttf", 40, 900, 125)
    d.text((M, y), "LO QUE TENÉS QUE SABER", font=f_tit, fill=NEGRO)
    wt = d.textlength("LO QUE TENÉS QUE SABER", font=f_tit)
    d.rectangle([M, y + 62, M + wt, y + 65], fill=AZUL)
    d.rectangle([M, y + 71, M + wt, y + 74], fill=AZUL)
    y_claves = y + 120

    claves = ed.get("claves", [])[:4]
    ancho = W - M - 150
    limite = H - 200
    for tam in range(42, 27, -1):
        f_texto = fuente("Newsreader.ttf", tam, 450)
        paso = int(tam * 1.36)
        bloques = [partir(d, c, f_texto, ancho) for c in claves]
        total = sum(len(b) * paso for b in bloques) + 36 * (len(bloques) - 1)
        if y_claves + total <= limite:
            break
    f_num = fuente("Archivo.ttf", 30, 900, 110)
    yy = y_claves
    for i, lineas in enumerate(bloques, 1):
        d.ellipse((M, yy + 4, M + 50, yy + 54), fill=AZUL)
        d.text((M + 25, yy + 29), str(i), font=f_num, fill="#FFFFFF", anchor="mm")
        for j, linea in enumerate(lineas):
            d.text((M + 78, yy + j * paso), linea, font=f_texto, fill=(19, 27, 46))
        yy += len(lineas) * paso + 36

    # Pie: franja de afiche con la direccion
    pie = og.fondo_semitono(W, 150, semilla=17, paso_px=7)
    img.paste(pie.resize((W, 150)), (0, H - 150))
    d = ImageDraw.Draw(img)
    sitio = (RAIZ / "CNAME").read_text().strip() if (RAIZ / "CNAME").exists() else "clippingrenovador.github.io"
    f_sitio = fuente("Archivo.ttf", 40, 900, 115)
    d.text((W / 2, H - 75), sitio, font=f_sitio, fill=CREMA, anchor="mm")

    img.save(RAIZ / "tarjeta.jpg", quality=80, optimize=True, progressive=True)
    print("tarjeta.jpg lista", (RAIZ / "tarjeta.jpg").stat().st_size // 1024, "KB")


if __name__ == "__main__":
    main()
