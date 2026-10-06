"""Montaje con la conversación en pantalla dividida y rótulos que resaltan lo que se demuestra."""

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import generar_video as montar

AQUI = Path(__file__).parent
TMP = AQUI / "tmp2"
TMP.mkdir(exist_ok=True)
INK, GREEN, MINT, AMBER, WHITE, SOFT = "#0B1F2A", "#0B6E4F", "#9FE0C4", "#F2A541", "#FFFFFF", "#B8C6CC"
ESCALA = 1.0  # el video guarda la página a tamaño real (1280x720) en la esquina superior izquierda
ALTO_PANEL = 980


def fuente(tam, negrita=False):
    return ImageFont.truetype(r"C:\Windows\Fonts\calibrib.ttf" if negrita else r"C:\Windows\Fonts\calibri.ttf", tam)


def envolver(dibujo, texto, f, ancho):
    lineas, actual = [], ""
    for palabra in texto.split():
        prueba = (actual + " " + palabra).strip()
        if dibujo.textlength(prueba, font=f) <= ancho:
            actual = prueba
        else:
            lineas.append(actual)
            actual = palabra
    return lineas + [actual]


def fondo():
    im = Image.new("RGB", (1920, 1080), INK)
    d = ImageDraw.Draw(im)
    d.ellipse((-420, 560, 620, 1600), fill="#0E2A38")
    d.ellipse((1380, -520, 2300, 400), fill="#0E2A38")
    d.text((100, 70), "LATAM Bank", font=fuente(34, True), fill=WHITE)
    d.rounded_rectangle((300, 66, 506, 112), radius=23, fill=GREEN)
    d.ellipse((316, 82, 332, 98), fill=MINT)
    d.text((342, 73), "LIVE PRODUCT", font=fuente(22, True), fill=WHITE)
    ruta = TMP / "fondo.png"
    im.save(ruta)
    return ruta


def rotulo(nombre, etiqueta, titular, apoyo, color=MINT):
    im = Image.new("RGBA", (1060, 760), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((0, 0), etiqueta.upper(), font=fuente(30, True), fill=color)
    y = 62
    f = fuente(86, True)
    for linea in envolver(d, titular, f, 1020):
        d.text((0, y), linea, font=f, fill=WHITE)
        y += 96
    y += 26
    f = fuente(36)
    for linea in envolver(d, apoyo, f, 960):
        d.text((0, y), linea, font=f, fill=SOFT)
        y += 48
    ruta = TMP / f"rot_{nombre}.png"
    im.save(ruta)
    return ruta


def barra(nombre, etiqueta, texto):
    im = Image.new("RGBA", (1920, 150), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((70, 18, 1850, 132), radius=26, fill=(11, 31, 42, 235))
    ancho = int(d.textlength(etiqueta.upper(), font=fuente(26, True))) + 44
    d.rounded_rectangle((100, 48, 100 + ancho, 102), radius=27, fill=GREEN)
    d.text((122, 60), etiqueta.upper(), font=fuente(26, True), fill=WHITE)
    d.text((100 + ancho + 30, 52), texto, font=fuente(40, True), fill=WHITE)
    ruta = TMP / f"bar_{nombre}.png"
    im.save(ruta)
    return ruta


X264 = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-r", "30", "-pix_fmt", "yuv420p", "-an"]


def panel(carpeta, inicio, fin, caja, rot, destino):
    """Conversación a la derecha, rótulo a la izquierda."""
    x, y, w, h = (round(v * ESCALA) for v in caja)
    w, h = w - w % 2, h - h % 2
    ancho = round(w * ALTO_PANEL / h / 2) * 2
    px = 1920 - ancho - 110
    f = (
        f"[1:v]crop={w}:{h}:{x}:{y},scale={ancho}:{ALTO_PANEL}:flags=lanczos,pad={ancho + 12}:{ALTO_PANEL + 12}:6:6:color=0x9FE0C4[p];"
        f"[0:v][p]overlay={px - 6}:{(1080 - ALTO_PANEL) // 2 - 6}[a];[a][2:v]overlay=100:230,fade=t=in:st=0:d=0.25[v]"
    )
    d = fin - inicio
    montar.correr(["-loop", "1", "-t", f"{d:.2f}", "-i", str(FONDO), "-ss", f"{max(0, inicio):.2f}", "-t", f"{d:.2f}", "-i", str(montar.crudo(carpeta)), "-loop", "1", "-t", f"{d:.2f}", "-i", str(rot), "-filter_complex", f, "-map", "[v]", "-t", f"{d:.2f}", *X264, str(destino)])


def completo(carpeta, inicio, fin, bar, destino, acercar=None):
    """Página completa con una barra inferior; `acercar` = (x, y, ancho) en píxeles del video para un acercamiento."""
    d = fin - inicio
    corte = "crop=1280:720:0:0," + (f"crop={acercar[2]}:{round(acercar[2] * 9 / 16)}:{acercar[0]}:{acercar[1]}," if acercar else "")
    f = f"[0:v]{corte}scale=1920:1080:flags=lanczos[b];[b][1:v]overlay=0:915,fade=t=in:st=0:d=0.25[v]"
    montar.correr(["-ss", f"{max(0, inicio):.2f}", "-t", f"{d:.2f}", "-i", str(montar.crudo(carpeta)), "-loop", "1", "-t", f"{d:.2f}", "-i", str(bar), "-filter_complex", f, "-map", "[v]", "-t", f"{d:.2f}", *X264, str(destino)])


def clips():
    m = json.loads((AQUI / "marcas2.json").read_text(encoding="utf-8"))
    c, e, q, caja = m["cliente"], m["experto"], m["pt"], m["panel"]
    dx, dy, dw, dh = (v * ESCALA for v in m["dialogo"])
    # acercamiento a la confirmación: un recuadro 16:9 de 1200 px centrado en el diálogo
    ax = int(min(max(dx + dw / 2 - 400, 0), 1280 - 800))
    ay = int(min(max(dy + dh / 2 - 225, 0), 720 - 450))

    # 04: el cargo, la conversación, la confirmación y el resultado
    completo("g2_cliente", c["banca_lista"] + 0.6, c["asistente_abierto"] + 0.4, barra("banca", "Online banking", "Camila opens a charge she does not recognize"), TMP / "04a.mp4")
    panel("g2_cliente", max(c["asistente_abierto"] + 0.4, c["aprobacion_visible"] - 7.0), c["aprobacion_visible"] - 0.1, caja, rotulo("encuentra", "Grounded in data", "Lía finds the charge", "The server pins the transaction. The model only reads it."), TMP / "04b.mp4")
    completo("g2_cliente", c["aprobacion_visible"] - 0.1, c["aprobado"] + 0.5, barra("si", "Promise 1", "Nothing happens until Camila says yes"), TMP / "04c.mp4", acercar=(ax, ay, 800))
    panel("g2_cliente", c["aprobado"] + 0.5, c["reclamo_abierto"] + 3.8, caja, rotulo("abierto", "Only what was verified", "Claim opened", "Lía reports what the system actually did, and what comes next."), TMP / "04d.mp4")
    montar.unir([TMP / f"04{x}.mp4" for x in "abcd"], TMP / "04.mp4")

    # 05: política con fuente y abstención honesta
    panel("g2_cliente", c["pregunta_politica"] - 3.6, c["respuesta_politica"] + 5.2, caja, rotulo("fuente", "Promise 4", "Answers with a source", "The bank's policy, cited by rule. Retrieved, not remembered."), TMP / "05a.mp4")
    panel("g2_cliente", c["pregunta_cupo"] - 3.4, c["respuesta_cupo"] + 4.2, caja, rotulo("honesta", "Honest limits", "It never invents an answer", "Out of scope? Lía says so, and offers what she can do.", AMBER), TMP / "05b.mp4")
    montar.unir([TMP / "05a.mp4", TMP / "05b.mp4"], TMP / "05.mp4")

    # 06: una persona, con la historia completa
    panel("g2_cliente", c["pide_persona"] - 0.8, c["esperando_persona"] + 2.2, caja, rotulo("persona", "Promise 3", "A person, whenever you ask", "One click. No questions asked."), TMP / "06a.mp4")
    completo("g2_experto", e["paquete"] + 0.3, e["paquete"] + 6.8, barra("paquete", "Expert console", "The whole story, verified, in one package"), TMP / "06b.mp4")
    completo("g2_experto", e["pide_borrador"] - 0.6, e["enviado"] + 1.2, barra("copiloto", "AI copilot", "It drafts. The human edits and sends"), TMP / "06c.mp4")
    panel("g2_cliente", c["mensaje_del_experto_enviado"] + 0.4, c["fin"] - 0.2, caja, rotulo("hilo", "Same conversation", "Camila never repeats herself", "The expert answers in the same thread."), TMP / "06d.mp4")
    montar.unir([TMP / f"06{x}.mp4" for x in "abcd"], TMP / "06.mp4")

    # 07: portugués
    panel("g2_pt", q["respuesta"] - 2.2, q["respuesta"] + 4.5, m.get("panel_pt", caja), rotulo("pt", "Portuguese", "The same care", "Em português, para clientes de toda a região."), TMP / "07.mp4")
    return TMP


FONDO = fondo()
montar.clips = clips

if __name__ == "__main__":
    montar.montar()
