import time
import threading
import fluidsynth
from pynput import keyboard

SOUNDFONT = "/Users/pedronogueira/PUC/micro/Trabalho/GeneralUser-GS/GeneralUser-GS.sf2"

BPM = 120
BEATS_POR_COMPASSO = 4

CANAL_GUITAR = 0

NOTA_FORTE     = 76
NOTA_FRACA     = 77
VELOCITY_FORTE = 110
VELOCITY_FRACA = 70

# Cada tecla dispara duas notas simultâneas (power chord)
# Tom original do riff (G)
MAPA_TECLAS = {
    'a': (55, 62),  # G3 + D4  → G5
    's': (58, 65),  # Bb3 + F4 → Bb5
    'd': (60, 67),  # C4 + G4  → C5
    'f': (61, 68),  # Db4 + Ab4 → Db5
}

# --- Sintetizador ---
fs = fluidsynth.Synth(gain=0.8)
fs.start(driver="coreaudio")

sfid = fs.sfload(SOUNDFONT)
fs.program_select(CANAL_GUITAR, sfid, 0, 29)   # Overdrive Guitar

# --- Teclado: press/release ---
teclas_ativas = set()

def on_press(key):
    try:
        char = key.char
    except AttributeError:
        if key == keyboard.Key.esc:
            return False
        return

    if char in MAPA_TECLAS and char not in teclas_ativas:
        teclas_ativas.add(char)
        for nota in MAPA_TECLAS[char]:
            fs.noteon(CANAL_GUITAR, nota, 90)
        print(f"[{char.upper()}] power chord {MAPA_TECLAS[char]} ON")

def on_release(key):
    try:
        char = key.char
    except AttributeError:
        return

    if char in MAPA_TECLAS and char in teclas_ativas:
        teclas_ativas.discard(char)
        for nota in MAPA_TECLAS[char]:
            fs.noteoff(CANAL_GUITAR, nota)
        print(f"[{char.upper()}] power chord {MAPA_TECLAS[char]} OFF")


# --- Main ---
print("smk riff — Consegue reconhecer? :)")
print("  Riff: A - S - D  |  A - S - F - D  |  A - S - D - S - A")
print("Segure as teclas para tocar. ESC para sair.\n")

try:
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()
finally:
    fs.delete()
    print("Encerrado.")
