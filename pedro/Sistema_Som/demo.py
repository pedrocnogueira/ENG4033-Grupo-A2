"""Demo da Meta 2 sobre o sistema em classes (Sistema_Som).

Mesmo roteiro do Meta 2/demo_meta2.py, mas usando a arquitetura em camadas.
O tocador automático é só mais um driver: chama looper.nota_on / nota_off —
exatamente as mesmas funções que o TecladoInput usa.

Quatro fases audíveis + tocar ao vivo:
  Fase 1 — Sintetizador da Meta 1 (escala soa)
  Fase 2 — Metrônomo + motor de loop (clique sincronizado)
  Fase 3 — Gravação em loop (frase entra e passa a repetir)
  Fase 4 — Alteração do loop EM EXECUÇÃO (notas novas + BPM + metrônomo)

Rode a partir da pasta Trabalho:
  .venv/bin/python -m Sistema_Som.demo
"""

import time

from . import config
from .sintetizador import Sintetizador
from .metronomo import Metronomo
from .looper import Looper
from .teclado import TecladoInput


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def banner(txt: str) -> None:
    print(f"\n{'=' * 52}\n{txt}\n{'=' * 52}")


def ouvir_loops(looper: Looper, n: float = 2) -> None:
    # Dorme o equivalente a n loops no BPM atual.
    dur_loop = looper.beats_por_loop * (60.0 / looper.bpm)
    time.sleep(n * dur_loop)


def tocar_frase(looper: Looper, notas, vel: int = config.VEL_PADRAO) -> None:
    # Uma nota por beat, via nota_on/nota_off — passa pela via real de gravação.
    time.sleep(looper.ms_ate_proximo_beat() / 1000.0)   # alinha ao próximo beat
    beat = 60.0 / looper.bpm
    for n in notas:
        looper.nota_on(n, vel)
        time.sleep(beat * 0.9)
        looper.nota_off(n)
        time.sleep(beat * 0.1)


# ---------------------------------------------------------------------------
# Fases
# ---------------------------------------------------------------------------
def fase1_sintetizador(sint: Sintetizador) -> None:
    banner("FASE 1 — Sintetizador (Meta 1): escala de Dó maior")
    print("Toca uma escala direto no synth — soundfont carrega e as notas soam.")
    escala = [60, 62, 64, 65, 67, 69, 71, 72]
    for n in escala:
        sint.nota_on(config.CANAL_INSTRUMENTO, n, 90)
        time.sleep(0.25)
        sint.nota_off(config.CANAL_INSTRUMENTO, n)
    time.sleep(0.6)


def fase2_metronomo(looper: Looper) -> None:
    banner("FASE 2 — Metrônomo + motor de loop (loop vazio)")
    print("Inicia o loop sem notas: só o clique. Forte no beat 1, fraco nos demais.")
    looper.iniciar()
    ouvir_loops(looper, 2)


def fase3_gravacao(looper: Looper) -> None:
    banner("FASE 3 — Gravação no loop (pentatônica menor de Lá)")
    print("O tocador 'grava' uma frase chamando nota_on/nota_off. Ela passa a repetir.")
    tocar_frase(looper, [57, 60, 62, 64])   # A3 C4 D4 E4 — uma nota por beat
    print(">> agora a frase repete sem ninguém tocando:")
    ouvir_loops(looper, 2)


def fase4_alteracao(looper: Looper, metronomo: Metronomo) -> None:
    banner("FASE 4 — Alteração do loop EM EXECUÇÃO")

    print(">> adicionando um contracanto grave (sem parar o loop)")
    tocar_frase(looper, [45, 48, 50, 52], vel=75)   # uma oitava abaixo
    ouvir_loops(looper, 2)

    print(">> mudando o BPM: 120 -> 90 (música e metrônomo desaceleram juntos)")
    looper.bpm = 90
    ouvir_loops(looper, 2)

    print(">> desligando o metrônomo (vale a partir do próximo loop)")
    metronomo.ativo = False
    ouvir_loops(looper, 2)

    print(">> restaurando: BPM 120 e metrônomo ligado")
    looper.bpm = 120
    metronomo.ativo = True
    ouvir_loops(looper, 1)


def tocar_ao_vivo(looper: Looper) -> None:
    banner("AGORA VOCÊ — toque no teclado (A S D F G)")
    print("As notas entram no mesmo loop. BACKSPACE limpa tudo. ESC encerra.")
    TecladoInput(looper).executar()


# ---------------------------------------------------------------------------
# Composição + roteiro
# ---------------------------------------------------------------------------
def main() -> None:
    sint = Sintetizador()
    sint.selecionar_instrumento(config.CANAL_INSTRUMENTO, config.PRESET_INSTRUMENTO)
    metronomo = Metronomo(sint)
    looper = Looper(sint, metronomo)

    try:
        fase1_sintetizador(sint)
        fase2_metronomo(looper)
        fase3_gravacao(looper)
        fase4_alteracao(looper, metronomo)
        tocar_ao_vivo(looper)
    finally:
        sint.encerrar()
        print("\nDemo encerrado.")


if __name__ == "__main__":
    main()
