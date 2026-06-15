"""Demo da Meta 2 para apresentação.

Roteiro automático e auto-narrado que prova, em 4 fases audíveis:
  Fase 1 — Sintetizador da Meta 1 (escala soa)
  Fase 2 — Metrônomo + motor de loop (clique sincronizado)
  Fase 3 — Gravação em loop (frase entra e passa a repetir)
  Fase 4 — Alteração do loop EM EXECUÇÃO (notas novas + BPM + metrônomo)
Ao final, abre o teclado para tocar ao vivo.

O tocador automático é só mais uma fonte de input: chama as MESMAS funções
nota_on/nota_off que o teclado usa — então o próprio demo já prova que o
engine está desacoplado da fonte de entrada.

Rode a partir da pasta Trabalho:
  .venv/bin/python "Meta 2/demo_meta2.py"
"""

import time

from pynput import keyboard

import play_and_record as eng   # importar já inicializa o áudio (synth + sequencer)


# ---------------------------------------------------------------------------
# Helpers de tempo
# ---------------------------------------------------------------------------
def banner(txt: str) -> None:
    print(f"\n{'=' * 52}\n{txt}\n{'=' * 52}")


def ouvir_loops(n: float = 2) -> None:
    # Dorme o equivalente a n loops no BPM atual (loop = beats * tempo do beat).
    dur_loop = eng.BEATS_POR_LOOP * (60.0 / eng.BPM)
    time.sleep(n * dur_loop)


def esperar_proximo_beat() -> None:
    # Alinha o início da frase ao próximo beat, para soar intencional.
    beat_ms = eng.ms_por_beat()
    desde_inicio = eng.sequencer.get_tick() - eng.loop_inicio
    falta = beat_ms - (desde_inicio % beat_ms)
    time.sleep(falta / 1000.0)


def tocar_frase(notas, vel: int = 90) -> None:
    # Toca uma nota por beat, via nota_on/nota_off — grava no loop de verdade.
    esperar_proximo_beat()
    beat = 60.0 / eng.BPM
    for n in notas:
        eng.nota_on(n, vel)
        time.sleep(beat * 0.9)
        eng.nota_off(n)
        time.sleep(beat * 0.1)


# ---------------------------------------------------------------------------
# Fases
# ---------------------------------------------------------------------------
def fase1_sintetizador() -> None:
    banner("FASE 1 — Sintetizador (Meta 1): escala de Dó maior")
    print("Toca uma escala direto no synth — prova que o soundfont carrega e as notas soam.")
    escala = [60, 62, 64, 65, 67, 69, 71, 72]
    for n in escala:
        eng.fs.noteon(eng.CANAL_GUITAR, n, 90)
        time.sleep(0.25)
        eng.fs.noteoff(eng.CANAL_GUITAR, n)
    time.sleep(0.6)


def fase2_metronomo() -> None:
    banner("FASE 2 — Metrônomo + motor de loop (loop vazio)")
    print("Inicia o loop sem notas: só o clique. Forte no beat 1, fraco nos demais.")
    eng.iniciar_loop()
    ouvir_loops(2)


def fase3_gravacao() -> None:
    banner("FASE 3 — Gravação no loop (pentatônica menor de Lá)")
    print("O tocador 'grava' uma frase chamando nota_on/nota_off. Ela passa a repetir sozinha.")
    tocar_frase([57, 60, 62, 64])   # A3 C4 D4 E4 — uma nota por beat (preenche 1 loop)
    print(">> agora a frase repete sem ninguém tocando:")
    ouvir_loops(2)


def fase4_alteracao() -> None:
    banner("FASE 4 — Alteração do loop EM EXECUÇÃO")

    print(">> adicionando um contracanto grave (sem parar o loop)")
    tocar_frase([45, 48, 50, 52], vel=75)   # uma oitava abaixo
    ouvir_loops(2)

    print(">> mudando o BPM: 120 -> 90 (tudo desacelera junto, música + metrônomo)")
    eng.BPM = 90
    ouvir_loops(2)

    print(">> desligando o metrônomo (vale a partir do próximo loop)")
    eng.metro_ativo = False
    ouvir_loops(2)

    print(">> restaurando: BPM 120 e metrônomo ligado")
    eng.BPM = 120
    eng.metro_ativo = True
    ouvir_loops(1)


def tocar_ao_vivo() -> None:
    banner("AGORA VOCÊ — toque no teclado (A S D F G)")
    print("As notas entram no mesmo loop. BACKSPACE limpa tudo. ESC encerra.")
    with keyboard.Listener(on_press=eng.on_press, on_release=eng.on_release) as listener:
        listener.join()


# ---------------------------------------------------------------------------
# Roteiro
# ---------------------------------------------------------------------------
def main() -> None:
    try:
        fase1_sintetizador()
        fase2_metronomo()
        fase3_gravacao()
        fase4_alteracao()
        tocar_ao_vivo()
    finally:
        eng.encerrar()
        print("\nDemo encerrado.")


if __name__ == "__main__":
    main()
