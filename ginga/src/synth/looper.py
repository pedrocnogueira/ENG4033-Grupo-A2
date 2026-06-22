"""Looper — o engine: timing, gravação e agendamento do loop.

Esta é a fronteira de integração. Qualquer fonte de input (teclado, MIDI,
rede, GUI) só precisa chamar nota_on / nota_off — o Looper não sabe de onde
veio o comando.

Modelo de gravação:
  self.track.events: dict[tick_relativo, list[Event]]
  - chave : tick PPQ dentro do loop (0 … ticks_por_loop-1), independente de BPM
  - valor : lista (acordes caem no mesmo tick)

Cada Event carrega `duration` em ticks; no playback o Looper expande em
note_on / note_off no sequencer.
"""

import threading

from . import config
from .Event import Event
from .Track import Track


class Looper:
    def __init__(self, sint, metronomo, track: Track,
                 bpm=config.BPM_PADRAO, beats_por_loop=config.BEATS_POR_LOOP):
        self.sint = sint
        self.metronomo = metronomo
        self.track = track
        self.bpm = bpm
        self.beats_por_loop = beats_por_loop

        # (channel, note) -> (abs_press_tick, velocity) enquanto a nota está
        # segurada. Guardamos o tick ABSOLUTO do sequencer (não o tick
        # relativo ao loop): assim conseguimos detectar corretamente notas
        # que cruzam a barra do loop, sem confundir com a virada do
        # _loop_inicio que acontece no callback _on_loop.
        self._pending: dict[tuple[int, int], tuple[int, int]] = {}
        self._lock = threading.Lock()
        self._loop_inicio = 0
        self._client_id = sint.sequencer.register_client("looper", self._on_loop)

    # --- derivados de tempo ---
    @property
    def ticks_por_loop(self):
        return self.track.PPQ * self.beats_por_loop

    def _ms_por_tick(self):
        return (60_000 / self.bpm) / self.track.PPQ

    def ms_ate_proximo_beat(self):
        beat_ms = 60_000 / self.bpm
        desde_inicio = self.sint.sequencer.get_tick() - self._loop_inicio
        return beat_ms - (desde_inicio % beat_ms)

    # --- API do engine (input-agnóstica) ---
    def nota_on(self, nota, velocity=config.VEL_PADRAO, canal=config.CANAL_INSTRUMENTO):
        # Toca ao vivo (monitoração) e marca a nota como em curso. O Event só
        # é gravado em nota_off, quando já conhecemos a duration.
        self.sint.nota_on(canal, nota, velocity)
        abs_press = self.sint.sequencer.get_tick()
        with self._lock:
            self._pending[(canal, nota)] = (abs_press, velocity)
            tick_rel = self._tick_relativo(abs_press)
        return tick_rel

    def nota_off(self, nota, canal=config.CANAL_INSTRUMENTO):
        self.sint.nota_off(canal, nota)
        abs_off = self.sint.sequencer.get_tick()
        ms_por_tick = self._ms_por_tick()
        extra = None

        with self._lock:
            start = self._pending.pop((canal, nota), None)
            if start is None:
                return abs_off
            abs_press, velocity = start

            # Duração real (em ticks do grid). Clampamos a um loop: além
            # disso a nota se sobreporia à sua própria reprodução no loop
            # seguinte. 0 = release instantâneo → tratamos como loop inteiro.
            elapsed = round((abs_off - abs_press) / ms_por_tick)
            duration = min(elapsed, self.ticks_por_loop) or self.ticks_por_loop

            # press_tick relativo ao grid. Funciona mesmo se _loop_inicio
            # mudou após o press: a posição relativa é a mesma em qualquer
            # loop (modulo Python normaliza valores negativos).
            press_tick = self._tick_relativo(abs_press)

            ev = Event(nota, duration, canal, velocity)
            self.track.events.setdefault(press_tick, []).append(ev)

            # Se a virada do loop aconteceu entre o press e o release, o
            # snapshot do loop atual foi tirado pelo _on_loop SEM este
            # evento — a nota sumiria por um loop inteiro. Compensamos
            # agendando manualmente neste loop, se o press_tick ainda
            # estiver no futuro da volta atual.
            if abs_press < self._loop_inicio:
                t_on = self._loop_inicio + round(press_tick * ms_por_tick)
                if t_on > abs_off:
                    extra = (t_on, ev)

        if extra is not None:
            t_on, ev = extra
            t_off = t_on + round(ev.duration * ms_por_tick)
            seq, synth_id = self.sint.sequencer, self.sint.synth_id
            seq.note_on(t_on, ev.channel, ev.note, ev.velocity, dest=synth_id)
            seq.note_off(t_off, ev.channel, ev.note, dest=synth_id)

        return abs_off

    def limpar(self):
        with self._lock:
            self.track.events.clear()
            self._pending.clear()

    # --- gravação interna ---
    def _tick_atual(self):
        return self._tick_relativo(self.sint.sequencer.get_tick())

    def _tick_relativo(self, abs_tick):
        # Posição no grid do loop a partir de um tick absoluto do sequencer.
        # Modulo Python mantém o resultado em [0, ticks_por_loop) mesmo se
        # abs_tick é anterior ao _loop_inicio atual (loop já virou).
        ms_rel = abs_tick - self._loop_inicio
        return round(ms_rel / self._ms_por_tick()) % self.ticks_por_loop

    # --- agendamento do loop ---
    def iniciar(self):
        self._loop_inicio = self.sint.sequencer.get_tick()
        self._agendar(self._loop_inicio)

    def _agendar(self, inicio):
        ms_por_tick = self._ms_por_tick()
        seq, synth_id = self.sint.sequencer, self.sint.synth_id

        with self._lock:
            snapshot = list(self.track.events.items())

        for tick, lista in snapshot:
            t_on = inicio + round(tick * ms_por_tick)
            for ev in lista:
                t_off = t_on + round(ev.duration * ms_por_tick)
                seq.note_on(t_on, ev.channel, ev.note, ev.velocity, dest=synth_id)
                seq.note_off(t_off, ev.channel, ev.note, dest=synth_id)

        self.metronomo.agendar(inicio, ms_por_tick, self.beats_por_loop)

        dur_loop_ms = round(self.ticks_por_loop * ms_por_tick)
        seq.timer(inicio + dur_loop_ms, dest=self._client_id)

    def _on_loop(self, time, event, seq, data):
        self._loop_inicio = time
        self._agendar(time)
