import time
import threading
import fluidsynth
from pynput import keyboard

SOUNDFONT = "/Users/pedronogueira/PUC/micro/Trabalho/GeneralUser-GS/GeneralUser-GS.sf2"

BPM             = 120
BEATS_POR_LOOP  = 4
ticks_per_beat             = 480                       # ticks por beat
TICKS_POR_LOOP  = ticks_per_beat * BEATS_POR_LOOP      # ticks no loop inteiro

# para BPM mutável -> toda conversão tick→ms lê o valor atual.
def ms_por_beat() -> float:
    return 60000 / BPM

# ---------------------------------------------------------------------------
# Metrônomo (agendado no próprio sequencer)
# ---------------------------------------------------------------------------
CANAL_METRO      = 15      # canal livre
PRESET_METRO     = 115     # Woodblock
METRO_NOTA_FORTE = 76      # primeiro beat do compasso
METRO_NOTA_FRACA = 77      # demais beats
METRO_VEL_FORTE  = 110
METRO_VEL_FRACA  = 70

metro_ativo  = True        # liga/desliga o clique -> lido por loop (vale no próximo loop)
metro_volume = 100         # volume master do canal (CC7) -> efeito imediato via set_metro_volume

# ---------------------------------------------------------------------------
# Instrumento do usuário
# ---------------------------------------------------------------------------
CANAL_GUITAR  = 1          # canal da guitarra
PRESET_GUITAR = 27         # Electric Guitar (Clean)
VEL_GRAVACAO  = 90         # velocity padrão das notas tocadas/gravadas

# ---------------------------------------------------------------------------
# Eventos globais -> começa VAZIO: o usuário grava tocando.
#
# Chave  : tick PPQ relativo dentro do loop  (0 … TICKS_POR_LOOP - 1)
# Valor  : LISTA de eventos {tipo, canal, nota, velocity, beat} -> vários
#          eventos podem cair no mesmo tick (acordes, notas simultâneas).
#
# Tocado pela thread do sequencer e gravado pela thread do teclado, então
# todo acesso é protegido por eventos_lock
# ---------------------------------------------------------------------------
eventos: dict[int, list[dict]] = {}
eventos_lock = threading.Lock()

# ---------------------------------------------------------------------------
# Sintetizador e sequencer
# ---------------------------------------------------------------------------
fs = fluidsynth.Synth(gain=0.8)
fs.start(driver="coreaudio")

sfid = fs.sfload(SOUNDFONT)
fs.program_select(CANAL_GUITAR, sfid, 0, PRESET_GUITAR)       # guitarra
fs.program_select(CANAL_METRO,  sfid, 0, PRESET_METRO)        # metrônomo -> Woodblock
fs.cc(CANAL_METRO, 7, metro_volume)                           # CC7 = volume do canal do metrônomo

sequencer = fluidsynth.Sequencer(use_system_timer=False)
synthSeqID = sequencer.register_fluidsynth(fs)

# Tick absoluto (ms) em que o loop atual começou -> atualizado a cada loop.
# Serve de referência para gravar a posição relativa das notas.
loop_inicio = 0


# ---------------------------------------------------------------------------
# Controles do metrônomo
# ---------------------------------------------------------------------------
def set_metro_volume(v: int) -> None:
    # Volume master do metrônomo via CC7 -> efeito IMEDIATO (não espera o loop).
    global metro_volume
    metro_volume = max(0, min(127, v))
    fs.cc(CANAL_METRO, 7, metro_volume)


def schedule_metronomo(inicio: int, ms_por_tick: float) -> None:
    # Um clique por beat, na mesma régua de tempo da música.
    if not metro_ativo:
        return
    for beat in range(BEATS_POR_LOOP):
        t = inicio + round(beat * ticks_per_beat * ms_por_tick)
        nota = METRO_NOTA_FORTE if beat == 0 else METRO_NOTA_FRACA
        vel  = METRO_VEL_FORTE if beat == 0 else METRO_VEL_FRACA
        sequencer.note_on(t, CANAL_METRO, nota, vel, dest=synthSeqID)
        sequencer.note_off(t + 20, CANAL_METRO, nota, dest=synthSeqID)


# ---------------------------------------------------------------------------
# Gravação
# ---------------------------------------------------------------------------
def tick_relativo_atual() -> int:
    # Onde estamos AGORA dentro do loop, em ticks PPQ (0 … TICKS_POR_LOOP-1).
    ms_rel = sequencer.get_tick() - loop_inicio
    tick = round(ms_rel / (ms_por_beat() / ticks_per_beat))
    return tick % TICKS_POR_LOOP


def registrar_evento(tick: int, ev: dict) -> None:
    # Grava um evento, anexando à lista do tick. Vários eventos no mesmo
    # tick convivem (acordes, notas simultâneas).
    with eventos_lock:
        eventos.setdefault(tick, []).append(ev)


# ---------------------------------------------------------------------------
# API externa -> aciona o som e grava no loop.
#
# É a fronteira de integração -> qualquer fonte de input (teclado hoje; MIDI,
# rede ou GUI no futuro) só precisa chamar nota_on/nota_off. O engine não
# sabe nada sobre de onde veio o comando.
# ---------------------------------------------------------------------------
def nota_on(nota: int, velocity: int = VEL_GRAVACAO, canal: int = CANAL_GUITAR) -> int:
    # Toca ao vivo (monitoração) e grava o evento ON no tick atual.
    # Retorna o tick em que foi gravado.
    fs.noteon(canal, nota, velocity)
    tick = tick_relativo_atual()
    registrar_evento(tick, {
        "tipo": "on", "canal": canal, "nota": nota,
        "velocity": velocity, "beat": tick // ticks_per_beat + 1,
    })
    return tick


def nota_off(nota: int, canal: int = CANAL_GUITAR) -> int:
    # Para a nota ao vivo e grava o evento OFF no tick atual.
    fs.noteoff(canal, nota)
    tick = tick_relativo_atual()
    registrar_evento(tick, {
        "tipo": "off", "canal": canal, "nota": nota,
        "velocity": 0, "beat": tick // ticks_per_beat + 1,
    })
    return tick


def limpar_loop() -> None:
    # Apaga tudo que foi gravado -> recomeça do zero.
    with eventos_lock:
        eventos.clear()
    print("  loop limpo")


# ---------------------------------------------------------------------------
# Agendamento do loop
# ---------------------------------------------------------------------------
def set_loop(inicio: int) -> None:
    # Agenda no sequencer os eventos gravados + o metrônomo para este loop.
    # Lê eventos e BPM agora -> o que foi gravado/alterado já vale neste loop.
    ms_por_tick = ms_por_beat() / ticks_per_beat

    # Snapshot sob lock -> a thread do teclado pode estar gravando ao mesmo tempo.
    with eventos_lock:
        snapshot = list(eventos.items())

    for tick_rel, lista in snapshot:
        t = inicio + round(tick_rel * ms_por_tick)
        for ev in lista:
            if ev["tipo"] == "on":
                sequencer.note_on(t, ev["canal"], ev["nota"], ev["velocity"], dest=synthSeqID)
            else:
                sequencer.note_off(t, ev["canal"], ev["nota"], dest=synthSeqID)

    schedule_metronomo(inicio, ms_por_tick)

    dur_loop_ms = round(TICKS_POR_LOOP * ms_por_tick)
    sequencer.timer(inicio + dur_loop_ms, dest=mySeqID)


def loop_callback(time, event, seq, data) -> None:
    # Início de um novo loop -> registra a referência de tempo e reagenda.
    global loop_inicio
    loop_inicio = time
    set_loop(time)


# ---------------------------------------------------------------------------
# Adaptador de teclado (única parte que conhece o pynput) 
# 
# traduz tecla para nota e delega ao engine.
#
# Para trocar a fonte de input no futuro, basta substituir este bloco.
# ---------------------------------------------------------------------------
# Pentatônica menor de Lá -> A3 C4 D4 E4 G4
MAPA_TECLAS = {
    'a': 57,  # A3
    's': 60,  # C4
    'd': 62,  # D4
    'f': 64,  # E4
    'g': 67,  # G4
}

teclas_ativas = set()  # debounce

def on_press(key):
    try:
        char = key.char
    except AttributeError:
        if key == keyboard.Key.esc:
            return False
        if key == keyboard.Key.backspace:
            limpar_loop()
        return

    if char in MAPA_TECLAS and char not in teclas_ativas:
        teclas_ativas.add(char)
        tick = nota_on(MAPA_TECLAS[char])
        print(f"[{char.upper()}] nota {MAPA_TECLAS[char]} ON  @tick {tick}")

def on_release(key):
    try:
        char = key.char
    except AttributeError:
        return

    if char in MAPA_TECLAS and char in teclas_ativas:
        teclas_ativas.discard(char)
        nota_off(MAPA_TECLAS[char])


# ---------------------------------------------------------------------------
# Início
# ---------------------------------------------------------------------------
mySeqID = sequencer.register_client("loop_callback", loop_callback)

def iniciar_loop() -> None:
    # Começa o agendamento do loop a partir de agora.
    global loop_inicio
    loop_inicio = sequencer.get_tick()
    set_loop(loop_inicio)


def encerrar() -> None:
    # Libera os recursos de áudio.
    sequencer.delete()
    fs.delete()


def main() -> None:
    print(f"BPM={BPM} | {BEATS_POR_LOOP} beats/loop | PPQ={ticks_per_beat}")
    print(f"Metrônomo: canal {CANAL_METRO} | ativo={metro_ativo} | volume={metro_volume}")
    print("Guitarra - pentatônica menor de Lá:")
    print("  A=57  S=60  D=62  F=64  G=67")
    print("Toque para gravar no loop. BACKSPACE limpa. ESC sai.\n")

    iniciar_loop()
    try:
        with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
            listener.join()
    finally:
        encerrar()
        print("Encerrado.")


if __name__ == "__main__":
    main()
