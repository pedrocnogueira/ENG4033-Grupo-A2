"""Composição do sistema — monta as peças e roda (CLI de teste).

Este é o "composition root": o único lugar que conhece todas as camadas e as
liga por injeção de dependência. Esta versão é a CLI para testar a integração
synth <-> correção SEM UI: input pelo teclado (pynput), com a tecla C disparando
o módulo de correção sobre a track gravada.

Rode (a partir de ginga/, com o python do venv):
  ../.venv/bin/python -m src
"""

from . import config
from .synth.sintetizador import Sintetizador
from .synth.metronomo import Metronomo
from .synth.studio import Studio
from .synth.teclado import TecladoInput
from .correction.corrector import perform_music_adjustments

# Resolução fixa da quantização (8 = colcheia). Caminho SEM LLM: quantize por
# inteiro + adjust_melody=False não chama ollama nem usa os prompts.
RESOLUCAO_CORRECAO = 8


def main():
    sint = Sintetizador()
    metronomo = Metronomo(sint)

    canal = config.CANAL_INSTRUMENTO

    def corrigir(track):
        nova = perform_music_adjustments(track, quantize=RESOLUCAO_CORRECAO,
                                         adjust_melody=False)
        # A notação ABC não carrega canal MIDI: abc_to_track recria os eventos
        # no canal 0. Re-carimbamos o canal original (single-track) para a
        # reprodução sair no instrumento certo. Gap conhecido da correção.
        for eventos in nova.events.values():
            for ev in eventos:
                ev.channel = canal
        return nova

    studio = Studio(sint, metronomo, corrigir)
    studio.adicionar_track(instrumento=config.PRESET_INSTRUMENTO, canal=canal, key="C")

    print(f"BPM={studio.bpm} | {config.BEATS_POR_LOOP} beats/loop | PPQ={config.PPQ}")
    print(f"Metrônomo: canal {metronomo.canal} | ativo={metronomo.ativo}")
    print("Guitarra - pentatônica menor de Lá:")
    print("  A=57  S=60  D=62  F=64  G=67")
    print("Toque para gravar no loop.")
    print(f"  C = corrigir (quantiza, resolução {RESOLUCAO_CORRECAO})")
    print("  R = restaurar (desfaz a correção)")
    print("  BACKSPACE limpa | ESC sai.\n")

    studio.play()
    teclado = TecladoInput(studio)
    try:
        teclado.executar()
    finally:
        sint.encerrar()
        print("Encerrado.")


if __name__ == "__main__":
    main()
