import time
import fluidsynth

SOUNDFONT = "/Users/pedronogueira/PUC/micro/Trabalho/GeneralUser-GS/GeneralUser-GS.sf2"
DRIVER = 'coreaudio'

fs = fluidsynth.Synth(gain=0.8)
# especifica o driver para o OS, consultar README.md para mais informações
fs.start(driver=DRIVER)  

sfid = fs.sfload(SOUNDFONT)
fs.program_select(0, sfid, 0, 0)  # canal 0, banco 0, preset 0 (piano)

fs.noteon(0, 60, 64)   # Dó central, velocity 64
time.sleep(1.5)
fs.noteoff(0, 60)

time.sleep(0.5)

# Escala de Dó maior (C4 a C5)
ESCALA = [60, 62, 64, 65, 67, 69, 71, 72]
DURACAO_NOTA = 0.3   
PAUSA_NOTA   = 0.05
REPETICOES   = 3

print("Tocando escala em loop...")
print("Ctrl+C para parar.")

# Try-except-finally para garantir que o sintetizador seja fechado corretamente
try:
    for i in range(REPETICOES):
        print(f"Repetição {i + 1}/{REPETICOES}")
        for nota in ESCALA:
            fs.noteon(0, nota, 80)
            time.sleep(DURACAO_NOTA)
            fs.noteoff(0, nota)
            time.sleep(PAUSA_NOTA)
        time.sleep(0.3)  # pausa entre repetições

except KeyboardInterrupt:
    print("Interrompido.")

finally:
    fs.delete()
    print("Sintetizador encerrado.")
