# Síntese de Audio com Python e FluidSynth

## Instalação

```bash
# 1. Instalar a biblioteca nativa
brew install fluid-synth        # macOS
sudo apt install fluidsynth     # Linux
# Windows: baixar em https://github.com/FluidSynth/fluidsynth/releases e adicionar bin/ ao PATH

# 2. Instalar o binding Python
pip install pyfluidsynth
```

## Como funciona

O FluidSynth é um sintetizador MIDI por software. O fluxo básico é sempre:

1. Criar o sintetizador e iniciar o driver de áudio
2. Carregar um arquivo **SoundFont (.sf2)** com os instrumentos
3. Selecionar um instrumento em um canal (`program_select`)
4. Disparar notas com `noteon` / `noteoff`

```python
import fluidsynth

fs = fluidsynth.Synth()
fs.start(driver="coreaudio")          # driver depende do OS (ver abaixo)

sfid = fs.sfload("caminho/para/arquivo.sf2")
fs.program_select(canal, sfid, banco, preset)

fs.noteon(canal, nota_midi, velocity) # toca a nota
fs.noteoff(canal, nota_midi)          # para a nota

fs.delete()
```

## Drivers de áudio por OS

| OS      | Driver         |
|---------|----------------|
| macOS   | `coreaudio`    |
| Linux   | `alsa`         |
| Windows | `dsound`       |

## Notas MIDI

Cada nota é um número de 0 a 127. Referência rápida:

| Nota | MIDI |
|------|------|
| C4 (Dó central) | 60 |
| A4 (Lá 440Hz)   | 69 |
| C5              | 72 |

## SoundFont utilizado

**GeneralUser GS** — cobre todos os 128 instrumentos do padrão General MIDI.

- Arquivo: `GeneralUser-GS/GeneralUser-GS.sf2`
- Download: https://schristiancollins.com/generaluser.php

Cada instrumento é identificado por `banco` + `preset`. Exemplos:

| Preset | Instrumento          |
|--------|----------------------|
| 0      | Acoustic Grand Piano |
| 25     | Acoustic Guitar      |
| 40     | Violin               |
| 73     | Flute                |
| 115    | Woodblock            |

## Documentação

- [pyfluidsynth — PyPI](https://pypi.org/project/pyfluidsynth/)
- [pyfluidsynth — GitHub](https://github.com/nwhitehead/pyfluidsynth)
- [FluidSynth API (C)](https://www.fluidsynth.org/api/)
