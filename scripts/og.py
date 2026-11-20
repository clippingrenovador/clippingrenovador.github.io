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


AZUL = (24, 140, 232)
NEGRO = (14, 18, 26)
CREMA = (244, 240, 228)


def sol_chico(d, cx, cy, r, color):
    for k in range(16):
        a = math.radians(k * 22.5)
        d.polygon(rayo_recto(cx, cy, k * 22.5, r * 0.5, r, r * 0.16), fill=color)
    d.ellipse([cx - r * 0.55, cy - r * 0.55, cx + r * 0.55, cy + r * 0.55], fill=color)


def sol_grande(d, cx, cy, r, color):
    """Sol de 24 rayos alternados largos y cortos."""
    for k in range(24):
        largo = r if k % 2 == 0 else r * 0.78
        d.polygon(rayo_recto(cx, cy, k * 15, r * 0.45, largo, r * 0.11), fill=color)
    d.ellipse([cx - r * 0.5, cy - r * 0.5, cx + r * 0.5, cy + r * 0.5], fill=color)


def fondo_semitono(W, H, semilla=1945, paso_px=12):
    """Fondo azul y negro con trama de semitono y grano, como las piezas de Jovenes FR."""
    import numpy as np
    rng = np.random.default_rng(semilla)
    manchas = Image.fromarray((rng.random((5, 9)) * 255).astype("uint8")).resize((W, H), Image.BICUBIC)
    m = np.asarray(manchas, dtype=float) / 255
    yy, xx = np.mgrid[0:H, 0:W]
    vin = np.hypot((xx - W / 2) / (W / 2), (yy - H / 2) / (H / 2)) / 1.41
    tono = np.clip(0.02 + 0.42 * m ** 1.4 + 0.75 * vin ** 2.4, 0, 1)
    img = Image.new("RGB", (W, H), AZUL)
    d = ImageDraw.Draw(img)
    paso = paso_px * E
    c, s_ = math.cos(math.radians(45)), math.sin(math.radians(45))
    rango = int(math.hypot(W, H) / paso) + 2
    for i in range(-rango, rango):
        for k in range(-rango, rango):
            x = W / 2 + (i * c - k * s_) * paso
            y = H / 2 + (i * s_ + k * c) * paso
            if -paso < x < W + paso and -paso < y < H + paso:
                t = tono[min(H - 1, max(0, int(y))), min(W - 1, max(0, int(x)))]
                r = paso * 0.78 * t ** 0.85
                if r > 0.4 * E:
                    d.ellipse([x - r, y - r, x + r, y + r], fill=NEGRO)
    arr = np.asarray(img, dtype=float)
    arr += rng.normal(0, 9, (H, W, 1))
    return Image.fromarray(np.clip(arr, 0, 255).astype("uint8"))


def cabecera():
    """Textura para la cabecera del sitio (sin texto)."""
    img = fondo_semitono(1280 * E, 600 * E, semilla=1972, paso_px=10)
    img = img.resize((1280, 600), Image.LANCZOS)
    img.save(RAIZ / "cabecera.jpg", quality=60, optimize=True, progressive=True)
    print("cabecera.jpg listo", (RAIZ / "cabecera.jpg").stat().st_size // 1024, "KB")


def main():
    import numpy as np
    rng = np.random.default_rng(1945)
    # Campo de tono: manchas suaves tipo foto de archivo + viñeta oscura en los bordes
    manchas = Image.fromarray((rng.random((5, 9)) * 255).astype("uint8")).resize((W, H), Image.BICUBIC)
    m = np.asarray(manchas, dtype=float) / 255
    yy, xx = np.mgrid[0:H, 0:W]
    vin = np.hypot((xx - W / 2) / (W / 2), (yy - H / 2) / (H / 2)) / 1.41
    tono = np.clip(0.02 + 0.42 * m ** 1.4 + 0.75 * vin ** 2.4, 0, 1)

    # Semitono negro sobre azul, trama a 45 grados
    img = Image.new("RGB", (W, H), AZUL)
    d = ImageDraw.Draw(img)
    paso = 12 * E
    c, s_ = math.cos(math.radians(45)), math.sin(math.radians(45))
    rango = int(math.hypot(W, H) / paso) + 2
    for i in range(-rango, rango):
        for k in range(-rango, rango):
            x = W / 2 + (i * c - k * s_) * paso
            y = H / 2 + (i * s_ + k * c) * paso
            if -paso < x < W + paso and -paso < y < H + paso:
                t = tono[min(H - 1, max(0, int(y))), min(W - 1, max(0, int(x)))]
                r = paso * 0.78 * t ** 0.85
                if r > 0.4 * E:
                    d.ellipse([x - r, y - r, x + r, y + r], fill=NEGRO)

    # Grano de impresion
    arr = np.asarray(img, dtype=float)
    arr += rng.normal(0, 9, (H, W, 1))
    img = Image.fromarray(np.clip(arr, 0, 255).astype("uint8"))
    d = ImageDraw.Draw(img)

    # Titulo crema entre filetes dobles, como las piezas de Jovenes FR
    margen = 70 * E
    ancho_util = W - 2 * margen

    def tinta(texto, f, esp):
        """Ancho real de tinta y desplazamiento izquierdo del texto con espaciado esp."""
        x, izq, der = 0, None, 0
        for k, c in enumerate(texto):
            b = d.textbbox((x, 0), c, font=f)
            if izq is None:
                izq = b[0]
            der = b[2]
            x += d.textlength(c, font=f) + esp
        return der - izq, izq

    def dibujar(texto, f, esp, x_ini, y):
        _, izq = tinta(texto, f, esp)
        x = x_ini - izq
        for c in texto:
            d.text((x, y), c, font=f, fill=CREMA)
            x += d.textlength(c, font=f) + esp

    # Tamaño: RENOVADOR ocupa exactamente el ancho de los filetes
    tam = 200
    while tam > 60:
        f = fuente(tam * E, 900, 125)
        if tinta("RENOVADOR", f, 2 * E)[0] <= ancho_util:
            break
        tam -= 2
    w_ren, _ = tinta("RENOVADOR", f, 0)
    esp_ren = (ancho_util - w_ren) / 8
    esp_cli = 2 * E
    w_cli, _ = tinta("CLIPPING", f, esp_cli)

    caja = d.textbbox((0, 0), "RENOVADOR", font=f)
    alto_l = caja[3] - caja[1]
    grosor = 11 * E
    entre_filetes = 9 * E
    aire = alto_l * 0.38
    gap = alto_l * 0.36
    bloque_filetes = 2 * grosor + entre_filetes
    total = 2 * bloque_filetes + 2 * aire + 2 * alto_l + gap
    y = (H - total) / 2

    def filetes(y0):
        d.rectangle([margen, y0, W - margen, y0 + grosor], fill=CREMA)
        d.rectangle([margen, y0 + grosor + entre_filetes, W - margen, y0 + 2 * grosor + entre_filetes], fill=CREMA)

    filetes(y)
    y_cli = y + bloque_filetes + aire
    y_ren = y_cli + alto_l + gap
    dibujar("CLIPPING", f, esp_cli, (W - w_cli) / 2, y_cli - caja[1])
    dibujar("RENOVADOR", f, esp_ren, margen, y_ren - caja[1])
    filetes(y_ren + alto_l + aire)

    # Soles a los costados de CLIPPING, alineados con el inicio y el fin de los filetes
    r_sol = min(alto_l * 0.46, (ancho_util - w_cli) / 2 * 0.36)
    cy = y_cli + alto_l / 2
    sol_grande(d, margen + r_sol, cy, r_sol, CREMA)
    sol_grande(d, W - margen - r_sol, cy, r_sol, CREMA)

    img = img.resize((W // E, H // E), Image.LANCZOS)
    img.save(RAIZ / "og.jpg", quality=62, subsampling=2, optimize=True, progressive=True)
    print("og.jpg listo", (RAIZ / "og.jpg").stat().st_size // 1024, "KB")


if __name__ == "__main__":
    main()
    cabecera()

