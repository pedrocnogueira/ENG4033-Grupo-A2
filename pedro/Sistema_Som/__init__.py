"""Sistema_Som — looper/gravador de notas sobre FluidSynth.

Organizado em camadas:
  config        — constantes e defaults
  evento        — Evento (dado puro)
  sintetizador  — recurso de áudio (FluidSynth + Sequencer)
  metronomo     — agenda os cliques de referência
  looper        — engine: timing, gravação e agendamento do loop
  teclado       — adaptador de input (substituível)

A fronteira de integração é o Looper: qualquer fonte de input só precisa
chamar looper.nota_on / looper.nota_off.
"""
