"""arduino — adaptador de input do hardware via serial (A IMPLEMENTAR).

Lê o Arduino (pyserial) e traduz em chamadas studio.nota_on / studio.nota_off.
Substitui o lerArduino() inline que hoje vive em ui/app.py
(ex-mariam/telas_projeto.py). O polling continua sob o after() do Tk.

Esqueleto — lógica real conforme o plano de integração.
"""


class ArduinoInput:
    def __init__(self, studio, port="/dev/serial0", baudrate=9600):
        self._studio = studio
        self._port = port
        self._baudrate = baudrate

    def poll(self) -> None:
        raise NotImplementedError
