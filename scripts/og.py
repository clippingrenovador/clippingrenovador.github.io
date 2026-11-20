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
    # Fondo: degradado azul a celeste, con semitono blanco que crece hacia las esquinas
    img = Image.new("RGB", (W, H))
    px = img.load()
    a, b = (40, 96, 160), CELESTE
    for y in range(H):
        for x in range(0, W):
            t = (x / W) * 0.6 + (y / H) * 0.4
            px[x, y] = tuple(int(a[k] + (b[k] - a[k]) * t) for k in range(3))
    d = ImageDraw.Draw(img)
    paso = 22 * E
    for fila, y in enumerate(range(-paso, H + paso, paso)):
        desplaza = (paso // 2) if fila % 2 else 0
        for x in range(-paso + desplaza, W + paso, paso):
            # distancia al centro, normalizada: los puntos crecen hacia los bordes
            # semitono que nace en la mitad inferior y llega a blanco abajo
            fuerza = min(1.0, max(0.0, (y / H - 0.60) / 0.40)) + max(0.0, 0.18 - y / H) * 1.2
            r = paso * 0.64 * fuerza ** 1.1
            if r > 0.6 * E:
                d.ellipse([x - r, y - r, x + r, y + r], fill=BLANCO)

    # Titulo en blanco con sombra suave
    f = fuente(132 * E, 900, 100)
    sombra = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ds = ImageDraw.Draw(sombra)
    for texto, y in (("CLIPPING", H * 0.16), ("RENOVADOR", H * 0.40)):
        anchos = [ds.textlength(c, font=f) for c in texto]
        total = sum(anchos) + 6 * E * (len(texto) - 1)
        x = (W - total) / 2
        for c, w in zip(texto, anchos):
            ds.text((x + 4 * E, y + 6 * E), c, font=f, fill=(20, 50, 95, 110))
            x += w + 6 * E
    from PIL import ImageFilter
    sombra = sombra.filter(ImageFilter.GaussianBlur(8 * E))
    img.paste(sombra, (0, 0), sombra)
    d = ImageDraw.Draw(img)
    texto_centrado(d, H * 0.16, "CLIPPING", f, BLANCO, espaciado=6 * E)
    texto_centrado(d, H * 0.40, "RENOVADOR", f, BLANCO, espaciado=6 * E)

    img = img.resize((W // E, H // E), Image.LANCZOS)
    img.save(RAIZ / "og.png", optimize=True)
    print("og.png listo")


if __name__ == "__main__":
    main()
