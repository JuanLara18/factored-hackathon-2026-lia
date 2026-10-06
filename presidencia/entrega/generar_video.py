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
    ("01", "slide:1", "LATAM Bank. An AI-first way to handle unrecognized card charges, in Spanish and Portuguese."),
    ("02", "slide:2", "We started from the data. Across sixty-seven thousand complaints, unrecognized charges are the largest group, and the first answer takes thirty-seven hours. Fraud is contained in minutes, so we built one focused workflow: dispute intake."),
    ("03", "clip", "This is the live system. The customer opens a charge in online banking and tells Lía, our assistant, that it is not theirs. The server pins the transaction, not the model. Lía reads the data and proposes a claim, and nothing happens until the customer approves on screen."),
    ("04", "clip", "Policy questions are answered only from a retrieved source, with the rule cited. That retriever is a learned component: ninety percent accuracy, against fifty-two for a keyword baseline. Out of scope, like a credit limit, Lía abstains and never invents eligibility."),
    ("05", "clip", "A human is always one click away. The expert receives a package with the request, the verified facts, the actions taken, and the rule that triggered the handoff. An AI copilot drafts the reply. The expert edits it and sends it, in the same conversation."),
    ("06", "clip", "And the same assistant answers in Portuguese, for customers across the region. The data has no Brazilian accounts, and we say so."),
    ("07", "slide:3", "Behind it, the model understands and writes, and code decides. Permissions, approvals and policy live outside the prompt, in versioned rules. A prompt injection cannot open a claim or reach another customer's data."),
    ("08", "slide:4", "The data runs through tested layers in BigQuery, with contracts and lineage. We evaluated three learned components against baselines. One clearly wins. One helps a little. And one has no signal, so we report it, and it abstains."),
    ("09", "slide:5", "We froze a new held-out set before building the latest features, and ran it once. The agent passes eighty-nine percent of runs. Simple rules tie on the core dispute flow, and fall to thirty-eight percent on policy questions, follow-up and multi-request conversations. One real unsafe outcome in one hundred twenty-nine runs: the agent repeated card digits the customer had typed. We report it."),
    ("10", "slide:6", "It is live on Google Cloud today, with tracing, retention and alerts. And we are clear about what is still missing. Thank you."),
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


def voz_elevenlabs(texto, destino, llave):
    voz = os.environ.get("VOZ_ID", "JBFqnCBsd6RMkjVDRZzb")  # George, voz prefabricada
    cuerpo = {"text": texto, "model_id": "eleven_multilingual_v2", "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}}
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voz}?output_format=mp3_44100_128",
        data=json.dumps(cuerpo).encode(),
        method="POST",
        headers={"xi-api-key": llave, "Content-Type": "application/json"},
    )
    destino.write_bytes(urllib.request.urlopen(req, timeout=120).read())


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
            voz_elevenlabs(texto, destino, llave)
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
    recorte("crudo_cliente", c["banca_lista"] + 0.8, c["asistente_abierto"] + 3.5, tmp / "03a.mp4")
    recorte("crudo_cliente", c["aprobacion_visible"] - 5.0, c["reclamo_abierto"] + 3.5, tmp / "03b.mp4", acercar=True)
    unir([tmp / "03a.mp4", tmp / "03b.mp4"], tmp / "03.mp4")
    recorte("crudo_cliente", c["reclamo_abierto"] + 4.3, c["respuesta_cupo"] + 4.0, tmp / "04.mp4", acercar=True)
    recorte("crudo_cliente", c["pide_persona"] - 0.8, c["esperando_persona"] + 2.0, tmp / "05a.mp4", acercar=True)
    recorte("crudo_experto", e["paquete"] - 0.8, e["paquete"] + 8.7, tmp / "05b.mp4")
    recorte("crudo_experto", e["tomado"] + 0.5, e["enviado"] + 1.3, tmp / "05c.mp4")
    recorte("crudo_cliente", c["mensaje_del_experto_enviado"] + 0.4, c["fin"], tmp / "05d.mp4", acercar=True)
    unir([tmp / "05a.mp4", tmp / "05b.mp4", tmp / "05c.mp4", tmp / "05d.mp4"], tmp / "05.mp4")
    recorte("crudo_pt", q["pregunta"] - 3.2, q["respuesta"] + 3.0, tmp / "06.mp4", acercar=True)
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
            png = AQUI / "slides" / f"Slide{fuente.split(':')[1]}.PNG"
            n = int(d * 30)
            zoom = f"scale=2880:1620,zoompan=z='min(1.0+0.00018*on,1.06)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={n}:s=1920x1080:fps=30,format=yuv420p,{desv}"
            correr(["-loop", "1", "-i", str(png), "-i", str(audio), "-filter_complex", f"[0:v]{zoom}[v];[1:a]apad=pad_dur=0.45[a]", "-map", "[v]", "-map", "[a]", "-t", f"{d:.2f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-c:a", "aac", "-b:a", "160k", "-ar", "44100", str(salida)])
        else:
            clip = tmp / f"{ident}.mp4"
            dc = duracion(clip)
            factor = d / dc  # <1 acelera, >1 frena; no se frena más de 1,15: se congela el último cuadro
            factor_v = min(factor, 1.15)
            relleno = max(0.0, d - dc * factor_v) + 0.1
            vf = f"setpts={factor_v:.4f}*PTS,tpad=stop_mode=clone:stop_duration={relleno:.2f},fps=30,format=yuv420p,{desv}"
            correr(["-i", str(clip), "-i", str(audio), "-filter_complex", f"[0:v]{vf}[v];[1:a]apad=pad_dur=0.45[a]", "-map", "[v]", "-map", "[a]", "-t", f"{d:.2f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-c:a", "aac", "-b:a", "160k", "-ar", "44100", str(salida)])
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
