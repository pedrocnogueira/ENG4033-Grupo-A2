"""Metronomo — agenda um clique por beat na régua de tempo do loop.

Não tem clock próprio: recebe o início e o fator de conversão do loop e
deposita os cliques no sequencer. Sincronia perfeita com a música, sem drift.
"""

from . import config


class Metronomo:
    def __init__(self, sint, canal=config.CANAL_METRONOMO):
        self.sint = sint
        self.canal = canal
        self.ativo = True   # estado de runtime: lido a cada agendamento

        sint.selecionar_instrumento(canal, config.PRESET_METRONOMO)
        sint.volume_canal(canal, config.METRO_VOLUME)

    def set_volume(self, volume):
        # Volume master via CC7 — efeito imediato (não espera o loop).
        self.sint.volume_canal(self.canal, volume)

    def agendar(self, inicio, ms_por_tick, beats_por_loop):
        # Chamado pelo Looper a cada loop. Respeita self.ativo no momento.
        if not self.ativo:
            return
        seq, synth_id = self.sint.sequencer, self.sint.synth_id
        for beat in range(beats_por_loop):
            t = inicio + round(beat * config.PPQ * ms_por_tick)
            forte = beat == 0
            nota = config.METRO_NOTA_FORTE if forte else config.METRO_NOTA_FRACA
            vel  = config.METRO_VEL_FORTE if forte else config.METRO_VEL_FRACA
            seq.note_on(t, self.canal, nota, vel, dest=synth_id)
            seq.note_off(t + 20, self.canal, nota, dest=synth_id)
