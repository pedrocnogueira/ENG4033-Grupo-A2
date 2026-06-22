"""keyboard — adaptador de input do teclado via Tkinter (A IMPLEMENTAR).

Traduz <KeyPress>/<KeyRelease> das teclas (A S D F G) em chamadas
studio.nota_on / studio.nota_off. Substitui o handler inline que hoje vive em
ui/app.py (ex-mariam/telas_projeto.py) e o adaptador pynput de synth/teclado.py.

Esqueleto — lógica real conforme o plano de integração.
"""


class KeyboardInput:
    def __init__(self, studio):
        self._studio = studio

    def bind(self, janela) -> None:
        raise NotImplementedError
