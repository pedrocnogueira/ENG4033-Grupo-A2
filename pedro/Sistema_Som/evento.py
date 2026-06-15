"""Evento musical — a unidade mínima gravada no loop."""

from dataclasses import dataclass


@dataclass
class Evento:
    # tipo     – "on" liga a nota, "off" desliga
    # canal    – canal MIDI (0–15)
    # nota     – número MIDI da nota (0–127)
    # velocity – intensidade (0–127); irrelevante em "off"
    #
    # A posição no tempo NÃO mora aqui: é a chave (tick) do dicionário do
    # loop. Assim o mesmo Evento pode, em tese, ser reaproveitado em ticks
    # diferentes, e a serialização para enviar a outras partes do sistema
    # fica trivial (asdict).
    tipo: str
    canal: int
    nota: int
    velocity: int = 0
