import time
import threading
import fluidsynth
from pynput import keyboard

SOUNDFONT = "/Users/pedronogueira/PUC/micro/Trabalho/GeneralUser-GS/GeneralUser-GS.sf2"

BPM = 120
BEATS_POR_COMPASSO = 4

# Canal 0 = metrônomo (Woodblock)
# Canal 1 = guitarra (Electric Guitar Clean, preset 27)
CANAL_METRO  = 0
CANAL_GUITAR = 1

NOTA_FORTE     = 76
NOTA_FRACA     = 77
VELOCITY_FORTE = 110
VELOCITY_FRACA = 70

# Pentatônica menor de Lá: A3 C4 D4 E4 G4
# Teclas: A=57  S=60  D=62  F=64  G=67
MAPA_TECLAS = {
    'a': 57,  # A3
    's': 60,  # C4
    'd': 62,  # D4
    'f': 64,  # E4
    'g': 67,  # G4
}

# --- Sintetizador ---
fs = fluidsynth.Synth(gain=0.8)
fs.start(driver="coreaudio")

sfid = fs.sfload(SOUNDFONT)
fs.program_select(CANAL_METRO,  sfid, 0, 115)  # Woodblock
fs.program_select(CANAL_GUITAR, sfid, 0, 29)   # Overdrive Guitar

# --- Metrônomo em thread ---
_stop_event = threading.Event()

def loop_metronomo():
    intervalo = 60.0 / BPM
    beat = 0
    while not _stop_event.is_set():
        eh_forte = (beat % BEATS_POR_COMPASSO == 0)
        nota = NOTA_FORTE if eh_forte else NOTA_FRACA
        vel  = VELOCITY_FORTE if eh_forte else VELOCITY_FRACA

        fs.noteon(CANAL_METRO, nota, vel)
        time.sleep(0.05)
        fs.noteoff(CANAL_METRO, nota)

        _stop_event.wait(timeout=intervalo - 0.05)
        beat += 1

threading.Thread(target=loop_metronomo, daemon=True).start()

# --- Teclado: press/release ---
teclas_ativas = set()

def on_press(key):
    try:
        char = key.char
    except AttributeError:
        if key == keyboard.Key.esc:
            return False  # encerra o listener
        return

    if char in MAPA_TECLAS and char not in teclas_ativas:
        teclas_ativas.add(char)
        fs.noteon(CANAL_GUITAR, MAPA_TECLAS[char], 90)
        print(f"[{char.upper()}] nota {MAPA_TECLAS[char]} ON")

def on_release(key):
    try:
        char = key.char
    except AttributeError:
        return

    if char in MAPA_TECLAS and char in teclas_ativas:
        teclas_ativas.discard(char)
        fs.noteoff(CANAL_GUITAR, MAPA_TECLAS[char])
        print(f"[{char.upper()}] nota {MAPA_TECLAS[char]} OFF")


# --- Main ---
print(f"Metrônomo: {BPM} BPM | {BEATS_POR_COMPASSO}/4")
print("Guitarra - pentatônica menor de Lá:")
print("  A=57  S=60  D=62  F=64  G=67")
print("Segure as teclas para tocar. ESC para sair.\n")

try:
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()
finally:
    _stop_event.set()
    fs.delete()
    print("Encerrado.")
