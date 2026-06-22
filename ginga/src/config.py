"""Constantes e valores padrão do sistema.

Aqui ficam só defaults imutáveis. Estado que muda em runtime (BPM atual,
metrônomo ligado/desligado, volume) vive nas instâncias, não aqui.
"""

from pathlib import Path

# Raiz do projeto (ginga/), resolvida a partir da localização deste arquivo
# (ginga/src/config.py) — independe do diretório de onde o sistema é executado.
RAIZ = Path(__file__).resolve().parent.parent

SOUNDFONT = str(RAIZ / "assets" / "soundfonts" / "GeneralUser-GS.sf2")
DRIVER    = "coreaudio"   # macOS; use "alsa" no Linux, "dsound" no Windows
GAIN      = 0.8

# --- Tempo / resolução ---
BPM_PADRAO     = 120
BEATS_POR_LOOP = 16
PPQ            = 480      # pulses per quarter note — ticks por beat

# --- Canais MIDI ---
CANAL_INSTRUMENTO = 1
CANAL_METRONOMO   = 15    # melódico livre (evita o 9, reservado à percussão GM)

# --- Instrumento do usuário ---
PRESET_INSTRUMENTO = 27   # Electric Guitar (Clean)
VEL_PADRAO         = 90

# --- Metrônomo ---
PRESET_METRONOMO = 115    # Woodblock
METRO_NOTA_FORTE = 76     # primeiro beat do compasso
METRO_NOTA_FRACA = 77     # demais beats
METRO_VEL_FORTE  = 110
METRO_VEL_FRACA  = 70
METRO_VOLUME     = 100    # volume inicial do canal (CC7)
