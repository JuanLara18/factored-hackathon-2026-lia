"""Narración (ElevenLabs o Gemini TTS) y montaje del video con ffmpeg. Uso: python montar.py [voz|montar|todo]"""

import json
import os
import subprocess
import sys
import urllib.request
import wave
from pathlib import Path

import imageio_ffmpeg

AQUI = Path(__file__).parent
FF = imageio_ffmpeg.get_ffmpeg_exe()
AUDIO = AQUI / "audio"
SEG = AQUI / "seg"
AUDIO.mkdir(exist_ok=True)
SEG.mkdir(exist_ok=True)
LLAVE = Path("G:/My Drive/Professional/Hackathons/Factored_2026/API.txt")

# (id, fuente, narración). fuente: "slide:N" o "clip"
GUION = [
    ("01", "slide:1", "Most teams would build a chatbot. We built a bank. LATAM Bank: a bank that keeps its word, by design."),
    ("02", "slide:2", "Here is the promise banks break every day. A customer sees a charge they never made, and waits thirty-seven hours for a first answer. Fraud moves in minutes. Trust is lost in hours."),
    ("03", "slide:3", "So we ran this project like a bank. A presidency, five vice presidencies, and an independent audit. Twenty-one research studies. Thirty-four recorded decisions. Governance challenged the design, and audit reviewed it cold."),
    ("04", "clip", "This is the result, live. Camila opens a charge she does not recognize, and tells Lía. The server pins the transaction, not the model. In seconds, Lía finds it and proposes a claim. And nothing happens until Camila says yes, on screen."),
    ("05", "clip", "She asks about the bank's policy. Lía answers from the source, and cites the rule. She asks for more credit. Lía says no, honestly, and never invents an answer. Every reply is grounded in the bank's own rules."),
    ("06", "clip", "She wants a person. One click. The expert receives her whole story: what she asked, what was verified, what was done, and what is still open. An AI copilot drafts the reply, and the expert edits and sends it. Camila never repeats herself."),
    ("07", "clip", "And in Portuguese, the same care."),
    ("08", "slide:4", "These are five promises a bank can actually keep. They are enforced in code and versioned policy, not in a prompt. No prompt injection can break them."),
    ("09", "slide:5", "Under the hood, a Gemini agent with typed tools runs on Google Cloud. Policy lives as versioned code. Answers are retrieved, not remembered. Nineteen million rows flow through tested data layers in BigQuery. And every model is measured against a baseline."),
    ("10", "slide:6", "Then we tried to break it. On a fresh test set, frozen before we built the latest features, the assistant passes eighty-nine percent of runs, against seventy-two for a rules engine. Zero actions without approval. Zero missed handoffs. And one real flaw, which we found and published. This is what changes when a bank keeps its word. LATAM Bank. Live today."),
]


def correr(args):
    r = subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", *args], capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(r.stderr[-1500:])


def duracion(ruta):
    r = subprocess.run([FF, "-hide_banner", "-i", str(ruta)], capture_output=True, text=True)
    linea = next(x for x in r.stderr.splitlines() if "Duration:" in x)
    h, m, s = linea.split("Duration:")[1].split(",")[0].strip().split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


# Dos voces: la narradora cuenta la historia y una segunda voz acompaña el producto en vivo.
NARRADORA = ["XrExE9yKIg1WjnnlVkGX", "EXAVITQu4vr4xnSDxMaL", "21m00Tcm4TlvDq8ikWAM"]  # Matilda, Sarah, Rachel
GUIA = ["nPczCjzI2devNBz1zQrb", "iP95p4xoKVk53GoZ742B", "JBFqnCBsd6RMkjVDRZzb"]  # Brian, Chris, George
EN_VIVO = {"04", "05", "06", "07"}


def voz_elevenlabs(texto, destino, llave, voces):
    cuerpo = {
        "text": texto,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.38, "similarity_boost": 0.8, "style": 0.35, "use_speaker_boost": True},
    }
    ultimo = None
    for voz in voces:
        req = urllib.request.Request(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voz}?output_format=mp3_44100_128",
            data=json.dumps(cuerpo).encode(),
            method="POST",
            headers={"xi-api-key": llave, "Content-Type": "application/json"},
        )
        try:
            destino.write_bytes(urllib.request.urlopen(req, timeout=120).read())
            return voz
        except Exception as error:  # voz no disponible en la cuenta: se prueba la siguiente
            ultimo = error
    raise ultimo


def voz_gemini(texto, destino):
    from google import genai
    from google.genai import types

    cliente = genai.Client(vertexai=True, project="latam-bank-hackaton-2026", location="global")
    r = cliente.models.generate_content(
        model="gemini-2.5-flash-preview-tts",
        contents="Read this as a calm, confident product narrator: " + texto,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Charon"))),
        ),
    )
    pcm = r.candidates[0].content.parts[0].inline_data.data
    wav = destino.with_suffix(".wav")
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(24000)
        w.writeframes(pcm)
    correr(["-i", str(wav), "-ar", "44100", "-b:a", "128k", str(destino)])
    wav.unlink()


def hacer_voz():
    llave = LLAVE.read_text(encoding="utf-8").strip() if LLAVE.exists() else None
    for ident, _, texto in GUION:
        destino = AUDIO / f"{ident}.mp3"
        if destino.exists():
            continue
        if llave:
            usada = voz_elevenlabs(texto, destino, llave, GUIA if ident in EN_VIVO else NARRADORA)
            print('   voz', usada, flush=True)
        else:
            voz_gemini(texto, destino)
        print("voz", ident, round(duracion(destino), 1), "s", "elevenlabs" if llave else "gemini", flush=True)


V = "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=0B1F2A,fps=30,format=yuv420p"


def crudo(carpeta):
    return next((AQUI / carpeta).glob("*.webm"))


CHAT = "crop=1280:720:320:180,"  # acerca la conversación: el panel del asistente vive a la derecha


def recorte(carpeta, inicio, fin, destino, acercar=False):
    filtro = (CHAT if acercar else "") + V
    correr(["-ss", f"{max(0, inicio):.2f}", "-to", f"{fin:.2f}", "-i", str(crudo(carpeta)), "-an", "-vf", filtro, "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", str(destino)])


def unir(partes, destino):
    lista = destino.with_suffix(".txt")
    lista.write_text("".join(f"file '{p.as_posix()}'\n" for p in partes), encoding="utf-8")
    correr(["-f", "concat", "-safe", "0", "-i", str(lista), "-c", "copy", str(destino)])


def clips():
    m = json.loads((AQUI / "marcas.json").read_text(encoding="utf-8"))
    c, e, q = m["cliente"], m["experto"], m["pt"]
    tmp = AQUI / "tmp"
    tmp.mkdir(exist_ok=True)
    recorte("crudo_cliente", c["banca_lista"] + 0.8, c["asistente_abierto"] + 3.5, tmp / "04a.mp4")
    recorte("crudo_cliente", c["aprobacion_visible"] - 5.0, c["reclamo_abierto"] + 3.5, tmp / "04b.mp4", acercar=True)
    unir([tmp / "04a.mp4", tmp / "04b.mp4"], tmp / "04.mp4")
    recorte("crudo_cliente", c["reclamo_abierto"] + 4.3, c["respuesta_cupo"] + 4.0, tmp / "05.mp4", acercar=True)
    recorte("crudo_cliente", c["pide_persona"] - 0.8, c["esperando_persona"] + 2.0, tmp / "06a.mp4", acercar=True)
    recorte("crudo_experto", e["paquete"] - 0.8, e["paquete"] + 8.7, tmp / "06b.mp4")
    recorte("crudo_experto", e["tomado"] + 0.5, e["enviado"] + 1.3, tmp / "06c.mp4")
    recorte("crudo_cliente", c["mensaje_del_experto_enviado"] + 0.4, c["fin"], tmp / "06d.mp4", acercar=True)
    unir([tmp / "06a.mp4", tmp / "06b.mp4", tmp / "06c.mp4", tmp / "06d.mp4"], tmp / "06.mp4")
    recorte("crudo_pt", q["respuesta"] - 1.5, q["respuesta"] + 3.5, tmp / "07.mp4", acercar=True)
    return tmp


TOPE = 172.0  # el video no puede pasar de tres minutos


def ajustar_ritmo():
    """Si la narración entera no cabe, se acelera toda por igual (sin cambiar el tono)."""
    total = sum(duracion(AUDIO / f"{i}.mp3") + 0.45 for i, _, _ in GUION)
    factor = max(1.0, total / TOPE)
    destino = AQUI / "audio_final"
    destino.mkdir(exist_ok=True)
    for ident, _, _ in GUION:
        correr(["-i", str(AUDIO / f"{ident}.mp3"), "-filter:a", f"atempo={factor:.4f}", "-b:a", "160k", str(destino / f"{ident}.mp3")])
    print("narración", round(total, 1), "s; ritmo x", round(factor, 3), flush=True)
    return destino


def montar():
    tmp = clips()
    partes = []
    audios = ajustar_ritmo()
    for ident, fuente, _ in GUION:
        audio = audios / f"{ident}.mp3"
        d = duracion(audio) + 0.45  # respiro entre frases
        salida = SEG / f"{ident}.mp4"
        desv = f"fade=t=in:st=0:d=0.3,fade=t=out:st={d - 0.3:.2f}:d=0.3"
        if fuente.startswith("slide:"):
            png = AQUI / "slides3" / f"Slide{fuente.split(':')[1]}.PNG"
            n = int(d * 30)
            zoom = f"scale=7680:4320:flags=lanczos,zoompan=z='1.0+0.05*on/{n}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={n}:s=1920x1080:fps=30,format=yuv420p,{desv}"
            correr(["-loop", "1", "-i", str(png), "-i", str(audio), "-filter_complex", f"[0:v]{zoom}[v];[1:a]apad[a]", "-map", "[v]", "-map", "[a]", "-t", f"{d:.2f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-c:a", "aac", "-b:a", "160k", "-ar", "44100", str(salida)])
        else:
            clip = tmp / f"{ident}.mp4"
            dc = duracion(clip)
            d = max(d, dc / 1.6 + 0.2)  # nunca más de 1,6 veces la velocidad real: se deja ver el producto
            desv = f"fade=t=in:st=0:d=0.3,fade=t=out:st={d - 0.3:.2f}:d=0.3"
            factor = d / dc  # <1 acelera, >1 frena; no se frena más de 1,15: se congela el último cuadro
            factor_v = min(factor, 1.15)
            relleno = max(0.0, d - dc * factor_v) + 0.1
            vf = f"setpts={factor_v:.4f}*PTS,tpad=stop_mode=clone:stop_duration={relleno:.2f},fps=30,format=yuv420p,{desv}"
            correr(["-i", str(clip), "-i", str(audio), "-filter_complex", f"[0:v]{vf}[v];[1:a]apad[a]", "-map", "[v]", "-map", "[a]", "-t", f"{d:.2f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-c:a", "aac", "-b:a", "160k", "-ar", "44100", str(salida)])
            print("clip", ident, "audio", round(d, 1), "clip", round(dc, 1), "factor", round(factor, 2), flush=True)
        partes.append(salida)
    final = AQUI / "LATAM_Bank_video_pitch.mp4"
    lista = AQUI / "final.txt"
    lista.write_text("".join(f"file '{p.as_posix()}'\n" for p in partes), encoding="utf-8")
    correr(["-f", "concat", "-safe", "0", "-i", str(lista), "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(final)])
    print("final", round(duracion(final), 1), "s", round(final.stat().st_size / 1e6, 1), "MB")


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "todo"
    if modo in ("voz", "todo"):
        hacer_voz()
    if modo in ("montar", "todo"):
        montar()
