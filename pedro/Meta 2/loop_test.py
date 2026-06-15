import time
import fluidsynth

SOUNDFONT = "/Users/pedronogueira/PUC/micro/Trabalho/GeneralUser-GS/GeneralUser-GS.sf2"

BPM             = 120
BEATS_POR_LOOP  = 4
PPQ             = 480                       # ticks (pulsos) por beat — resolução musical
TICKS_POR_LOOP  = PPQ * BEATS_POR_LOOP      # 1920 ticks no loop inteiro

# BPM é mutável em runtime; toda conversão tick→ms lê o valor atual.
def ms_por_beat() -> float:
    return 60_000 / BPM

# ---------------------------------------------------------------------------
# Metrônomo (agendado no próprio sequencer)
#
# Canal dedicado, fora do canal 0 da música. As variáveis de controle são
# lidas a cada loop dentro de set_loop, então ligar/desligar e mudar volume
# passam a valer no próximo loop — exatamente o comportamento desejado.
# ---------------------------------------------------------------------------
CANAL_METRO     = 15       # canal melódico livre (evita o 9, reservado à percussão GM)
PRESET_METRO    = 115      # Woodblock
METRO_NOTA_FORTE = 76      # primeiro beat do compasso
METRO_NOTA_FRACA = 77      # demais beats
METRO_VEL_FORTE  = 110     # velocity fixa — define só o caráter forte/fraco do clique
METRO_VEL_FRACA  = 70

metro_ativo  = True        # liga/desliga o clique — lido por loop (vale no próximo loop)
metro_volume = 100         # volume master do canal (CC7) — efeito imediato via set_metro_volume

# ---------------------------------------------------------------------------
# Eventos globais
#
# Chave  : tick PPQ relativo dentro do loop  (0 … TICKS_POR_LOOP - 1)
#          Independente de BPM: beat N começa em N * PPQ.
#          Subdivisões: PPQ=480 → colcheia=240, semicolcheia=120, etc.
# Valor  : dicionário com os campos do evento
#
# Estrutura do evento:
#   tipo      – "on" | "off"
#   canal     – canal MIDI (0–15)
#   nota      – número MIDI da nota (0–127)
#   velocity  – intensidade (0–127); ignorado em "off"
#   beat      – beat dentro do compasso em que o evento cai (1–4), apenas informativo
# ---------------------------------------------------------------------------
eventos: dict[int, dict] = {
    #  beat 1  (tick 0)
       0: {"tipo": "on",  "canal": 0, "nota": 60, "velocity": 90, "beat": 1},   # C4 on
     432: {"tipo": "off", "canal": 0, "nota": 60, "velocity":  0, "beat": 1},   # C4 off

    #  beat 2  (tick 480)
     480: {"tipo": "on",  "canal": 0, "nota": 64, "velocity": 80, "beat": 2},   # E4 on
     912: {"tipo": "off", "canal": 0, "nota": 64, "velocity":  0, "beat": 2},   # E4 off

    #  beat 3  (tick 960)
     960: {"tipo": "on",  "canal": 0, "nota": 67, "velocity": 85, "beat": 3},   # G4 on
    1392: {"tipo": "off", "canal": 0, "nota": 67, "velocity":  0, "beat": 3},   # G4 off

    #  beat 4  (tick 1440)
    1440: {"tipo": "on",  "canal": 0, "nota": 72, "velocity": 90, "beat": 4},   # C5 on
    1872: {"tipo": "off", "canal": 0, "nota": 72, "velocity":  0, "beat": 4},   # C5 off
}

# ---------------------------------------------------------------------------
# Sintetizador e sequencer
# ---------------------------------------------------------------------------
fs = fluidsynth.Synth(gain=0.8)
fs.start(driver="coreaudio")

sfid = fs.sfload(SOUNDFONT)
fs.program_select(0, sfid, 0, 0)  # canal 0 → Acoustic Grand Piano
fs.program_select(CANAL_METRO, sfid, 0, PRESET_METRO)  # canal do metrônomo → Woodblock
fs.cc(CANAL_METRO, 7, metro_volume)  # CC7 = volume do canal; inicializa o volume master

sequencer = fluidsynth.Sequencer(use_system_timer=False)
synthSeqID = sequencer.register_fluidsynth(fs)


def set_metro_volume(v: int) -> None:
    # Volume master do metrônomo via CC7 — efeito IMEDIATO (não espera o loop).
    # É só uma referência de usabilidade pro usuário, então mudança instantânea
    # faz mais sentido que esperar o próximo loop.
    global metro_volume
    metro_volume = max(0, min(127, v))
    fs.cc(CANAL_METRO, 7, metro_volume)


def schedule_metronomo(inicio: int, ms_por_tick: float) -> None:
    # Agenda um clique por beat no canal do metrônomo, usando a mesma
    # conversão tick->ms da música (sincronia perfeita, sem drift).
    # Lê metro_ativo agora: ligar/desligar vale a partir deste loop.
    # O volume é controlado à parte pelo CC7 (set_metro_volume), instantâneo.
    if not metro_ativo:
        return
    for beat in range(BEATS_POR_LOOP):
        t = inicio + round(beat * PPQ * ms_por_tick)
        nota = METRO_NOTA_FORTE if beat == 0 else METRO_NOTA_FRACA
        vel  = METRO_VEL_FORTE if beat == 0 else METRO_VEL_FRACA
        sequencer.note_on(t, CANAL_METRO, nota, vel, dest=synthSeqID)
        sequencer.note_off(t + 20, CANAL_METRO, nota, dest=synthSeqID)


def set_loop(inicio: int) -> None:
    # Agenda no sequencer todos os eventos do loop atual.

    # Lê eventos E o BPM no momento da chamada - alterações feitas
    # externamente durante a reprodução já valem para o próximo loop.

    # Fator de conversão tick PPQ -> ms, congelado para este loop.
    ms_por_tick = ms_por_beat() / PPQ

    for tick_rel, ev in eventos.items():
        t = inicio + round(tick_rel * ms_por_tick)
        if ev["tipo"] == "on":
            sequencer.note_on(t, ev["canal"], ev["nota"], ev["velocity"], dest=synthSeqID)
        else:
            sequencer.note_off(t, ev["canal"], ev["nota"], dest=synthSeqID)

    # Metrônomo no mesmo loop, compartilhando o fator de conversão.
    schedule_metronomo(inicio, ms_por_tick)

    # Duração do loop em ms com o BPM atual; o próximo callback usa o BPM
    # que estiver valendo lá na frente.
    dur_loop_ms = round(TICKS_POR_LOOP * ms_por_tick)
    sequencer.timer(inicio + dur_loop_ms, dest=mySeqID)
    # print(f"  loop agendado: inicio={inicio}  BPM={BPM}  dur={dur_loop_ms}ms")


def loop_callback(time, event, seq, data) -> None:
    # Chamado pelo sequencer no início de cada novo loop.
    set_loop(time)


mySeqID = sequencer.register_client("loop_callback", loop_callback)

# ---------------------------------------------------------------------------
# Início
# ---------------------------------------------------------------------------
print(f"BPM={BPM} | {BEATS_POR_LOOP} beats/loop | {TICKS_POR_LOOP} ticks/loop (PPQ={PPQ})")
print(f"Metrônomo: canal {CANAL_METRO} | ativo={metro_ativo} | volume={metro_volume}")
print("Rodando em loop. Ctrl+C para sair.\n")

now = sequencer.get_tick()
set_loop(now)

try:
    while True:
        time.sleep(0.5)
except KeyboardInterrupt:
    print("\nEncerrando.")
finally:
    sequencer.delete()
    fs.delete()
