"""TecladoInput — adaptador de input por teclado.

Única parte do sistema que conhece o pynput. Traduz tecla -> nota e delega
ao Looper. Para trocar a fonte de input no futuro, escreve-se outro adaptador
com a mesma ideia (chamar looper.nota_on / nota_off) e o engine não muda.
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

    def __init__(self, looper):
        self.looper = looper
        self._ativas = set()   # debounce: evita retrigger enquanto a tecla segue pressionada

    def _on_press(self, key):
        try:
            char = key.char
        except AttributeError:
            if key == keyboard.Key.esc:
                return False            # encerra o listener
            if key == keyboard.Key.backspace:
                self.looper.limpar()
                print("  loop limpo")
            return

        if char in self.MAPA and char not in self._ativas:
            self._ativas.add(char)
            tick = self.looper.nota_on(self.MAPA[char])
            print(f"[{char.upper()}] nota {self.MAPA[char]} ON  @tick {tick}")

    def _on_release(self, key):
        try:
            char = key.char
        except AttributeError:
            return

        if char in self.MAPA and char in self._ativas:
            self._ativas.discard(char)
            self.looper.nota_off(self.MAPA[char])

    def executar(self):
        # Bloqueia até o usuário apertar ESC.
        with keyboard.Listener(on_press=self._on_press, on_release=self._on_release) as listener:
            listener.join()
