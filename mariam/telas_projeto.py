import tkinter as tk
from tkinter import ttk, font, messagebox
from serial import Serial, SerialException
from serial.tools import list_ports


# Cores do projeto
azul = "#929EFA"
branco = "#F8F9FC"

# Teclas que podem ser apertadas
listaTeclas = ["a", "s", "d", "f", "g"]

# Mapear botões do Arduino para teclas
mapaBotoes = {"1": "a", "2": "s", "3": "d", "4": "f", "5": "g"}


def conectar_arduino():
    portas = list_ports.comports()

    for porta in portas:
        print("Porta encontrada:", porta.device, "-", porta.description)

        if "ttyUSB" in porta.device or "ttyACM" in porta.device:
            try:
                arduino = Serial(porta.device, baudrate=9600, timeout=0.1)
                print("Arduino conectado em", porta.device)
                return arduino
            except SerialException as e:
                print("Erro ao conectar em", porta.device)
                print(e)

    try:
        arduino = Serial("/dev/ttyUSB0", baudrate=9600, timeout=0.1)
        print("Arduino conectado em /dev/ttyUSB0")
        return arduino
    except SerialException as e:
        print("Arduino não conectado")
        print(e)
        return None


def run():
    arduino = conectar_arduino()

    janela = tk.Tk()
    janela.geometry("800x600")
    janela.minsize(800, 600)
    janela.configure(bg=branco)

    fonteBase = font.Font(family="Segoe UI", size=11, weight="bold")
    fonteTitulo = font.Font(family="Segoe UI", size=24, weight="bold")

    frameInicial = tk.Frame(janela, bg=branco)
    frameConfig = tk.Frame(janela, bg=branco)
    frameTracks = tk.Frame(janela, bg=branco)
    frameInstrumento = tk.Frame(janela, bg=branco)
    frameEditor = tk.Frame(janela, bg=branco)

    listaTracks = []

    configProjeto = {"nota": "", "bpm": 0, "tempo": 0}

    trackAtual = None
    cursorX = 40

    posicoesTeclas = {}

    teclasAtivas = {}
    for t in listaTeclas:
        teclasAtivas[t] = None

    retangulos = []

    corBend = "#FF8FA3"
    corNotaAtual = azul

    gravando = False
    tocando = False

    # Controle via encoder na tela de configuração
    seletorConfigAtual = "nota"
    indiceNotaAtual = 0
    bpmAtual = 120
    indiceInstrumentoAtual = 0
    indiceTrackSelecionada = 0
    framesTracks = []

    # =========================
    # Comunicação com Arduino
    # =========================

    def lerArduino():
        if arduino is not None and arduino.in_waiting > 0:
            texto_recebido = arduino.readline().decode(errors="ignore").strip()

            if texto_recebido:
                print("Texto recebido do Arduino:", texto_recebido)
                processarArduino(texto_recebido)

        janela.after(50, lerArduino)

    def processarArduino(texto):
        nonlocal corNotaAtual

        texto = texto.lower().strip()
        print("Processando texto recebido do Arduino:", texto)

        if texto in ["aumentou", "abaixou", "avancou"]:
            processarEncoder(texto)
            return
        

        # processar sensor de distância:
        if texto == "perto":
            corNotaAtual = azul
            return

        if texto == "longe":
            corNotaAtual = corBend
            return

        partes = texto.split()

        if len(partes) < 3:
            return

        if partes[0] not in ["botao", "botão"]:
            return

        numeroBotao = partes[1]
        acao = partes[2]

        if numeroBotao not in mapaBotoes:
            return

        tecla = mapaBotoes[numeroBotao]

        if acao == "pressionado":
            pressionarTecla(tecla)
        elif acao == "solto":
            soltarTecla(tecla)
    
    def atualizarSelecaoTrack():
        for i in range(len(framesTracks)):
            if i == indiceTrackSelecionada:
                destacarWidget(framesTracks[i])
            else:
                normalWidget(framesTracks[i])

    def processarEncoder(comando):
        if frameConfig.winfo_ismapped():
            processarEncoderConfig(comando)

        elif frameTracks.winfo_ismapped():
            processarEncoderTracks(comando)

        elif frameInstrumento.winfo_ismapped():
            processarEncoderInstrumento(comando)
    

    # Para simular com o teclado do computador:
    # Encoder:
    def simularEncoderAumentou(event):
        processarEncoder("aumentou")

    def simularEncoderAbaixou(event):
        processarEncoder("abaixou")

    def simularEncoderAvancou(event):
        processarEncoder("avancou")

    # Sensor de distância:
    def simularDistanciaPerto(event):
        processarArduino("perto")

    def simularDistanciaLonge(event):
        processarArduino("longe")

    def processarEncoderConfig(comando):
        nonlocal seletorConfigAtual, indiceNotaAtual, bpmAtual
        if seletorConfigAtual == "nota":
            if comando == "aumentou":
                indiceNotaAtual = (indiceNotaAtual + 1) % len(notas)
                entradaNota.current(indiceNotaAtual)

            elif comando == "abaixou":
                indiceNotaAtual = (indiceNotaAtual - 1) % len(notas)
                entradaNota.current(indiceNotaAtual)

            elif comando == "avancou":
                seletorConfigAtual = "bpm"
                entradaBPM.focus_set()
                print("Selecionando BPM")

        elif seletorConfigAtual == "bpm":
            if comando == "aumentou":
                bpmAtual += 1
                if bpmAtual > 250:
                    bpmAtual = 250

                entradaBPM.delete(0, "end")
                entradaBPM.insert(0, str(bpmAtual))

            elif comando == "abaixou":
                bpmAtual -= 1
                if bpmAtual < 40:
                    bpmAtual = 40

                entradaBPM.delete(0, "end")
                entradaBPM.insert(0, str(bpmAtual))

            elif comando == "avancou":
                salvarConfig()

    def processarEncoderTracks(comando):
        nonlocal indiceTrackSelecionada
        if len(listaTracks) == 0:
            return

        if comando == "aumentou":
            indiceTrackSelecionada = (indiceTrackSelecionada + 1) % len(listaTracks)
            atualizarSelecaoTrack()

        elif comando == "abaixou":
            indiceTrackSelecionada = (indiceTrackSelecionada - 1) % len(listaTracks)
            atualizarSelecaoTrack()

        elif comando == "avancou":
            abrirTrack(indiceTrackSelecionada + 1)


    def processarEncoderInstrumento(comando):
        nonlocal indiceInstrumentoAtual

        if comando == "aumentou":
            indiceInstrumentoAtual = (indiceInstrumentoAtual + 1) % len(instrumentos)
            entradaInstrumento.current(indiceInstrumentoAtual)

        elif comando == "abaixou":
            indiceInstrumentoAtual = (indiceInstrumentoAtual - 1) % len(instrumentos)
            entradaInstrumento.current(indiceInstrumentoAtual)

        elif comando == "avancou":
            salvarInstrumento()



    # =========================
    # UI
    # =========================

    def mostrarTela(tela):
        tela.place(relx=0.5, rely=0.5, anchor="center")

    def abrirConfig():
        nonlocal seletorConfigAtual

        seletorConfigAtual = "nota"

        frameInicial.place_forget()
        mostrarTela(frameConfig)
        entradaNota.focus_set()

    def voltarInicio():
        frameConfig.place_forget()
        mostrarTela(frameInicial)

    def voltarConfig():
        frameTracks.place_forget()
        mostrarTela(frameConfig)

    def salvarConfig():
        nonlocal bpmAtual

        nota = entradaNota.get()

        try:
            bpm = int(entradaBPM.get())
        except ValueError:
            messagebox.showerror("Erro", "BPM inválido.")
            return

        bpmAtual = bpm
        tempo = 960 / bpm

        configProjeto["nota"] = nota
        configProjeto["bpm"] = bpm
        configProjeto["tempo"] = tempo

        print(configProjeto)

        frameConfig.place_forget()
        mostrarTela(frameTracks)
        

    def salvarInstrumento():
        instrumento = entradaInstrumento.get()

        if instrumento == "":       # Não aceita campo vazio para instrumento
            messagebox.showerror("Erro", "Escolha um instrumento.")
            return
    
        listaTracks[trackAtual]["instrumento"] = instrumento

        print(instrumento)
        print(listaTracks)

        frameInstrumento.place_forget()
        mostrarTela(frameEditor)

    def voltarTracks():
        frameInstrumento.place_forget()
        mostrarTela(frameTracks)

    def salvarTrack():
        if gravando:
            print("Botão salvar apertado mas ignorado: gravação em andamento")
            return

        if retangulos == []:
            messagebox.showerror("Track vazio", "Você não tem nada para salvar.")
            return

        pergunta = "Salvar track %d?" % (trackAtual + 1)
        resposta = messagebox.askyesno("Salvar", pergunta)

        if resposta:
            listaTracks[trackAtual]["salvo"] = True

    def cancelarTrack():
        resposta = True

        if listaTracks[trackAtual]["salvo"] == False:
            resposta = messagebox.askyesno(
                "Seu progresso não foi salvo",
                "Tem certeza que deseja voltar e perder seu progresso desse track?"
            )

        if resposta:
            frameEditor.place_forget()
            mostrarTela(frameTracks)
            janela.unbind("<KeyPress>")
            janela.unbind("<KeyRelease>")

    def destacarWidget(widget):
        widget.config(bd=3, bg="#EEF1FF")

    def normalWidget(widget):
        widget.config(bd=1, bg="white")

    def destacar(event):
        destacarWidget(event.widget)

    def normal(event):
        normalWidget(event.widget)

    def destacarAdicionar(event):
        event.widget.config(bd=1, bg="#EEF1FF", fg="black")

    def normalAdicionar(event):
        event.widget.config(bd=1, bg=azul, fg="white")

    def posicoesEditor(lista_y):
        for i in range(len(lista_y) - 1):
            posicoesTeclas[listaTeclas[i]] = {
                "y1": lista_y[i],
                "y2": lista_y[i + 1]
            }

    def pressionarTecla(tecla):
        print(tecla)

        if tecla not in listaTeclas:
            return

        if teclasAtivas[tecla] is not None:
            return

        if tecla not in posicoesTeclas:
            return

        y1 = posicoesTeclas[tecla]["y1"]
        y2 = posicoesTeclas[tecla]["y2"]

        retangulo = canvasMusica.create_rectangle(
            cursorX,
            y1,
            cursorX,
            y2,
            fill=corNotaAtual,
            outline=""
        )

        retangulos.append(retangulo)
        teclasAtivas[tecla] = retangulo
        canvasMusica.tag_lower(retangulo)

    def soltarTecla(tecla):
        if tecla not in listaTeclas:
            return

        teclasAtivas[tecla] = None

    def teclaPressionada(event):
        pressionarTecla(event.keysym)

    def teclaSolta(event):
        soltarTecla(event.keysym)

    def abrirTrack(numero):
        nonlocal trackAtual

        trackAtual = numero - 1

        frameTracks.place_forget()
        mostrarTela(frameInstrumento)

        print("Track %d selecionada" % numero)

        janela.bind("<KeyPress>", teclaPressionada)
        janela.bind("<KeyRelease>", teclaSolta)

    def criarTrack(numero, tipo):
        frameEspaco = tk.Frame(frameListaTracks, bg=branco, width=450, height=65)
        frameTrack = tk.Frame(
            frameEspaco,
            width=450,
            height=65,
            bg="white",
            relief="solid",
            bd=1
        )
        framesTracks.append(frameTrack)

        if tipo == "melodia":
            simbolo = "🎵"
        else:
            simbolo = "🥁"

        icone = tk.Label(frameEspaco, text=simbolo, bg=branco, font=22)

        frameTrack.bind("<Button-1>", lambda event: abrirTrack(numero))

        frameEspaco.pack(pady=5)
        frameTrack.pack(side="left")
        icone.pack(side="left")

        frameTrack.bind("<Enter>", destacar)
        frameTrack.bind("<Leave>", lambda event: atualizarSelecaoTrack())

        track = {
            "numero": numero,
            "tipo": tipo,
            "instrumento": "",
            "notas": [],
            "salvo": False
        }

        listaTracks.append(track)
        

    def atualizarTempo():
        nonlocal cursorX, tocando, gravando

        if not tocando:
            return

        cursorX += 2
        gravando = True

        if cursorX > 650:
            gravando = False
            tocando = False
            cursorX = 40
            canvasMusica.coords(cursorTempo, cursorX, 0, cursorX, 30)
            return

        canvasMusica.coords(cursorTempo, cursorX, 0, cursorX, 30)

        for tecla, retangulo in teclasAtivas.items():
            if retangulo is not None:
                coords = canvasMusica.coords(retangulo)
                canvasMusica.coords(
                    retangulo,
                    coords[0],
                    coords[1],
                    cursorX,
                    coords[3]
                )
                canvasMusica.tag_lower(retangulo)

        janela.after(50, atualizarTempo)

    def iniciar():
        nonlocal tocando

        if not tocando:
            tocando = True
            atualizarTempo()

    def excluir():
        nonlocal cursorX, gravando, tocando

        voltar = False

        if tocando:
            voltar = True
            pausar()

        resposta = messagebox.askyesno(
            "Limpar Track",
            "Tem certeza que deseja apagar todas as notas desse track? \n"
            "Se o track já estiver salvo e você excluí-lo, ele só será substituído "
            "caso você grave novamente e salve."
        )

        if resposta:
            cursorX = 40
            gravando = False
            tocando = False

            canvasMusica.coords(cursorTempo, cursorX, 0, cursorX, 30)

            for retangulo in retangulos:
                canvasMusica.delete(retangulo)

            retangulos.clear()

            for tecla in teclasAtivas:
                teclasAtivas[tecla] = None
        else:
            if voltar:
                iniciar()

    def pausar():
        nonlocal tocando, gravando
        tocando = False
        gravando = False

    def playPause():
        if tocando:
            pausar()
        else:
            iniciar()

    # =========================
    # Tela inicial
    # =========================

    mostrarTela(frameInicial)

    botaoNovo = tk.Button(
        frameInicial,
        text="Novo Projeto",
        font=fonteBase,
        bg=azul,
        fg="white",
        width=18,
        height=2,
        command=abrirConfig
    )

    botaoAbrir = tk.Button(
        frameInicial,
        text="Abrir Projeto",
        font=fonteBase,
        bg=azul,
        fg="white",
        width=18,
        height=2
    )

    logo = tk.Label(
        frameInicial,
        text="Logo do Projeto",
        font=fonteTitulo,
        bg=branco
    )

    logo.pack(pady=10)
    botaoNovo.pack(pady=10)
    botaoAbrir.pack(pady=10)

    # =========================
    # Tela configurações
    # =========================

    labelNota = tk.Label(frameConfig, text="Nota", bg=branco, font=fonteBase)
    labelBPM = tk.Label(frameConfig, text="BPM", bg=branco, font=fonteBase)

    botaoSalvarConfig = tk.Button(
        frameConfig,
        text="Salvar",
        font=fonteBase,
        bg=azul,
        fg="white",
        width=12,
        height=1,
        command=salvarConfig
    )

    botaoVoltar = tk.Button(
        frameConfig,
        text="Voltar",
        font=fonteBase,
        bg=azul,
        fg="white",
        width=12,
        height=1,
        command=voltarInicio
    )

    labelNota.grid(row=1, column=0, padx=20, pady=(30, 5))
    labelBPM.grid(row=1, column=1, padx=20, pady=(30, 5))
    botaoSalvarConfig.grid(row=5, column=1, pady=30, padx=10)
    botaoVoltar.grid(row=5, column=0, pady=30, padx=10)

    notas = ["A", "Bb", "B", "C", "C#", "D", "Eb", "E", "F", "F#", "G", "G#"]

    entradaNota = ttk.Combobox(
        frameConfig,
        values=notas,
        width=8,
        justify="center",
        state="readonly"
    )

    entradaBPM = tk.Spinbox(
        frameConfig,
        from_=40,
        to=250,
        width=8,
        justify="center"
    )

    entradaNota.grid(row=2, column=0, padx=20)
    entradaBPM.grid(row=2, column=1, padx=20)

    entradaNota.current(indiceNotaAtual)
    entradaBPM.delete(0, "end")
    entradaBPM.insert(0, str(bpmAtual))

    # =========================
    # Tela tracks
    # =========================

    tituloTrack = tk.Label(frameTracks, text="Tracks", font=fonteTitulo, bg=branco)
    frameListaTracks = tk.Frame(frameTracks, bg=branco)

    frameAdicionar = tk.Frame(frameTracks, bg=branco)

    labelAdicionar = tk.Label(
        frameAdicionar,
        text="  +  Adicionar Track  ",
        font=fonteBase,
        bg=azul,
        fg="white",
        relief="solid",
        bd=0.5
    )

    labelAdicionar.bind(
        "<Button-1>",
        lambda event: criarTrack(len(listaTracks) + 1, "melodia")
    )

    frameBotoes = tk.Frame(frameTracks, bg=branco)

    botaoVoltarConfig = tk.Button(
        frameBotoes,
        text="Voltar",
        font=fonteBase,
        bg=azul,
        fg="white",
        width=14,
        height=1,
        command=voltarConfig
    )

    botaoSalvarMusica = tk.Button(
        frameBotoes,
        text="Salvar Música",
        font=fonteBase,
        bg=azul,
        fg="white",
        width=14,
        height=1
    )

    tituloTrack.pack(anchor="w", pady=5)
    frameListaTracks.pack(pady=5)

    labelAdicionar.pack()
    frameAdicionar.pack(pady=5)

    botaoVoltarConfig.pack(side="left", padx=35)
    botaoSalvarMusica.pack(side="left", padx=35)
    frameBotoes.pack(pady=10)

    criarTrack(1, "percussao")
    criarTrack(2, "melodia")
    criarTrack(3, "melodia")
    
    atualizarSelecaoTrack()

    labelAdicionar.bind("<Enter>", destacarAdicionar)
    labelAdicionar.bind("<Leave>", normalAdicionar)

    # =========================
    # Tela instrumento
    # =========================

    labelInstrumento = tk.Label(
        frameInstrumento,
        text="Escolher Instrumento",
        bg=branco,
        font=fonteBase
    )

    instrumentos = ["Piano", "Guitarra", "Violão", "Flauta"]

    entradaInstrumento = ttk.Combobox(
        frameInstrumento,
        values=instrumentos,
        width=15,
        justify="center",
        state="readonly"
    )

    labelInstrumento.pack(pady=10)
    entradaInstrumento.pack(pady=10)

    frameBotoesInstrumento = tk.Frame(frameInstrumento, bg=branco)
    frameBotoesInstrumento.pack(pady=10)

    botaoVoltarTracks = tk.Button(
        frameBotoesInstrumento,
        text="Voltar",
        font=fonteBase,
        bg=azul,
        fg="white",
        width=12,
        height=1,
        command=voltarTracks
    )

    botaoVoltarTracks.pack(side="left", padx=10)

    botaoSalvarInstrumento = tk.Button(
        frameBotoesInstrumento,
        text="Salvar",
        font=fonteBase,
        bg=azul,
        fg="white",
        width=12,
        height=1,
        command=salvarInstrumento
    )

    botaoSalvarInstrumento.pack(side="left", padx=10)

    # =========================
    # Tela Editor
    # =========================

    comp_canvas = 650
    altura_canvas = 230

    canvasMusica = tk.Canvas(
        frameEditor,
        width=comp_canvas,
        height=altura_canvas,
        bg="white"
    )

    canvasMusica.pack(pady=20)

    lista_y = []

    for i in range(30, altura_canvas + 1, 40):
        lista_y.append(i)

    for y in lista_y:
        canvasMusica.create_line(0, y, comp_canvas + 1, y)

    canvasMusica.create_line(40, 30, 40, altura_canvas + 1)

    for i in range(5):
        canvasMusica.create_text(20, 50 + 40 * i, text=str(i + 1), font=fonteBase)

    tam_compasso = (comp_canvas - 40) / 4

    for i in range(1, 4):
        canvasMusica.create_line(
            40 + (i * tam_compasso),
            0,
            40 + (i * tam_compasso),
            altura_canvas,
            dash=(4, 1)
        )

    posicoesEditor(lista_y)
    print(posicoesTeclas)

    cursorTempo = canvasMusica.create_line(40, 0, 40, 30, fill=azul, width=2)

    frameBotoesEditor = tk.Frame(frameEditor, bg=branco)

    botaoPlayPause = tk.Button(
        frameBotoesEditor,
        text="⏯️",
        font=fonteBase,
        bg=azul,
        fg="white",
        width=3,
        height=1,
        command=playPause
    )

    botaoGravar = tk.Button(
        frameBotoesEditor,
        text="⏺️",
        font=fonteBase,
        bg=azul,
        fg="white",
        width=3,
        height=1,
        command=iniciar
    )

    botaoExcluir = tk.Button(
        frameBotoesEditor,
        text="🗑",
        font=fonteBase,
        bg=azul,
        fg="white",
        width=3,
        height=1,
        command=excluir
    )

    botaoSalvarTrack = tk.Button(
        frameBotoesEditor,
        text="💾",
        font=fonteBase,
        bg=azul,
        fg="white",
        width=3,
        height=1,
        command=salvarTrack
    )

    botaoCancelarTrack = tk.Button(
        frameBotoesEditor,
        text="Voltar",
        font=fonteBase,
        bg=azul,
        fg="white",
        width=8,
        height=1,
        command=cancelarTrack
    )

    frameBotoesEditor.pack(pady=20)

    botaoCancelarTrack.pack(side="left", padx=15)
    botaoPlayPause.pack(side="left", padx=15)
    botaoGravar.pack(side="left", padx=15)
    botaoExcluir.pack(side="left", padx=15)
    botaoSalvarTrack.pack(side="left", padx=15)

    # Para simulações com o teclado do computador (sem necessidade de arduino):
    janela.bind("<Right>", simularEncoderAumentou)
    janela.bind("<Left>", simularEncoderAbaixou)
    janela.bind("<Return>", simularEncoderAvancou)

    janela.bind("p", simularDistanciaPerto)
    janela.bind("l", simularDistanciaLonge) 


    lerArduino()

    janela.mainloop()


if __name__ == "__main__":
    run()