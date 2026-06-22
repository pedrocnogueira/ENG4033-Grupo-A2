"""Composição do sistema — monta as peças e roda.

Este é o "composition root": o único lugar que conhece todas as camadas e as
liga por injeção de dependência. Rode com:  python3 -m Sistema_Som
"""

from . import config
from .synth.sintetizador import Sintetizador
from .synth.metronomo import Metronomo
from .synth.looper import Looper
from .synth.teclado import TecladoInput
from .model.track import Track


def main():
    sint = Sintetizador()
    sint.selecionar_instrumento(config.CANAL_INSTRUMENTO, config.PRESET_INSTRUMENTO)

    metronomo = Metronomo(sint)
    track = Track(
        key="default",
        time_signature=(config.BEATS_POR_LOOP, 4),
        PPQ=config.PPQ,
    )
    looper = Looper(sint, metronomo, track)

    print(f"BPM={looper.bpm} | {looper.beats_por_loop} beats/loop | PPQ={config.PPQ}")
    print(f"Metrônomo: canal {metronomo.canal} | ativo={metronomo.ativo}")
    print("Guitarra - pentatônica menor de Lá:")
    print("  A=57  S=60  D=62  F=64  G=67")
    print("Toque para gravar no loop. BACKSPACE limpa. ESC sai.\n")

    looper.iniciar()
    teclado = TecladoInput(looper)
    try:
        teclado.executar()
    finally:
        sint.encerrar()
        print("Encerrado.")


if __name__ == "__main__":
    main()
