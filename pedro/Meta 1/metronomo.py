import time
import fluidsynth

SOUNDFONT = "/Users/pedronogueira/PUC/micro/Trabalho/GeneralUser-GS/GeneralUser-GS.sf2"
BPM = 120
COMPASSOS = 8
BEATS_POR_COMPASSO = 4

# Preset 115 = Woodblock (banco 0) - som clássico de metrônomo
BANCO = 0
PRESET = 115

# Notas: tempo forte vs tempos fracos
NOTA_FORTE = 76   # High Wood Block
NOTA_FRACA  = 77  # Low Wood Block

# Velocidade funciona como volume, quanto maior, mais forte. Range: 0-127
VELOCITY_FORTE = 110
VELOCITY_FRACA  = 70

intervalo = 60.0 / BPM  # segundos por beat

fs = fluidsynth.Synth(gain=0.8)
fs.start(driver="coreaudio")

sfid = fs.sfload(SOUNDFONT)
fs.program_select(0, sfid, BANCO, PRESET)

print(f"Metrônomo: {BPM} BPM | {BEATS_POR_COMPASSO}/4 | {COMPASSOS} compassos")

for compasso in range(COMPASSOS):
    for beat in range(BEATS_POR_COMPASSO):
        eh_forte = (beat == 0)
        nota     = NOTA_FORTE if eh_forte else NOTA_FRACA
        vel      = VELOCITY_FORTE if eh_forte else VELOCITY_FRACA
        simbolo  = "FORTE" if eh_forte else "  --"

        print(f"Compasso {compasso + 1} | Beat {beat + 1} {simbolo}")

        fs.noteon(0, nota, vel)
        time.sleep(0.05)
        fs.noteoff(0, nota)

        time.sleep(intervalo - 0.05)

fs.delete()
