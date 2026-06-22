"""ginga — looper/gravador musical com correção automática e UI.

Pacote unificado do trabalho. Estrutura (ver ARQUITETURA.md na raiz):

  model       — Event, Track (dados puros, sem comportamento)
  synth       — som e gravação (FluidSynth, looper, studio)
  correction  — quantização rítmica + correção melódica (Track -> Track)
  ui          — interface Tkinter + adaptadores de input (teclado, Arduino)

Dependências: ui -> synth -> correction, todos -> model.
"""
