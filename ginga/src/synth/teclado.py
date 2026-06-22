"""TecladoInput — adaptador de input por teclado (CLI, via pynput).

Única parte do sistema que conhece o pynput. Traduz tecla -> nota e delega ao
Studio. É a fonte de input legada da CLI; na GUI quem captura tecla é o Tk
(ui/inputs/keyboard.py). Mantido aqui para testar a integração sem UI.

Teclas:
  A S D F G  -> notas (pentatônica menor de Lá)
  C          -> corrigir a track (módulo de correção)
  R          -> restaurar a track ao estado anterior à correção
  BACKSPACE  -> limpa a track
  ESC        -> sai
"""

from pynput import keyboard


class TecladoInput:
    # Pentatônica menor de Lá: A3 C4 D4 E4 G4
    MAPA = {
        'a': 57,  # A3
        's': 60,  # C4
        'd': 62,  # D4
        'f': 64,  # E4
        'g': 67,  # G4
    }

    def __init__(self, studio, track_i=0):
        self.studio = studio
        self.track_i = track_i
        self._ativas = set()   # debounce: evita retrigger enquanto a tecla segue pressionada

    def _on_press(self, key):
        try:
            char = key.char
        except AttributeError:
            if key == keyboard.Key.esc:
                return False            # encerra o listener
            if key == keyboard.Key.backspace:
                self.studio.limpar_track(self.track_i)
                print("  track limpa")
            return

        if char in self.MAPA and char not in self._ativas:
            self._ativas.add(char)
            self.studio.nota_on(self.track_i, self.MAPA[char])
            print(f"[{char.upper()}] nota {self.MAPA[char]} ON")
        elif char == 'c' and 'c' not in self._ativas:
            self._ativas.add('c')
            self.studio.corrigir_track(self.track_i)
            print("  >> track corrigida (R restaura)")
        elif char == 'r' and 'r' not in self._ativas:
            self._ativas.add('r')
            self.studio.restaurar_track(self.track_i)
            print("  >> track restaurada")

    def _on_release(self, key):
        try:
            char = key.char
        except AttributeError:
            return

        if char in self.MAPA and char in self._ativas:
            self._ativas.discard(char)
            self.studio.nota_off(self.track_i, self.MAPA[char])
        elif char in ('c', 'r'):
            self._ativas.discard(char)

    def executar(self):
        # Bloqueia até o usuário apertar ESC.
        with keyboard.Listener(on_press=self._on_press, on_release=self._on_release) as listener:
            listener.join()
