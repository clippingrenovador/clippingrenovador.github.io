"""Genera og.png (vista previa al compartir por WhatsApp): CLIPPING RENOVADOR con el Sol de Mayo detras.

Usa Archivo si esta en fuentes/ (el workflow la descarga); si no, una sans del sistema.
"""
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
from tarjeta import fuente as fuente_marca  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
E = 2  # se dibuja al doble y se reduce, para bordes suaves
W, H = 1200 * E, 630 * E

CELESTE = (116, 172, 223)
CELESTE_OSC = (52, 118, 182)
ORO = (200, 150, 30)
ORO_OSC = (150, 105, 10)
SOL = (236, 196, 92)
SOL_CLARO = (246, 224, 160)
BLANCO = (255, 255, 255)


def fuente(tam, peso=800, ancho=None):
    if (RAIZ / "fuentes" / "Archivo.ttf").exists():
        return fuente_marca("Archivo.ttf", tam, peso, ancho)
    for ruta in ("/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(ruta, tam)
        except OSError:
            pass
    return ImageFont.load_default()


def rayo_recto(cx, cy, ang, r0, r1, ancho):
    a = math.radians(ang)
    p = a + math.pi / 2
    base1 = (cx + r0 * math.cos(a) + ancho * math.cos(p), cy + r0 * math.sin(a) + ancho * math.sin(p))
    base2 = (cx + r0 * math.cos(a) - ancho * math.cos(p), cy + r0 * math.sin(a) - ancho * math.sin(p))
    punta = (cx + r1 * math.cos(a), cy + r1 * math.sin(a))
    return [base1, punta, base2]


def rayo_ondulado(cx, cy, ang, r0, r1, ancho, ondas=2.5, amp=0.06):
    a = math.radians(ang)
    izq, der = [], []
    pasos = 60
    for i in range(pasos + 1):
        t = i / pasos
        r = r0 + (r1 - r0) * t
        desvio = math.sin(t * ondas * 2 * math.pi) * amp * (r1 - r0) * (0.3 + 0.7 * t)
        ang_t = a + desvio / r
        x, y = cx + r * math.cos(ang_t), cy + r * math.sin(ang_t)
        w = ancho * (1 - t) ** 0.9
        p = ang_t + math.pi / 2
        izq.append((x + w * math.cos(p), y + w * math.sin(p)))
        der.append((x - w * math.cos(p), y - w * math.sin(p)))
    return izq + der[::-1]


def sol_de_mayo(d, cx, cy, radio, color, color_linea):
    """Sol de 32 rayos alternados rectos y flamigeros, con rostro."""
    nucleo = radio * 0.36
    for i in range(32):
        ang = i * 360 / 32 - 90
        if i % 2 == 0:
            d.polygon(rayo_recto(cx, cy, ang, nucleo * 0.9, radio, nucleo * 0.16), fill=color)
        else:
            d.polygon(rayo_ondulado(cx, cy, ang, nucleo * 0.9, radio * 0.86, nucleo * 0.13), fill=color)
    d.ellipse([cx - nucleo, cy - nucleo, cx + nucleo, cy + nucleo], fill=color)
    # rostro
    lw = max(2, int(nucleo * 0.045))
    d.ellipse([cx - nucleo * 0.93, cy - nucleo * 0.93, cx + nucleo * 0.93, cy + nucleo * 0.93], outline=color_linea, width=lw)
    for s in (-1, 1):
        ox = cx + s * nucleo * 0.36
        oy = cy - nucleo * 0.12
        # ceja
        d.arc([ox - nucleo * 0.24, oy - nucleo * 0.30, ox + nucleo * 0.24, oy + nucleo * 0.02], 200, 340, fill=color_linea, width=lw)
        # ojo
        d.arc([ox - nucleo * 0.17, oy - nucleo * 0.07, ox + nucleo * 0.17, oy + nucleo * 0.13], 190, 350, fill=color_linea, width=lw)
        d.ellipse([ox - nucleo * 0.05, oy - nucleo * 0.03, ox + nucleo * 0.05, oy + nucleo * 0.07], fill=color_linea)
        # mejilla
        d.arc([ox - nucleo * 0.16, oy + nucleo * 0.26, ox + nucleo * 0.16, oy + nucleo * 0.46], 20, 160, fill=color_linea, width=lw)
    # nariz
    d.line([(cx, cy - nucleo * 0.18), (cx - nucleo * 0.07, cy + nucleo * 0.22), (cx + nucleo * 0.07, cy + nucleo * 0.24)], fill=color_linea, width=lw, joint="curve")
    # boca
    d.arc([cx - nucleo * 0.30, cy + nucleo * 0.22, cx + nucleo * 0.30, cy + nucleo * 0.58], 20, 160, fill=color_linea, width=lw)
    d.line([(cx - nucleo * 0.2, cy + nucleo * 0.47), (cx + nucleo * 0.2, cy + nucleo * 0.47)], fill=color_linea, width=lw)


def texto_centrado(d, y, texto, f, color, borde=0, color_borde=BLANCO, espaciado=0):
    anchos = [d.textlength(c, font=f) for c in texto]
    total = sum(anchos) + espaciado * (len(texto) - 1)
    x = (W - total) / 2
    for c, a in zip(texto, anchos):
        d.text((x, y), c, font=f, fill=color, stroke_width=borde, stroke_fill=color_borde)
        x += a + espaciado


def main():
    img = Image.new("RGB", (W, H), BLANCO)
    d = ImageDraw.Draw(img)

    # Franjas celestes arriba y abajo, como la bandera
    franja = int(H * 0.12)
    d.rectangle([0, 0, W, franja], fill=CELESTE)
    d.rectangle([0, H - franja, W, H], fill=CELESTE)
    d.rectangle([0, franja, W, franja + 4 * E], fill=ORO)
    d.rectangle([0, H - franja - 4 * E, W, H - franja], fill=ORO)

    # Sol de Mayo detras del titulo
    capa = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sol_de_mayo(ImageDraw.Draw(capa), W / 2, H / 2, H * 0.37, SOL_CLARO + (255,), (226, 184, 90, 255))
    img.paste(capa, (0, 0), capa)
    d = ImageDraw.Draw(img)

    # Titulo
    f = fuente(150 * E, 900, 100)
    texto_centrado(d, H * 0.235, "CLIPPING", f, CELESTE_OSC, borde=5 * E, espaciado=6 * E)
    texto_centrado(d, H * 0.49, "RENOVADOR", f, ORO_OSC, borde=5 * E, espaciado=6 * E)

    # Bajada en la franja inferior
    fb = fuente(26 * E, 600)
    texto_centrado(d, H - franja + (franja - 26 * E) / 2 - 4 * E,
                   "Sergio Massa y el Frente Renovador en los medios, a las 6, 14 y 22 h", fb, BLANCO)
    fa = fuente(24 * E, 700)
    texto_centrado(d, (franja - 24 * E) / 2 - 4 * E, "Monitoreo de prensa", fa, BLANCO, espaciado=2 * E)

    img = img.resize((W // E, H // E), Image.LANCZOS)
    img.save(RAIZ / "og.png", optimize=True)
    print("og.png listo")


if __name__ == "__main__":
    main()
