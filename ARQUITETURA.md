# Arquitetura do Sistema

Documento de referência para a integração dos três módulos desenvolvidos pelo
grupo num único sistema. Descreve a estrutura de pacotes, as fronteiras entre os
módulos e as decisões de design já tomadas. É um guia de destino — a migração do
código atual é gradual (ver [Migração](#migração)).

## Visão geral

O sistema é um **looper/gravador musical** com correção automática e interface
gráfica. Três módulos principais, mais um modelo de dados compartilhado:

- **`model`** — modelo de dados da música (`Event`, `Track`). Só dados, sem comportamento.
- **`synth`** — som e gravação: FluidSynth, looper, e o estado da música (lista de tracks).
- **`correction`** — limpeza da música: quantização rítmica e correção melódica (via LLM).
- **`ui`** — interface Tkinter; também abriga os adaptadores de input (teclado, Arduino).

## Dependências entre módulos

A dependência é uma cadeia de mão única — não há ciclos:

```
   ui ──controla / lê tracks──►  synth ──Track──►  correction
                                   │                   │
                                   └──── importam ─────┴──► model (Event, Track)
```

- `ui` depende **só** de `synth`. Não conhece `correction`.
- `synth` depende de `correction` e a chama internamente.
- `correction` depende só de `model`. É uma função pura `Track -> Track`.
- `model` não depende de ninguém.
- Ninguém importa a `ui`.

## Modelo de dados: a `Track` é a moeda única

Toda a música circula entre os módulos como `Track`. Definição única em `model`:

- **`Event(note, duration, channel=0, velocity=0, type="note_on")`** — uma nota com
  duração explícita (em ticks).
- **`Track(key, time_signature, PPQ, events)`** — `events: dict[int, list[Event]]`,
  mapeando tick (posição no loop, independente de BPM) para a lista de notas que
  começam naquele tick.

O `Looper` grava ao vivo recebendo `nota_on`/`nota_off` e converte internamente os
pares liga/desliga em `Event` com duração; no playback expande de volta em
`note_on`/`note_off` no sequencer. Ou seja: **a conversão on/off ↔ duração mora
dentro do `synth`**, não num tradutor à parte. A fronteira entre os módulos é
simplesmente o `Track`.

## Módulo `synth`

Dono do som e do **estado da música**. Centraliza tudo numa fachada `Studio`, que é
a única superfície que a `ui` enxerga do lado do som.

- **`sintetizador.py`** — recurso de áudio (FluidSynth + Sequencer), compartilhado.
- **`metronomo.py`** — cliques de referência sincronizados ao loop.
- **`looper.py`** — engine single-track: uma `Track`, um canal MIDI. Timing,
  gravação e agendamento do loop.
- **`studio.py`** — fachada multi-track: dona da `list[Track]`, gerencia um
  `Looper` por track (todos compartilhando o mesmo `Sintetizador`/Sequencer),
  é o dono do clock e expõe a API para a UI.

### Multi-track

Cada track tem seu instrumento (logo, seu canal MIDI), então o desenho é **um
`Looper` por track**, todos sobre o mesmo `Sintetizador`. O `Studio` cria e
gerencia esses loopers.

**Subtileza de clock:** com vários loopers, apenas um agendamento de metrônomo deve
existir e todos os loopers devem compartilhar a mesma virada de loop. Por isso o
`Studio` (e não cada `Looper`) passa a ser o dono do clock na versão integrada.

### API do `Studio` (esboço)

```python
class Studio:
    def __init__(self, sint, metronomo, correction):
        self._correction = correction        # injetada; usada só em corrigir_track()
        ...

    # gestão de tracks
    def adicionar_track(self, instrumento, canal) -> int: ...
    def remover_track(self, i): ...

    # leitura para a UI (snapshot sob lock)
    @property
    def tracks(self) -> list[Track]: ...

    # input ao vivo (teclado Tk / Arduino delegam aqui)
    def nota_on(self, track_i, nota, vel): ...
    def nota_off(self, track_i, nota): ...

    # controles
    def play(self): ...
    def stop(self): ...
    def set_bpm(self, bpm): ...

    # CORREÇÃO — pronta, porém NÃO disparada por ninguém ainda
    def corrigir_track(self, i):
        corrigida = self._correction(self._loopers[i].track)
        self._loopers[i].substituir_track(corrigida)
```

## Módulo `correction`

Função pura `perform_music_adjustments(track, quantize, adjust_melody) -> Track`:
quantiza o ritmo e (opcionalmente) corrige a melodia, passando por notação ABC.
Não conhece o `synth`.

Depende de um LLM local (`ollama` / gemma3) para o modo de quantização `"AUTO"` e
para a correção melódica.

**Estado atual:** a correção está **cabeada mas dormente** — a `correction` é
injetada no `Studio` e o método `corrigir_track` está pronto, mas nenhum input ou
evento o dispara ainda. O gatilho (ex.: ao parar a gravação, ou via Arduino) será
definido depois e plugado em `corrigir_track`.

## Módulo `ui`

Interface Tkinter. É **observadora**: lê `studio.tracks` e redesenha a tela quando
necessário. Não dispara correção.

- **`app.py`** — telas Tkinter; orquestra `synth`.
- **`inputs/keyboard.py`** — teclas do Tk → `studio.nota_on/off`.
- **`inputs/arduino.py`** — leitura serial (pyserial) → `studio.nota_on/off`.

Os adaptadores de input (teclado e Arduino) são ambos "fontes de input" que só
chamam `studio.nota_on/off` — exatamente a fronteira de input-agnosticismo do
`synth`.

### Modelo de threads

O `mainloop` do Tk é single-thread; o `synth` roda no thread do Sequencer do
FluidSynth, com lock. Convivem porque a API do `synth` não bloqueia (`nota_on/off`
só agendam). Regras:

- Callbacks de botão/tecla podem chamar o `studio` direto.
- A UI nunca bloqueia esperando áudio.
- A leitura de `studio.tracks` retorna um snapshot sob lock.

### Observação da lista de tracks

A UI já roda um polling do Tk. O mesmo mecanismo serve para observar o `synth`:

```python
def atualizar_tela():
    desenhar_tracks(studio.tracks)   # lê o estado atual e redesenha
    janela.after(50, atualizar_tela)
```

Quando o `synth` altera uma track (ex.: após corrigir), o próximo tick do polling
redesenha sozinho — a UI não precisa ser avisada.

## Estrutura de pacotes

Layout `src/`, pacote único instalável (`pip install -e .`):

```
ENG4033-Grupo-A2/
├── pyproject.toml          # deps: pyfluidsynth, pynput, mido, ollama, pyserial
├── README.md
├── ARQUITETURA.md
├── assets/
│   ├── soundfonts/GeneralUser-GS.sf2
│   └── prompts/            # rhythm_prompt.txt, melody_prompt.txt
├── src/
│   └── ginga/
│       ├── __init__.py
│       ├── __main__.py     # composition root: monta sint, metronomo,
│       │                   #   correction → Studio → UI, e injeta tudo
│       ├── config.py
│       ├── model/          # Event, Track (definição única)
│       │   ├── event.py
│       │   └── track.py
│       ├── synth/
│       │   ├── sintetizador.py
│       │   ├── metronomo.py
│       │   ├── looper.py
│       │   └── studio.py
│       ├── correction/
│       │   ├── corrector.py
│       │   ├── rhythm.py
│       │   ├── melody.py
│       │   ├── abc.py
│       │   ├── midi_io.py
│       │   └── llm.py
│       └── ui/
│           ├── app.py
│           └── inputs/
│               ├── keyboard.py
│               └── arduino.py
└── tests/
    ├── test_abc.py
    └── test_looper_track.py
```

## Migração

Estratégia **aditiva**: o pacote novo em `src/` é criado ao lado das pastas atuais
(`pedro/`, `davi/`, `mariam/`), que permanecem intactas. O código migra
gradualmente para a nova estrutura; as pastas antigas só são removidas no fim.

## Pendências (decisões e ajustes em aberto)

1. **Unificar `Event`/`Track`** numa definição só em `model`. **Decidido:** a
   definição canônica é a do **Davi** — `Event(type, note, duration, channel=0,
   velocity=0)`. Ao migrar para `model`, limpar para um dataclass simples:

   ```python
   @dataclass
   class Event:
       type: str
       note: int
       duration: int
       channel: int = 0
       velocity: int = 0
   ```

   **Consequência:** o `Looper` do Pedro constrói o evento posicionalmente na
   ordem antiga (`Event(nota, duration, canal, velocity)` em
   `pedro/Sistema_Som/looper.py:89`). Com `type` como 1º campo, essa chamada fica
   deslocada — precisa virar keyword: `Event(note=nota, duration=duration,
   channel=canal, velocity=velocity)`. Os call-sites do Davi (`abc_to_track`,
   `midi_to_track_list`) já usam keywords e não mudam.
2. **Gatilho da correção** — quando o `synth` chama `corrigir_track`. Indefinido;
   por ora o método fica dormente.
3. **Dono do clock no multi-track** — mover o agendamento do metrônomo e a virada
   de loop do `Looper` para o `Studio`.
4. **Dependências de runtime** — `mido` e `ollama` (e o modelo gemma3) ainda não
   instalados no ambiente; `pyserial` necessário para o input do Arduino.
5. **Caminhos hardcoded** — `config.SOUNDFONT` aponta para um caminho absoluto
   antigo; passar a resolver via `assets/`. Prompts da `correction` hoje são
   relativos ao cwd; passar a resolver via pacote.
