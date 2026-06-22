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

# Tracks da sessão: (nome, preset GM, canal MIDI, banco).
# Bateria vai no canal 9 (percussão GM) com bank 128 (drum kit).
TRACKS = [
    ("Guitarra", config.PRESET_INSTRUMENTO, config.CANAL_INSTRUMENTO, 0),   # Electric Guitar, ch 1
    ("Baixo",    33,                        2,                         0),   # Electric Bass, ch 2
    ("Bateria",  0,                         9,                         128), # GM Drum Kit, ch 9
]


def main():
    sint = Sintetizador()
    metronomo = Metronomo(sint)

    def corrigir(track):
        # Captura o canal da track ANTES (todos os eventos de uma track usam o
        # mesmo canal) para re-carimbar depois: a notação ABC não carrega canal
        # MIDI, então abc_to_track recria tudo no canal 0. Gap da correção.
        canais = [ev.channel for evs in track.events.values() for ev in evs]
        canal_orig = canais[0] if canais else 0
        nova = perform_music_adjustments(track)
        for eventos in nova.events.values():
            for ev in eventos:
                ev.channel = canal_orig
        return nova

    studio = Studio(sint, metronomo, corrigir)
    for nome, preset, canal, banco in TRACKS:
        studio.adicionar_track(instrumento=preset, canal=canal, key="C", banco=banco)

    print(f"BPM={studio.bpm} | {config.BEATS_POR_LOOP} beats/loop | PPQ={config.PPQ}")
    print(f"Metrônomo: canal {metronomo.canal} | ativo={metronomo.ativo}")
    print("Tracks (troque com 1/2/3):")
    for n, (nome, preset, canal, banco) in enumerate(TRACKS, start=1):
        print(f"  {n} = {nome}  (canal {canal}, preset {preset})")
    print("Notas - pentatônica menor de Lá:")
    print("  A=57  S=60  D=62  F=64  G=67")
    print(f"  C = corrigir track ativa")
    print("  R = restaurar (desfaz a correção)")
    print("  BACKSPACE limpa a track ativa | ESC sai.\n")

    studio.play()
    teclado = TecladoInput(studio, n_tracks=len(TRACKS))
    try:
        teclado.executar()
    finally:
        sint.encerrar()
        print("Encerrado.")


if __name__ == "__main__":
    main()
