"""studio — fachada multi-track do synth.

Dono da lista de Loopers (um por track, todos sobre o mesmo Sintetizador) e do
CLOCK da sessão: registra um único timer no sequencer e, a cada virada de loop,
agenda o metrônomo uma vez e manda cada Looper agendar seus eventos. Assim todas
as tracks compartilham a mesma virada, sem drift nem metrônomos duplicados.

É a única superfície que a UI enxerga do lado do som: a UI lê `tracks` para
desenhar e chama nota_on/off, play/stop, set_bpm. A correção fica cabeada
(corrigir_track) mas dormente — ninguém a dispara ainda.
"""

import threading

from .. import config
from .looper import Looper
from ..model.track import Track


class Studio:
    def __init__(self, sint, metronomo, correction,
                 bpm=config.BPM_PADRAO, beats_por_loop=config.BEATS_POR_LOOP):
        self._sint = sint
        self._metronomo = metronomo
        self._correction = correction        # callable Track -> Track; só em corrigir_track()
        self._bpm = bpm
        self._beats_por_loop = beats_por_loop

        self._loopers: list[Looper] = []
        self._lock = threading.Lock()
        self._rodando = False
        self._client_id = sint.sequencer.register_client("studio", self._on_loop)

    # --- gestão de tracks ---
    def adicionar_track(self, instrumento, canal, key="C", banco=0) -> int:
        # `instrumento` = preset General MIDI; `canal` = canal MIDI da track;
        # `banco` = bank do soundfont (use 128 p/ kits de percussão na bateria).
        self._sint.selecionar_instrumento(canal, instrumento, banco)
        track = Track(key=key, time_signature=(self._beats_por_loop, 4),
                      PPQ=config.PPQ, events={})
        looper = Looper(self._sint, self._metronomo, track,
                        bpm=self._bpm, beats_por_loop=self._beats_por_loop,
                        canal=canal)
        with self._lock:
            self._loopers.append(looper)
            return len(self._loopers) - 1

    def remover_track(self, i) -> None:
        with self._lock:
            self._loopers.pop(i)

    # --- leitura para a UI (snapshot sob lock) ---
    @property
    def tracks(self) -> list[Track]:
        with self._lock:
            return [lp.track for lp in self._loopers]

    # --- input ao vivo (teclado Tk / Arduino delegam aqui) ---
    def nota_on(self, track_i, nota, vel=config.VEL_PADRAO) -> None:
        self._loopers[track_i].nota_on(nota, vel)

    def nota_off(self, track_i, nota) -> None:
        self._loopers[track_i].nota_off(nota)

    def limpar_track(self, i) -> None:
        self._loopers[i].limpar()

    # --- controles de clock ---
    def play(self) -> None:
        if self._rodando:
            return
        self._rodando = True
        self._agendar(self._sint.sequencer.get_tick())

    def stop(self) -> None:
        self._rodando = False

    def set_bpm(self, bpm) -> None:
        # Propaga o tempo para os loopers (a gravação ao vivo usa bpm no cálculo
        # do tick). Vale a partir da próxima virada.
        with self._lock:
            self._bpm = bpm
            for lp in self._loopers:
                lp.bpm = bpm

    @property
    def bpm(self) -> int:
        return self._bpm

    # --- clock: agendamento sincronizado de todas as tracks ---
    def _ms_por_tick(self) -> float:
        return (60_000 / self._bpm) / config.PPQ

    def _agendar(self, inicio) -> None:
        ms_por_tick = self._ms_por_tick()

        with self._lock:
            loopers = list(self._loopers)

        for lp in loopers:
            lp.agendar_eventos(inicio, ms_por_tick)

        self._metronomo.agendar(inicio, ms_por_tick, self._beats_por_loop)

        if self._rodando:
            dur_loop_ms = round(config.PPQ * self._beats_por_loop * ms_por_tick)
            self._sint.sequencer.timer(inicio + dur_loop_ms, dest=self._client_id)

    def _on_loop(self, time, event, seq, data) -> None:
        if not self._rodando:
            return
        self._agendar(time)

    # --- CORREÇÃO: pronta, porém NÃO disparada por ninguém ainda ---
    def corrigir_track(self, i) -> None:
        # Sem lock durante a correção: pode ser lenta (LLM). substituir_track
        # tem o próprio lock; ler .track é leitura atômica de referência.
        looper = self._loopers[i]
        corrigida = self._correction(looper.track)
        looper.substituir_track(corrigida)

    def restaurar_track(self, i) -> None:
        self._loopers[i].restaurar_track()

    def pode_restaurar(self, i) -> bool:
        return self._loopers[i].pode_restaurar
