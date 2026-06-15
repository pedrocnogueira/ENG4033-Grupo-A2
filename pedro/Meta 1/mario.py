import time
import fluidsynth

SOUNDFONT = "../GeneralUser-GS/GeneralUser-GS.sf2"

fs = fluidsynth.Synth(gain=0.6)
fs.start(driver="coreaudio")

sfid = fs.sfload(SOUNDFONT)
fs.program_select(0, sfid, 0, 80)  # Lead 1 - Square (som 8-bit)

# Durações base (BPM ~200)
q  = 0.30    # quarter note
e  = q / 2   # eighth note
qd = q * 1.5 # dotted quarter
r3 = e * 1.4 # nota do grupo de 3 (G4-E5-G5)

R = None  # rest

# Melodia principal do Mario (overworld theme)
# Cada entrada: (nota_midi, duracao_segundos)
#
# Notas de referência usadas:
#   G4=67  A4=69  Bb4=70  B4=71
#   C5=72  D5=74  E5=76  F5=77  G5=79  A5=81
melody = [
    # Frase 1 - riff de abertura
    (76, e), (R, e), (76, e), (R, e), (76, e), (R, e), (72, e), (76, q),
    (79, qd), (R, e), (67, qd), (R, q),

    # Frase 2 - linha descendente
    (72, qd), (R, e), (67, qd), (R, e), (64, qd), (R, e),

    # Frase 3 - cromatismo + corrida ascendente
    (69, e), (71, e), (70, e), (69, q),
    (67, r3), (76, r3), (79, r3),   # G4  E5  G5
    (81, q),  (77, e), (79, e),     # A5  F5  G5
    (76, q),  (72, e), (74, e),     # E5  C5  D5
    (71, qd), (R, e),               # B4
]

VEL = 90

print("Tocando Mario em loop. Ctrl+C para parar.\n")

try:
    while True:
        for nota, dur in melody:
            if nota is None:
                time.sleep(dur)
            else:
                fs.noteon(0, nota, VEL)
                time.sleep(dur)
                fs.noteoff(0, nota)

except KeyboardInterrupt:
    print("\nGame over.")

finally:
    fs.delete()
