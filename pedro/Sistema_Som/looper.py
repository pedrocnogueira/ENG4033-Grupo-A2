"""Looper — o engine: timing, gravação e agendamento do loop.

Esta é a fronteira de integração. Qualquer fonte de input (teclado, MIDI,
rede, GUI) só precisa chamar nota_on / nota_off — o Looper não sabe de onde
veio o comando.

Estrutura dos eventos gravados:
  self.eventos: dict[tick_relativo, list[Evento]]
  - chave : tick PPQ dentro do loop (0 … ticks_por_loop-1), independente de BPM
  - valor : lista, pois vários eventos podem cair no mesmo tick (acordes)
"""

import threading

from . import config
from .evento import Evento


class Looper:
    def __init__(self, sint, metronomo,
                 bpm=config.BPM_PADRAO, beats_por_loop=config.BEATS_POR_LOOP):
        self.sint = sint
        self.metronomo = metronomo
        self.bpm = bpm                      # estado de runtime: muda ao vivo
        self.beats_por_loop = beats_por_loop

        self.eventos: dict[int, list[Evento]] = {}
        self._lock = threading.Lock()       # eventos é tocado e gravado por threads diferentes
        self._loop_inicio = 0               # tick absoluto (ms) em que o loop atual começou
        self._client_id = sint.sequencer.register_client("looper", self._on_loop)

    # --- derivados de tempo ---
    @property
    def ticks_por_loop(self):
        return config.PPQ * self.beats_por_loop

    def _ms_por_tick(self):
        # Lê self.bpm AGORA: trocar o BPM reflete no próximo agendamento.
        return (60_000 / self.bpm) / config.PPQ

    def ms_ate_proximo_beat(self):
        # Quanto falta (ms) até a próxima divisa de beat. Útil para uma fonte
        # de input alinhar disparos ao tempo, sem precisar do estado interno.
        beat_ms = 60_000 / self.bpm
        desde_inicio = self.sint.sequencer.get_tick() - self._loop_inicio
        return beat_ms - (desde_inicio % beat_ms)

    # --- API do engine (input-agnóstica) ---
    def nota_on(self, nota, velocity=config.VEL_PADRAO, canal=config.CANAL_INSTRUMENTO):
        # Toca ao vivo (monitoração) e grava o evento no tick atual. Retorna o tick.
        self.sint.nota_on(canal, nota, velocity)
        tick = self._tick_atual()
        self._registrar(tick, Evento("on", canal, nota, velocity))
        return tick

    def nota_off(self, nota, canal=config.CANAL_INSTRUMENTO):
        self.sint.nota_off(canal, nota)
        tick = self._tick_atual()
        self._registrar(tick, Evento("off", canal, nota))
        return tick

    def limpar(self):
        with self._lock:
            self.eventos.clear()

    # --- gravação interna ---
    def _tick_atual(self):
        ms_rel = self.sint.sequencer.get_tick() - self._loop_inicio
        return round(ms_rel / self._ms_por_tick()) % self.ticks_por_loop

    def _registrar(self, tick, ev):
        with self._lock:
            self.eventos.setdefault(tick, []).append(ev)

    # --- agendamento do loop ---
    def iniciar(self):
        self._loop_inicio = self.sint.sequencer.get_tick()
        self._agendar(self._loop_inicio)

    def _agendar(self, inicio):
        ms_por_tick = self._ms_por_tick()
        seq, synth_id = self.sint.sequencer, self.sint.synth_id

        # Snapshot sob lock: a thread de input pode estar gravando ao mesmo tempo.
        with self._lock:
            snapshot = list(self.eventos.items())

        for tick, lista in snapshot:
            t = inicio + round(tick * ms_por_tick)
            for ev in lista:
                if ev.tipo == "on":
                    seq.note_on(t, ev.canal, ev.nota, ev.velocity, dest=synth_id)
                else:
                    seq.note_off(t, ev.canal, ev.nota, dest=synth_id)

        self.metronomo.agendar(inicio, ms_por_tick, self.beats_por_loop)

        dur_loop_ms = round(self.ticks_por_loop * ms_por_tick)
        seq.timer(inicio + dur_loop_ms, dest=self._client_id)

    def _on_loop(self, time, event, seq, data):
        # Callback do sequencer no início de cada loop.
        self._loop_inicio = time
        self._agendar(time)
