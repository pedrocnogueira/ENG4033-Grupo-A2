import time
import threading
import fluidsynth
from pynput import keyboard

SOUNDFONT = "/Users/pedronogueira/PUC/micro/Trabalho/GeneralUser-GS/GeneralUser-GS.sf2"

BPM = 120
BEATS_POR_COMPASSO = 4

# Canal 0 = metrônomo (Woodblock)
# Canal 9 = bateria (canal de percussão padrão do GM — fixo)
CANAL_METRO = 0
CANAL_BATERIA = 10

NOTA_FORTE     = 76
NOTA_FRACA     = 77
VELOCITY_FORTE = 110
VELOCITY_FRACA = 70

# Notas GM de percussão no canal 9
MAPA_TECLAS = {
    'a': 36,  # Bass Drum (bumbo)
    's': 38,  # Snare Drum (caixa)
    'd': 42,  # Closed Hi-Hat
    'f': 46,  # Open Hi-Hat
    'g': 49,  # Crash Cymbal
}

NOMES = {
    'a': 'Bumbo',
    's': 'Caixa',
    'd': 'Hi-Hat Fechado',
    'f': 'Hi-Hat Aberto',
    'g': 'Crash',
}

# --- Sintetizador ---
fs = fluidsynth.Synth(gain=0.8)
fs.start(driver="coreaudio")

sfid = fs.sfload(SOUNDFONT)
fs.program_select(CANAL_METRO, sfid, 0, 115)   # Woodblock

# Canal 9 é percussão GM - banco 128, preset 0
fs.program_select(CANAL_BATERIA, sfid, 120, 8)

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
        fs.noteon(CANAL_BATERIA, MAPA_TECLAS[char], 100)
        print(f"[{char.upper()}] {NOMES[char]}")

def on_release(key):
    try:
        char = key.char
    except AttributeError:
        return

    if char in MAPA_TECLAS and char in teclas_ativas:
        teclas_ativas.discard(char)
        fs.noteoff(CANAL_BATERIA, MAPA_TECLAS[char])


# --- Main ---
print(f"Metrônomo: {BPM} BPM | {BEATS_POR_COMPASSO}/4")
print("Bateria:")
print("  A=Bumbo  S=Caixa  D=Hi-Hat Fechado  F=Hi-Hat Aberto  G=Crash")
print("Segure as teclas para tocar. ESC para sair.\n")

try:
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()
finally:
    _stop_event.set()
    fs.delete()
    print("Encerrado.")
