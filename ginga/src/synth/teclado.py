"""TecladoInput — adaptador de input por teclado (CLI, via pynput).

Única parte do sistema que conhece o pynput. Traduz tecla -> nota e delega ao
Studio. É a fonte de input legada da CLI; na GUI quem captura tecla é o Tk
(ui/inputs/keyboard.py). Mantido aqui para testar a integração sem UI.

Teclas:
  1 2 3      -> seleciona a track ativa (onde as notas são gravadas)
  A S D F G  -> notas (pentatônica menor de Lá) na track ativa
  C          -> corrigir a track ativa (módulo de correção)
  R          -> restaurar a track ativa ao estado anterior à correção
  BACKSPACE  -> limpa a track ativa
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

    def __init__(self, studio, n_tracks=1):
        self.studio = studio
        self.n_tracks = n_tracks
        self.track_i = 0
        self._notas: dict[str, int] = {}   # char -> track onde a nota foi pressionada
        self._acoes: set[str] = set()      # debounce de teclas de ação (C/R)

    def _on_press(self, key):
        try:
            char = key.char
        except AttributeError:
            if key == keyboard.Key.esc:
                return False            # encerra o listener
            if key == keyboard.Key.backspace:
                self.studio.limpar_track(self.track_i)
                print(f"  track {self.track_i + 1} limpa")
            return

        if char in self.MAPA:
            if char in self._notas:
                return                  # debounce: tecla já segurada
            self._notas[char] = self.track_i
            self.studio.nota_on(self.track_i, self.MAPA[char])
            print(f"[{char.upper()}] nota {self.MAPA[char]} ON  (track {self.track_i + 1})")
        elif char in ('1', '2', '3'):
            idx = int(char) - 1
            if idx < self.n_tracks and idx != self.track_i:
                self.track_i = idx
                print(f"== track {char} ativa ==")
        elif char == 'c':
            if 'c' in self._acoes:
                return
            self._acoes.add('c')
            self.studio.corrigir_track(self.track_i)
            print(f"  >> track {self.track_i + 1} corrigida (R restaura)")
        elif char == 'r':
            if 'r' in self._acoes:
                return
            self._acoes.add('r')
            self.studio.restaurar_track(self.track_i)
            print(f"  >> track {self.track_i + 1} restaurada")

    def _on_release(self, key):
        try:
            char = key.char
        except AttributeError:
            return

        if char in self._notas:
            ti = self._notas.pop(char)         # solta na track onde pressionou
            self.studio.nota_off(ti, self.MAPA[char])
        elif char in self._acoes:
            self._acoes.discard(char)

    def executar(self):
        # Bloqueia até o usuário apertar ESC.
        with keyboard.Listener(on_press=self._on_press, on_release=self._on_release) as listener:
            listener.join()
