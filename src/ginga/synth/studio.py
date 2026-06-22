"""studio — fachada multi-track do synth (A IMPLEMENTAR).

Dono da list[Track] e de um Looper por track (todos sobre o mesmo Sintetizador).
É a única superfície que a UI enxerga do lado do som, e o dono do clock.

Este arquivo é um ESQUELETO. A lógica real será preenchida conforme o plano de
integração (ver ARQUITETURA.md). As assinaturas abaixo refletem a API combinada.
"""

import threading

from ..model.track import Track


class Studio:
    def __init__(self, sint, metronomo, correction):
        self._sint = sint
        self._metronomo = metronomo
        self._correction = correction        # injetada; usada só em corrigir_track()
        self._loopers: list = []             # list[Looper]
        self._lock = threading.Lock()

    # --- gestão de tracks ---
    def adicionar_track(self, instrumento, canal) -> int:
        raise NotImplementedError

    def remover_track(self, i) -> None:
        raise NotImplementedError

    # --- leitura para a UI (snapshot sob lock) ---
    @property
    def tracks(self) -> list[Track]:
        raise NotImplementedError

    # --- input ao vivo (teclado Tk / Arduino delegam aqui) ---
    def nota_on(self, track_i, nota, vel) -> None:
        raise NotImplementedError

    def nota_off(self, track_i, nota) -> None:
        raise NotImplementedError

    # --- controles ---
    def play(self) -> None:
        raise NotImplementedError

    def stop(self) -> None:
        raise NotImplementedError

    def set_bpm(self, bpm) -> None:
        raise NotImplementedError

    # --- CORREÇÃO: pronta, porém NÃO disparada por ninguém ainda ---
    def corrigir_track(self, i) -> None:
        with self._lock:
            corrigida = self._correction(self._loopers[i].track)
            self._loopers[i].substituir_track(corrigida)
