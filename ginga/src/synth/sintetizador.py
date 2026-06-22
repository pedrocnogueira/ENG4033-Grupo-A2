"""Sintetizador — dono dos recursos de áudio (FluidSynth + Sequencer).

Encapsula o FluidSynth para o resto do sistema não falar com a lib direto.
Cria e possui o Sequencer, já que os dois são acoplados na prática.
"""

import fluidsynth

from .. import config


class Sintetizador:
    def __init__(self, soundfont=config.SOUNDFONT, driver=config.DRIVER, gain=config.GAIN):
        self.fs = fluidsynth.Synth(gain=gain)
        self.fs.start(driver=driver)
        self.sfid = self.fs.sfload(str(soundfont))

        self.sequencer = fluidsynth.Sequencer(use_system_timer=False)
        self.synth_id = self.sequencer.register_fluidsynth(self.fs)

    # --- configuração de canais ---
    def selecionar_instrumento(self, canal, preset, banco=0):
        self.fs.program_select(canal, self.sfid, banco, preset)

    def volume_canal(self, canal, volume):
        # CC7 = volume do canal; efeito imediato.
        self.fs.cc(canal, 7, max(0, min(127, volume)))

    # --- disparo ao vivo (monitoração, sem passar pelo sequencer) ---
    def nota_on(self, canal, nota, velocity):
        self.fs.noteon(canal, nota, velocity)

    def nota_off(self, canal, nota):
        self.fs.noteoff(canal, nota)

    def encerrar(self):
        self.sequencer.delete()
        self.fs.delete()
