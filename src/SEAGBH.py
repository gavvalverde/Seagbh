#Aqui começa a Mágica...

from tkinter import simpledialog
import tkinter as tk
from tkinter import messagebox, simpledialog
import tkinter.ttk as ttk
import sqlite3
from datetime import datetime
import os
import sys
import zipfile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import PageBreak
from reportlab.lib.enums import TA_CENTER
from tkinter import Toplevel, Label
from PIL import Image, ImageTk
import time
import shutil
from tkinter import filedialog
import threading
import glob
import re
from collections import Counter

if getattr(sys, 'frozen', False):
    # executável PyInstaller (_MEIPASS é só leitura)
    RESOURCE_DIR    = sys._MEIPASS
    APPLICATION_DIR = os.path.dirname(sys.executable)
else:
    # modo dev (VSCode/.py)
    RESOURCE_DIR    = os.path.dirname(os.path.abspath(__file__))
    APPLICATION_DIR = RESOURCE_DIR

def get_db_path():
    """
    Retorna o caminho absoluto do seaghb.db, tanto no .py quanto no .exe.
    """
    if getattr(sys, 'frozen', False):
        # rodando empacotado pelo PyInstaller em --onefile ou --onedir
        base = os.path.dirname(sys.executable)
    else:
        # rodando via Python (VSCode, .py puro)
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, 'seaghb.db')

class Cores:
    AZUL_ALURA = "#2A5A78"
    AZUL_MEDIO = "#3B8EB6"
    VERDE_ALURA = "#5CD2C6"
    CINZA_CLARO = "#F5F5F5"
    CINZA_MEDIO = "#E0E0E0"
    BRANCO = "#FFFFFF"
    VERMELHO_ALURA = "#EF5350"
    AMARELO_ALURA = "#FFD54F"

class SplashScreen(tk.Toplevel, Cores):
    def __init__(self, parent):
        super().__init__(parent)
        self._conteudo_notas = ""
        self.parent = parent
        self.title("SEAGBH - Carregando")
        self.geometry("1280x720")
        self.configure(bg=self.CINZA_CLARO)
        self.overrideredirect(True)

        # Começa transparente
        self.attributes("-alpha", 0.0)
        self.center_window()

        self.criar_elementos()
        self.atualizar_progresso()
        self.fade_in()

    def center_window(self):
        largura = self.winfo_screenwidth()
        altura = self.winfo_screenheight()
        x = (largura - 1280) // 2
        y = (altura - 720) // 2
        self.geometry(f"+{x}+{y}")

    def fade_in(self):
        alpha = self.attributes("-alpha")
        if alpha < 1.0:
            alpha += 0.02
            self.attributes("-alpha", alpha)
            self.after(10, self.fade_in)
        else:
            self.attributes("-alpha", 1.0)
        
    def criar_elementos(self):
        # Container principal centralizado
        main_frame = tk.Frame(self, bg=self.CINZA_CLARO)
        main_frame.place(relx=0.5, rely=0.5, anchor="center")  # Posicionamento central absoluto

        # Ícone
        lbl_icone = tk.Label(
            main_frame,
            text="⚙️📦",
            font=("Segoe UI", 96),
            bg=self.CINZA_CLARO,
            fg=self.AZUL_ALURA
        )
        lbl_icone.pack(pady=20)

        # Título
        self.lbl_titulo = tk.Label(
            main_frame,
            text="Inicializando SEAGBH",
            font=("Segoe UI", 24, "bold"),
            bg=self.CINZA_CLARO,
            fg=self.AZUL_ALURA
        )
        self.lbl_titulo.pack(pady=10)

        # Barra de progresso (garantir estilo)
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Custom.Horizontal.TProgressbar",
            troughcolor=self.CINZA_MEDIO,
            background=self.VERDE_ALURA,
            thickness=30  # Espessura aumentada
        )

        self.progresso = ttk.Progressbar(
            main_frame,
            style="Custom.Horizontal.TProgressbar",
            orient="horizontal",
            length=800,
            mode="determinate"
        )
        self.progresso.pack(pady=30, fill='x')

        # Mensagem de status
        self.lbl_status = tk.Label(
            main_frame,
            text="Carregando módulos principais...",
            font=("Segoe UI", 14, "bold"),
            bg=self.CINZA_CLARO,
            fg=self.AZUL_ALURA
        )
        self.lbl_status.pack(pady=10)

    def atualizar_progresso(self):
        mensagens = [
            ("Verificando banco de dados...", self.AZUL_ALURA),
            ("Carregando interface gráfica...", self.AZUL_MEDIO),
            ("Preparando relatórios...", self.VERDE_ALURA),
            ("Inicializando serviços...", self.VERMELHO_ALURA)
        ]
        total = 100
        intervalo = total / len(mensagens)

        def step(i):
            if i <= total:
                self.progresso['value'] = i
                idx = int(i // intervalo)
                if idx < len(mensagens):
                    txt, cor = mensagens[idx]
                    self.lbl_status.config(text=txt, fg=cor)
                self.after(30, step, i+1)
            else:
                self.lbl_titulo.config(text="Sistema Pronto!", fg=self.VERDE_ALURA)
                self.lbl_status.config(text="Acesso liberado", fg=self.AZUL_MEDIO)
                # em vez do lambda, chama finish_splash()
                self.after(1000, self.finish_splash)

        step(0)

    def finish_splash(self):
        """
        Fecha a splash e maximiza a janela pai (SEAGBH).
        """
        self.destroy()
        # Reexibe a janela principal e aplica maximizado
        self.parent.deiconify()
        self.parent.state('zoomed')

class SEAGBH(tk.Tk):
    def __init__(self):
        super().__init__()
        self.cores = Cores()
        self.title("SEAGBH - Sistema de Almoxarifado")
        self.autenticado_equipamentos = False
        self.tempo_inatividade = 120

        # === BLOCOS INICIAIS ===
        self.criar_pastas()
        self.conectar_banco()
        self.atualizar_estrutura_banco()

        # Monta interface, mas ainda esconde a janela principal
        self.criar_interface()
        self.configurar_estilos()
        self.criar_marca_dagua_fixa()

        # **Não** maximiza aqui — apenas esconde até o splash terminar
        self.withdraw()

        # O splash chama finish_splash() para reexibir e maximizar
        SplashScreen(self)

        self.after(1000, self.checar_eventos_atrasados)

        # Inicia backups automáticos (a cada 4 horas por padrão)
        self.agendar_backup_periodico(intervalo_ms= 4 * 3600000)

        # Mantenha os binds para alternância
        self.bind("<F11>", lambda e: self.attributes("-fullscreen", not self.attributes("-fullscreen")))
        self.bind("<Escape>", lambda e: self.attributes("-fullscreen", False))

        self.bind_all("<Any-KeyPress>", self.registrar_atividade)
        self.bind_all("<Any-Button>", self.registrar_atividade)

        # Cores Alura
        self.AZUL_ALURA = "#2A5A78"
        self.AZUL_MEDIO = "#3B8EB6"
        self.VERDE_ALURA = "#5CD2C6"
        self.CINZA_CLARO = "#F5F5F5"
        self.CINZA_MEDIO = "#E0E0E0"
        self.BRANCO = "#FFFFFF"
        self.VERMELHO_ALURA = "#EF5350"
        self.AMARELO_ALURA = "#FFD54F"

    def _obter_detalhes_evento(self, evento_id):
        """
        Retorna um dict com as chaves:
          - nome_evento
          - responsavel
          - data_inicio
          - data_fim
        """
        self.cursor.execute(
            "SELECT nome_evento, responsavel, data_inicio, data_fim "
            "FROM eventos WHERE id = ?",
            (evento_id,)
        )
        row = self.cursor.fetchone()
        if not row:
            raise ValueError(f"Evento com ID {evento_id} não encontrado")
        return {
            'nome_evento': row[0],
            'responsavel': row[1],
            'data_inicio': row[2],
            'data_fim':    row[3]
        }

    def _listar_equip_para_evento(self, evento_id):
        """
        Retorna lista de tuplas (codigo_barras, nome) dos equipamentos
        vinculados ao evento pelo seu ID.
        """
        self.cursor.execute(
            "SELECT e.codigo_barras, e.nome "
            "FROM movimentacoes m "
            " JOIN equipamentos e ON m.equipamento_id = e.id "
            "WHERE m.evento_id = ?",
            (evento_id,)
        )
        return self.cursor.fetchall()

    def configurar_estilos(self):
        style = ttk.Style()
        style.theme_use('clam')  # Tema que suporta alpha

        # fundo geral de frames e labels
        style.configure('TFrame', background=self.cores.CINZA_CLARO)
        style.configure('TLabel', background=self.cores.CINZA_CLARO,
                        foreground=self.cores.AZUL_ALURA)

        # Notebook e abas
        style.configure('TNotebook', background=self.cores.CINZA_CLARO)
        style.configure('TNotebook.Tab',
            background=self.cores.CINZA_MEDIO,
            foreground=self.cores.AZUL_ALURA,
            padding=[8,4])
        style.map('TNotebook.Tab',
            background=[('selected', self.cores.BRANCO)],
            foreground=[('selected', self.cores.AZUL_ALURA)])

        # Botões padrão (caso você use ttk.Button sem estilo customizado)
        style.configure('TButton',
            background=self.cores.CINZA_MEDIO,
            foreground=self.cores.AZUL_ALURA,
            borderwidth=1,
            focusthickness=3,
            focuscolor=self.cores.AZUL_MEDIO)
        style.map('TButton',
            background=[('active', self.cores.AZUL_MEDIO)],
            foreground=[('disabled', self.cores.CINZA_CLARO)])

        
        style.configure("Treeview",
            background=self.cores.BRANCO,
            fieldbackground=self.cores.BRANCO,
            foreground=self.cores.AZUL_ALURA,
            rowheight=30  # Aumentado para melhor visualização
        )
        
        # Estilos dos botões
        btn_config = {
        'Primary.TButton':   {'bg': self.cores.AZUL_MEDIO,  'fg': self.cores.BRANCO},
        'Success.TButton':   {'bg': self.cores.VERDE_ALURA, 'fg': self.cores.BRANCO},
        'Danger.TButton':    {'bg': self.cores.VERMELHO_ALURA, 'fg': self.cores.BRANCO},
        'Neutral.TButton':   {'bg': self.cores.CINZA_MEDIO, 'fg': self.cores.AZUL_ALURA},
        }
        for estilo, cores in btn_config.items():
            style.configure(estilo,
                background=cores['bg'],
                foreground=cores['fg'],
                font=('Arial',10,'bold'),
                padding=6,
                relief='raised',
                borderwidth=2
            )
            style.map(estilo,
                background=[('active', self.cores.AZUL_ALURA),
                            ('disabled', self.cores.CINZA_MEDIO)],
                relief=[('pressed', 'sunken'), ('!pressed', 'raised')]
            )

    def iniciar_criacao_evento(self):
        
        self._novo_evento_equipamentos = []
        popup = tk.Toplevel(self)
        self.janela_evento = popup
        popup.title("Adicionar Equipamentos ao Evento")
        popup.geometry("800x550")
        popup.transient(self)
        popup.grab_set()

        # Container principal
        container = ttk.Frame(popup, padding=20)
        container.grid(row=0, column=0, sticky="nsew")
        popup.grid_rowconfigure(0, weight=1)
        popup.grid_columnconfigure(0, weight=1)

        # Título
        title = ttk.Label(container, text="Seleção de Equipamentos", font=("Segoe UI", 16, "bold"))
        title.grid(row=0, column=0, columnspan=3, pady=(0,15))

        # Entry para código de barras e botão de adicionar
        lbl_entry = ttk.Label(container, text="Código de Barras:")
        lbl_entry.grid(row=1, column=0, sticky="w")
        self.entry_codigo_popup = ttk.Entry(container)
        self.entry_codigo_popup.grid(row=1, column=1, sticky="ew", padx=(5,5))

        self.entry_codigo_popup.bind(
            "<Return>",
            lambda ev: self._adicionar_equipamento_novo_evento()
        )
        
        container.grid_columnconfigure(1, weight=1)

        # Labelframe para Treeview
        tree_frame = ttk.Labelframe(container, text="Equipamentos Selecionados", padding=10)
        tree_frame.grid(row=2, column=0, columnspan=3, sticky="nsew", pady=(10,0))
        container.grid_rowconfigure(2, weight=1)

        cols = ("Código", "Nome do Equipamento")
        self.tree_novo_evento = ttk.Treeview(tree_frame, columns=cols, show="headings", height=15)
        style = ttk.Style()
        style.configure("Treeview", rowheight=30)
        for col in cols:
            self.tree_novo_evento.heading(col, text=col)
            self.tree_novo_evento.column(col, width=350, anchor="w")
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_novo_evento.yview)
        self.tree_novo_evento.configure(yscrollcommand=vsb.set)
        self.tree_novo_evento.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        # ─────────── Frame de Botões ───────────
        botoes_frame = ttk.Frame(container)
        botoes_frame.grid(row=3, column=0, columnspan=4, sticky="e", pady=(15,0))
        # ────────────────────────────────────────

        # Botão Finalizar
        btn_finish = ttk.Button(
            botoes_frame,
            text="✔️ Finalizar Cadastro",
            command=self.finalizar_criacao_evento,
            style="Success.TButton"
        )
        btn_finish.pack(side="right", padx=(5,0))

        # Botão Bloco de Anotações
        btn_notas = ttk.Button(
            botoes_frame,
            text="📝 Bloco de Anotações",
            command=self._abrir_bloco_notas,
            style="Neutral.TButton"
        )
        btn_notas.pack(side="right", padx=(5,0))

    def _adicionar_equipamento_novo_evento(self, event=None):
        """
        Lê o código da entry de criação de evento,
        impede duplicatas, checa manutenção e pendências de retorno,
        e insere na lista se tudo estiver OK.
        """
        codigo = self.entry_codigo_popup.get().strip()
        if not codigo:
            return

        # --- 1) obtém o ID do equipamento por código de barras ---
        equip_id = self.obter_id_por_codigo(codigo)
        if equip_id is None:
            self.entry_codigo_popup.delete(0, tk.END)
            self.entry_codigo_popup.focus_set()
            return

        # --- 2) verifica se há saída pendente (último tipo = 'saida') ---
        self.cursor.execute(
            "SELECT tipo, evento_id "
            "FROM movimentacoes "
            "WHERE equipamento_id = ? "
            "ORDER BY id DESC "
            "LIMIT 1",
            (equip_id,)
        )
        mov = self.cursor.fetchone()
        if mov and mov[0] == 'saida':
            # equipamento ainda não retornou
            evento_id_pendente = mov[1]
            # pega o nome do evento pendente
            self.cursor.execute(
                "SELECT nome_evento FROM eventos WHERE id = ?",
                (evento_id_pendente,)
            )
            nome_evt = self.cursor.fetchone()[0]
            messagebox.showwarning(
                "Equipamento Pendente de Retorno",
                f"Equipamento {codigo} não pode ser registrado, "
                f"o mesmo está pendente de retorno no Evento “{nome_evt}”",
                parent=self.janela_evento
            )
            self.entry_codigo_popup.delete(0, tk.END)
            self.entry_codigo_popup.focus_set()
            return

        # --- 3) verifica se está em manutenção ---
        if self.esta_em_manutencao(equip_id):
            aviso = tk.Toplevel(self.janela_evento)
            aviso.overrideredirect(True)
            x, y = self.winfo_pointerx(), self.winfo_pointery()
            aviso.geometry(f"+{x}+{y}")
            tk.Label(
                aviso,
                text="⚠️ Equipamento em manutenção!",
                bg="yellow", fg="red",
                font=("Arial", 12, "bold")
            ).pack(ipadx=10, ipady=5)
            aviso.after(2000, aviso.destroy)
            self.entry_codigo_popup.delete(0, tk.END)
            self.entry_codigo_popup.focus_set()
            return

        # --- 4) insere na base e na lista interna ---
        # (o SELECT abaixo é só pra pegar o nome, você já tem o ID)
        self.cursor.execute(
            'SELECT nome FROM equipamentos WHERE id = ?',
            (equip_id,)
        )
        row = self.cursor.fetchone()
        if not row:
            messagebox.showerror(
                "Erro",
                "Equipamento não cadastrado!",
                parent=self.janela_evento
            )
            self.entry_codigo_popup.delete(0, tk.END)
            return

        nome_equip = row[0]
        # insere na lista temporária
        self._novo_evento_equipamentos.append((equip_id, codigo, nome_equip))
        # insere na Treeview
        self.tree_novo_evento.insert("", "end", values=(codigo, nome_equip))

        # --- 5) limpa o campo e devolve o foco ---
        self.entry_codigo_popup.delete(0, tk.END)
        self.entry_codigo_popup.focus_set()


    def finalizar_criacao_evento(self):
        # Lê campos do formulário principal
        nome   = self.nome_evento.get().strip()
        local  = self.local_evento.get().strip()
        resp   = self.responsavel_evento.get().strip()
        inicio = self.data_inicio.get().strip()
        fim    = self.data_fim.get().strip()
        if not all([nome, local, resp, inicio, fim]):
            messagebox.showerror("Erro", "Preencha todos os campos do evento!", parent=self.janela_evento)
            return
        if not self._novo_evento_equipamentos:
            messagebox.showwarning("Aviso", "Adicione pelo menos um equipamento!", parent=self.janela_evento)
            return
        # Inserção em banco
        try:
            self.cursor.execute('BEGIN')
            self.cursor.execute(
                '''INSERT INTO eventos (nome_evento, local_evento, responsavel, data_inicio, data_fim, status)
                VALUES (?, ?, ?, ?, ?, ?)''',
                (nome, local, resp, inicio, fim, 'Agendado')
            )
            evento_id = self.cursor.lastrowid

            # ► Atualiza notas com o conteúdo digitado no bloco
            notas = getattr(self, "_conteudo_notas", "")
            self.cursor.execute(
                "UPDATE eventos SET notas = ? WHERE id = ?",
                (notas, evento_id)
            )

            # Loop de movimentações
            for equip_id, _, _ in self._novo_evento_equipamentos:
                self.cursor.execute(
                    '''INSERT INTO movimentacoes (evento_id, equipamento_id, data_movimentacao, tipo)
                    VALUES (?, ?, ?, 'saida')''',
                    (evento_id, equip_id, datetime.now().strftime("%d/%m/%Y %H:%M"))
                )

            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            messagebox.showerror("Erro", f"Falha ao criar evento: {e}", parent=self.janela_evento)
            return
        # Atualiza e fecha
        self.atualizar_lista_eventos()
        self.janela_evento.destroy()

    def criar_pastas(self):
        subdirs = [
            "Backups",
            "Relatórios/Relatórios de Inventário",
            "Relatórios/Relatórios de Manutenção",
            "Relatórios/Relatórios de Eventos"
        ]
        for rel in subdirs:
            full = os.path.join(APPLICATION_DIR, rel)
            os.makedirs(full, exist_ok=True)

    def criar_backup(self):
        # Pasta de backups
        pasta = os.path.join(APPLICATION_DIR, "Backups")
        # Nome do arquivo com timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_name = f"backup_{timestamp}.zip"
        backup_path = os.path.join(pasta, backup_name)
        # Compacta o banco de dados
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            db_file = get_db_path()
            zf.write(db_file, os.path.basename(db_file))
        # Limita a 100 backups: exclui os mais antigos
        todos = sorted(glob.glob(os.path.join(pasta, "backup_*.zip")))
        if len(todos) > 100:
            for antigo in todos[:-100]:
                os.remove(antigo)
        # Agenda o próximo backup em 4 horas
        threading.Timer(4 * 3600, self.criar_backup).start()

    def validar_quantidade(self, novo_valor):
        """Valida se o valor é um número inteiro não-negativo"""
        if novo_valor == "":  # Permite campo vazio temporariamente
            return True
        try:
            valor = int(novo_valor)
            return valor >= 0
        except ValueError:
            return False

    def conectar_banco(self):
        try:
            db_file = get_db_path()
            self.conn = sqlite3.connect(db_file)
            self.cursor = self.conn.cursor()
            
            # Habilitar chaves estrangeiras e verificar sintaxe
            self.cursor.execute("PRAGMA foreign_keys = ON")
            
            # Criar tabela equipamentos (deve vir primeiro)
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS equipamentos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    codigo_barras TEXT UNIQUE NOT NULL,
                    nome TEXT NOT NULL,
                    descricao TEXT,
                    localizacao TEXT,
                    data_cadastro TEXT NOT NULL
                )''')
            
            # Criar tabela eventos (antes de movimentacoes)
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS eventos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome_evento TEXT NOT NULL,
                    local_evento TEXT NOT NULL,
                    responsavel TEXT NOT NULL,
                    data_inicio TEXT NOT NULL,
                    data_fim TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'Agendado'
                )''')
            
            # Criar tabela movimentacoes (última, com dependências)
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS movimentacoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    evento_id INTEGER NOT NULL,
                    equipamento_id INTEGER NOT NULL,
                    data_movimentacao TEXT NOT NULL,
                    tipo TEXT CHECK(tipo IN ('saida', 'retorno')),
                    FOREIGN KEY(evento_id) REFERENCES eventos(id) ON DELETE CASCADE,
                    FOREIGN KEY(equipamento_id) REFERENCES equipamentos(id) ON DELETE CASCADE
                )''')
            
            # Criar tabela de manutenção
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS manutencao (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    equipamento_id INTEGER NOT NULL,
                    data_saida TEXT NOT NULL,
                    local_manutencao TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'Em manutenção',
                    FOREIGN KEY(equipamento_id) REFERENCES equipamentos(id)
                )''')
            
            # Adicionar esta nova tabela
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS auditoria (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tabela TEXT NOT NULL,
                    item_id INTEGER NOT NULL,
                    acao TEXT NOT NULL,
                    detalhes TEXT,
                    data TEXT NOT NULL,
                    usuario TEXT DEFAULT 'Sistema'
                )''')

            self.conn.commit()
            
        except sqlite3.Error as e:
            messagebox.showerror("Erro de Banco de Dados", f"Falha crítica:\n{str(e)}")
            self.destroy()

        # agenda o primeiro backup para daqui a 4h
        threading.Timer(4 * 3600, self.criar_backup).start()


    def backup_database(self, backup_path):
        """
        Faz um backup consistente do banco de dados ativo para backup_path.
        """
        # conecta ao arquivo de backup
        with sqlite3.connect(backup_path) as bck:
            # cópia incremental (1 página por vez)
            self.conn.backup(bck, pages=1, progress=None)

    def limpar_backups_antigos(self, max_files=10):
        """
        Mantém apenas os últimos max_files backups na pasta Backups.
        """
        pasta = os.path.join(APPLICATION_DIR, "Backups")
        # somente arquivos .db
        arquivos = sorted(f for f in os.listdir(pasta) if f.endswith(".db"))
        # remove mais antigos até sobrar max_files
        while len(arquivos) > max_files:
            os.remove(os.path.join(pasta, arquivos.pop(0)))

    def agendar_backup_periodico(self, intervalo_ms=3600000):
        """
        Agenda um backup automático a cada intervalo_ms milissegundos.
        """
        # gera timestamp e caminho
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        destino = os.path.join(APPLICATION_DIR, "Backups", f"seaghb_backup_{ts}.db")
        # faz o backup e limpa antigos
        self.backup_database(destino)
        self.limpar_backups_antigos(max_files=10)
        # agenda o próximo ciclo
        self.after(intervalo_ms, lambda: self.agendar_backup_periodico(intervalo_ms))

    def atualizar_estrutura_banco(self):
        """
        Garante que o banco tenha todas as colunas necessárias:
        - local_evento: texto, não nulo, default 'Não especificado'
        - notas: texto, default vazio
        """
        # 1️⃣ Coluna local_evento (mantém o comportamento atual)
        try:
            self.cursor.execute(
                "ALTER TABLE eventos "
                "ADD COLUMN local_evento TEXT NOT NULL DEFAULT 'Não especificado'"
            )
        except sqlite3.OperationalError:
            # já existe, ignora
            pass

        # 2️⃣ Nova coluna notas
        try:
            self.cursor.execute(
                "ALTER TABLE eventos "
                "ADD COLUMN notas TEXT DEFAULT ''"
            )
        except sqlite3.OperationalError:
            # já existe, ignora
            pass

        # 3️⃣ Commit único para ambas alterações
        self.conn.commit()

    def criar_interface(self):
        # Frame principal
        main_frame = tk.Frame(self, bg=self.cores.CINZA_CLARO)
        main_frame.pack(expand=True, fill='both', padx=20, pady=20)
    
        # Notebook (Abas)
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(expand=True, fill='both')

        # Monitorar troca de abas
        self.notebook.bind("<<NotebookTabChanged>>", self.verificar_inatividade)
        
        # Monitorar atividade do usuário
        self.bind_all("<Any-KeyPress>", self.registrar_atividade)
        self.bind_all("<Any-Button>", self.registrar_atividade)
    
        # EQUIPAMENTOS
        self.equip_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.equip_frame, text="Equipamentos", state="hidden")
        
        # Frame do formulário de equipamentos
        form_equip = tk.Frame(self.equip_frame, bg=self.cores.CINZA_CLARO)
        form_equip.pack(pady=10, fill='x')
        
        # Campos de entrada originais
        campos_equip = [
            ("Código de Barras:", 'codigo_barras'),
            ("Nome do Equipamento:", 'nome'),
            ("Descrição:", 'descricao'),
            ("Localização:", 'localizacao')
        ]

        for i, (texto, var) in enumerate(campos_equip):
            tk.Label(form_equip, text=texto, font=('Arial', 12), bg=self.cores.CINZA_CLARO, fg=self.cores.AZUL_ALURA).grid(row=i, column=0, padx=15, pady=10, sticky='e')
            entry = tk.Entry(
                form_equip,
                font=('Arial', 12),
                width=50,  # Largura aumentada
            )
            entry.grid(row=i, column=1, padx=15, pady=10, sticky='ew')
            setattr(self, var, entry)

        # Configurar expansão
        form_equip.grid_columnconfigure(1, weight=1)  # Permite expansão horizontal
    
        # Frame dos botões de equipamentos (ATUALIZADO)
        btn_equip_frame = tk.Frame(self.equip_frame, bg=self.cores.CINZA_CLARO)
        btn_equip_frame.pack(pady=10, fill='x')

        # Configurar grid com peso igual para todas as colunas
        for i in range(6):  # 6 botões
            btn_equip_frame.grid_columnconfigure(i, weight=1, uniform="btn_equip_col")
    
        botoes_equip = [
            ("Cadastrar", self.cadastrar, "Primary.TButton"),
            ("Consultar", self.consultar, "Neutral.TButton"),
            ("Listar Todos", self.listar_todos, "Neutral.TButton"),
            ("Exportar PDF", self.exportar_pdf, "Neutral.TButton"),
            ("Editar", self.abrir_edicao, "Neutral.TButton"),
            ("Remover", self.remover_item, "Danger.TButton")
        ]

        for i, (texto, comando, estilo) in enumerate(botoes_equip):
            btn = ttk.Button(
                btn_equip_frame, 
                text=texto, 
                command=comando,
                style=estilo,
                width=15
            )
            btn.grid(row=0, column=i, padx=5, pady=5, sticky='ew')

        # dentro de criar_interface(), antes de table_frame
        search_frame = tk.Frame(self.equip_frame, bg=self.cores.CINZA_CLARO)
        search_frame.pack(fill='x', padx=15, pady=(0,5))

        tk.Label(search_frame, text="Buscar:", bg=self.cores.CINZA_CLARO, fg=self.cores.AZUL_ALURA).pack(side='left')
        self.entry_search_equip = ttk.Entry(search_frame)
        self.entry_search_equip.pack(side='left', fill='x', expand=True, padx=(5,5))

        # aqui vem o bind para Enter
        self.entry_search_equip.bind('<Return>', lambda e: self.filtrar_equipamentos())

        btn_search = ttk.Button(search_frame, text="🔍", width=3, command=self.filtrar_equipamentos)
        btn_search.pack(side='left')

        # Tabela de equipamentos
        table_frame = tk.Frame(self.equip_frame, bg=self.cores.CINZA_CLARO)
        table_frame.pack(expand=True, fill='both', pady=10)
        
        self.tabela = ttk.Treeview(
            table_frame, 
            columns=("ID", "Código", "Nome", "Localização", "Data"), 
            show="headings",
            height=15
        )
    
        col_config = [
            ("ID", 80), 
            ("Código", 200), 
            ("Nome", 400),
            ("Localização", 300), 
            ("Data", 200)  # REMOVIDA A COLUNA "QUANTIDADE"
        ]

        for col, width in col_config:
            self.tabela.heading(col, text=col)
            self.tabela.column(col, width=width, anchor='center')
            
        scroll_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.tabela.yview)
        scroll_x = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tabela.xview)
        self.tabela.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        
        self.tabela.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")

        def revelar_aba_equipamentos():
            self.notebook.tab(self.equip_frame, state="normal")
            self.autenticado_equipamentos = True
            self.ultima_atividade = time.time()
        
            self.revelar_aba_equipamentos = revelar_aba_equipamentos

        # EVENTOS
        self.eventos_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.eventos_frame, text="Eventos")

        # Container principal
        main_event_frame = tk.Frame(self.eventos_frame, bg=self.cores.CINZA_CLARO)
        main_event_frame.pack(expand=True, fill='both', padx=20, pady=20)

        # Formulário de Eventos (30% superior)
        form_event_frame = tk.Frame(main_event_frame, bg=self.cores.CINZA_CLARO)
        form_event_frame.pack(fill='x', pady=10)

        campos_evento = [
            ("Nome do Evento:", 'nome_evento'),
            ("Local do Evento:", 'local_evento'),
            ("Responsável:", 'responsavel_evento'),
            ("Data Início (DD/MM/AAAA):", 'data_inicio'),
            ("Data Fim (DD/MM/AAAA):", 'data_fim')
        ]

        for i, (texto, var) in enumerate(campos_evento):
            lbl = tk.Label(form_event_frame, text=texto, font=('Arial', 12), anchor='w', bg=self.cores.CINZA_CLARO, fg=self.cores.AZUL_ALURA)
            lbl.grid(row=i, column=0, padx=15, pady=10, sticky='w')
            entry = tk.Entry(
                form_event_frame,
                font=('Arial', 12),
                width=50,  # Largura aumentada
            )
            entry.grid(row=i, column=1, padx=15, pady=10, sticky='ew')
            setattr(self, var, entry)

        # Configurar expansão
        form_event_frame.grid_columnconfigure(1, weight=1)  # Permite expansão horizontal

        # Botões (SEÇÃO CORRIGIDA)
        btn_frame = tk.Frame(main_event_frame, bg=self.cores.CINZA_CLARO)
        btn_frame.pack(pady=15, fill='x')

        # Configurar expansão das colunas
        for i in range(6):  # 6 botões
            btn_frame.grid_columnconfigure(i, weight=1, uniform="btn_col")

        botoes = [
            ("🗸 Criar Evento", self.iniciar_criacao_evento, "Primary.TButton"),
            ("📤 Registrar Retorno", self.registrar_retorno_equipamentos, "Success.TButton"),
            ("✏️ Editar Evento", self.abrir_edicao_evento, "Neutral.TButton"),
            ("🗑️ Remover Evento", self.remover_evento, "Danger.TButton"),
            ("🔄 Atualizar Lista", self.atualizar_lista_eventos, "Neutral.TButton"),
            ("📜 Histórico", self.mostrar_historico_completo, "Primary.TButton")
        ]

        for i, (texto, cmd, estilo) in enumerate(botoes):
            btn = ttk.Button(
                btn_frame, 
                text=texto, 
                command=cmd,
                style=estilo,
                width=20
            )
            btn.grid(row=0, column=i, padx=5, pady=5, sticky='ew')

        frame_search_evt = ttk.Frame(main_event_frame, padding=(10, 5))
        frame_search_evt.pack(fill="x", padx=10, pady=(0, 10))

        ttk.Label(frame_search_evt, text="Barra de pesquisa de localização:", font=("Segoe UI",10))\
            .pack(side="left", padx=(0,5))
        self.entry_search_evento = ttk.Entry(frame_search_evt, font=("Segoe UI",10), width=40)
        self.entry_search_evento.pack(side="left", fill="x", expand=True, padx=(0,5))
        ttk.Button(frame_search_evt, text="🔍", width=3, command=self._abrir_localizacao_evento)\
            .pack(side="left")
        self.entry_search_evento.bind("<Return>", lambda e: self._abrir_localizacao_evento())

        # Tabela de Eventos (70% inferior)
        table_frame = tk.Frame(main_event_frame, bg=self.cores.CINZA_CLARO)
        table_frame.pack(expand=True, fill='both', pady=10)

        colunas = ("ID", "Evento", "Local", "Responsável", "Início", "Fim", "Status")
        self.tabela_eventos = ttk.Treeview(table_frame, columns=colunas, 
                                        show="headings", height=18, selectmode='browse')
        self.tabela_eventos.tag_configure('concluido', background='#e8f5e9')

        # Configuração das colunas
        widths = [50, 250, 150, 120, 100, 100, 100]
        for col, w in zip(colunas, widths):
            self.tabela_eventos.heading(col, text=col, anchor='center')
            self.tabela_eventos.column(col, width=w, anchor='center', minwidth=50)

        # Scrollbars
        scroll_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.tabela_eventos.yview)
        scroll_x = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tabela_eventos.xview)
        self.tabela_eventos.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        # Layout
        self.tabela_eventos.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")

        # Configurar tags de cores
        self.tabela_eventos.tag_configure('agendado', background=self.cores.BRANCO)
        self.tabela_eventos.tag_configure('concluido', background=self.cores.VERDE_ALURA)
        self.tabela_eventos.tag_configure('andamento', background=self.cores.AZUL_MEDIO)

        #=================#
        # MANUTENÇÃO
        self.manutencao_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.manutencao_frame, text="Manutenção")
        
        main_manutencao_frame = tk.Frame(self.manutencao_frame, bg=self.cores.CINZA_CLARO)
        main_manutencao_frame.pack(expand=True, fill='both', padx=20, pady=20)

        # FORMULÁRIO DE CADASTRO (NOVO)
        form_manutencao = tk.Frame(main_manutencao_frame, bg=self.cores.CINZA_CLARO)
        form_manutencao.pack(pady=10, fill='x')

        # Campo Código de Barras
        tk.Label(form_manutencao, text="Código de Barras:", font=('Arial', 12), bg=self.cores.CINZA_CLARO, fg=self.cores.AZUL_ALURA).grid(row=0, column=0, padx=15, sticky='e')
        self.entry_codigo_manutencao = tk.Entry(form_manutencao, font=('Arial', 12), width=40)
        self.entry_codigo_manutencao.grid(row=0, column=1, padx=15, sticky='ew')

        # Campo Local de Manutenção
        tk.Label(form_manutencao, text="Local de Manutenção:", font=('Arial', 12), bg=self.cores.CINZA_CLARO, fg=self.cores.AZUL_ALURA).grid(row=1, column=0, padx=15, sticky='e')
        self.entry_local_manutencao = tk.Entry(form_manutencao, font=('Arial', 12), width=40)
        self.entry_local_manutencao.grid(row=1, column=1, padx=15, sticky='ew', pady=10)

        # BOTÕES ATUALIZADOS
        btn_manutencao_frame = tk.Frame(main_manutencao_frame, bg=self.cores.CINZA_CLARO)
        btn_manutencao_frame.pack(pady=15, fill='x')

        botoes_manutencao = [
            ("🔧 Cadastrar Saída", self.cadastrar_saida_manutencao, "Primary.TButton"),
            ("📥 Registrar Retorno", self.registrar_retorno_manutencao, "Success.TButton"),
            ("🔄 Atualizar Lista", self.atualizar_lista_manutencao, "Neutral.TButton")
        ]

        for i, (texto, cmd, estilo) in enumerate(botoes_manutencao):
            btn = ttk.Button(
                btn_manutencao_frame, 
                text=texto, 
                command=cmd,
                style=estilo,
                width=20
            )
            btn.grid(row=0, column=i, padx=8, pady=5, sticky='ew')

        # TABELA ATUALIZADA
        colunas_manutencao = ("ID", "Código", "Nome", "Data Saída", "Local Manutenção", "Status")
        self.tabela_manutencao = ttk.Treeview(
            main_manutencao_frame,
            columns=colunas_manutencao,
            show="headings",
            height=15
        )
        
        # Configuração das colunas
        widths = [50, 150, 250, 150, 200, 120]
        for col, w in zip(colunas_manutencao, widths):
            self.tabela_manutencao.heading(col, text=col, anchor='center')
            self.tabela_manutencao.column(col, width=w, anchor='center')
        
        # Tags de status
        self.tabela_manutencao.tag_configure('em_manutencao', background='#FFF3E0')
        self.tabela_manutencao.tag_configure('concluido', background='#E8F5E9')

        scroll_y = ttk.Scrollbar(main_manutencao_frame, orient="vertical", command=self.tabela_manutencao.yview)
        scroll_x = ttk.Scrollbar(main_manutencao_frame, orient="horizontal", command=self.tabela_manutencao.xview)
        self.tabela_manutencao.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        self.tabela_manutencao.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")

        # ABA DE RELATÓRIOS
        relatorios_frame = ttk.Frame(self.notebook)
        self.notebook.add(relatorios_frame, text="Relatórios")

        # Container principal
        main_relatorios_frame = tk.Frame(relatorios_frame, bg=self.cores.CINZA_CLARO)
        main_relatorios_frame.pack(expand=True, fill='both', padx=20, pady=20)

        # Botões em coluna
        botoes_relatorios = [
            ("📋 Gerar Relatório: Eventos em Andamento", self.gerar_relatorio_eventos_andamento),
            ("📑 Gerar Relatório: Eventos Detalhados", self.abrir_selecao_relatorio_detalhado),
            ("🔧 Gerar Relatório: Equip. em Manutenção", self.gerar_relatorio_manutencao)
        ]

        for i, (texto, comando) in enumerate(botoes_relatorios):
            btn = ttk.Button(
                main_relatorios_frame,
                text=texto,
                command=comando,
                style="Primary.TButton",
                width=40
            )
            btn.pack(pady=10, ipady=8)

        # ===== NOVO BOTÃO DE MENU DE UTILITÁRIOS =====
        btn_frame_utilitarios = tk.Frame(main_relatorios_frame)
        btn_frame_utilitarios.pack(side='bottom', anchor='se', padx=10, pady=10)
        
        btn_menu_utilitarios = ttk.Button(
            btn_frame_utilitarios,
            text="⚙️ Utilitários",
            command=self.abrir_menu_utilitarios,
            style="Neutral.TButton",
            width=15
        )
        btn_menu_utilitarios.pack()

    def _abrir_localizacao_evento(self, event=None):
        """
        Pesquisa onde o equipamento está:
        • Se estiver em manutenção, alerta e sai.
        • Senão, busca última saída pendente; se não houver ou for concluído, alerta.
        • Caso esteja em evento agendado, abre popup 450×450 com os dados.
        """
        codigo = self.entry_search_evento.get().strip()
        if not codigo:
            return

        # 0) Verifica manutenção primeiro
        equip_id = self.obter_id_por_codigo(codigo)
        if equip_id is not None and self.esta_em_manutencao(equip_id):
            messagebox.showwarning(
                "Equipamento em Manutenção",
                f"O equipamento {codigo} está em manutenção no momento.",
                parent=self.master
            )
            return

        # 1) Busca último movimento tipo 'saida' (saída ainda não retornada)
        sql = """
        SELECT
            ev.nome_evento,
            ev.data_inicio,
            ev.local_evento,
            ev.status,
            eq.nome,
            eq.codigo_barras,
            eq.descricao
        FROM movimentacoes m
        JOIN eventos ev     ON m.evento_id     = ev.id
        JOIN equipamentos eq ON m.equipamento_id = eq.id
        WHERE eq.codigo_barras = ?
            AND m.tipo = 'saida'
        ORDER BY m.rowid DESC
        LIMIT 1
        """
        self.cursor.execute(sql, (codigo,))
        row = self.cursor.fetchone()

        # 2) Se não houver saída pendente
        if not row:
            messagebox.showwarning(
                "Nenhum Evento Ativo",
                f"O equipamento {codigo} não está alocado em nenhum evento agendado.",
                parent=self.master
            )
            return

        nome_evt, data_ini, local_evt, status_evt, nome_eq, cod_eq, desc = row

        # 3) Se o evento já foi concluído
        if status_evt.lower() != 'agendado':
            messagebox.showwarning(
                "Nenhum Evento Ativo",
                f"O equipamento {codigo} não está alocado em nenhum evento agendado.",
                parent=self.master
            )
            return

        # 4) Está em um evento agendado: exibe popup com informações
        popup = tk.Toplevel(self.master)
        popup.title(f"Localização do Equipamento {codigo}")
        popup.geometry("450x450")
        popup.transient(self.master)
        popup.grab_set()

        frm = ttk.Frame(popup, padding=15)
        frm.pack(fill="both", expand=True)

        campos = [
            ("Evento",        nome_evt),
            ("Data Início",   data_ini),
            ("Local Evento",  local_evt),
            ("Nome Equip.",   nome_eq),
            ("Código Barras", cod_eq),
            ("Descrição",     desc),
        ]
        for label, valor in campos:
            ttk.Label(frm, text=f"{label}:", font=("Segoe UI", 9, "bold"))\
            .pack(anchor="w", pady=(10,0))
            ttk.Label(frm, text=valor, font=("Segoe UI", 9))\
            .pack(anchor="w", padx=(20,0))

        ttk.Button(frm, text="Fechar", command=popup.destroy)\
        .pack(pady=(20,0))

    def verificar_acesso_equipamentos(self, event=None):
        current_tab = self.notebook.index(self.notebook.select())
        tab_text = self.notebook.tab(current_tab, "text")
        
        if tab_text == "Equipamentos":
            if not self.autenticado_equipamentos:
                self.mostrar_login()
            else:
                # Verificar inatividade apenas se já autenticado
                if time.time() - self.ultima_atividade > self.tempo_inatividade:
                    self.bloquear_aba_equipamentos()
    
        # Permitir livre acesso às outras abas
        else:
            self.notebook.tab(self.equip_frame, state="hidden")
    
    def filtrar_equipamentos(self):
        termo = self.entry_search_equip.get().strip().lower()
        # limpa a tabela
        for item in self.tabela.get_children():
            self.tabela.delete(item)
        # busca no DB (ou, se já tiver carregado, filtra lista em memória)
        self.cursor.execute('''
            SELECT id, codigo_barras, nome, localizacao, data_cadastro
            FROM equipamentos
            WHERE lower(codigo_barras) LIKE ? OR lower(nome) LIKE ? OR lower(localizacao) LIKE ?
            ORDER BY id
        ''', (f'%{termo}%', f'%{termo}%', f'%{termo}%'))
        for row in self.cursor.fetchall():
            self.tabela.insert("", "end", values=row)

    def bloquear_aba_equipamentos(self):
        self.autenticado_equipamentos = False
        self.notebook.tab(self.equip_frame, state="hidden")
        self.notebook.select(0)  # Redirecionar para primeira aba
        self.mostrar_login()

    def registrar_atividade(self, event=None):
        if self.autenticado_equipamentos:
            self.ultima_atividade = time.time()

    def verificar_inatividade(self, event=None):
        """Verifica inatividade ao trocar para a aba de equipamentos"""
        current_tab = self.notebook.index(self.notebook.select())
        self.tab_ativa = self.notebook.tab(current_tab, "text")
        
        if self.tab_ativa == "Equipamentos" and not self.bloqueado:
            if time.time() - self.ultima_atividade > 120:  # 2 minutos
                self.mostrar_login()
            else:
                self.registrar_atividade()

    def mostrar_login(self):
        login_window = tk.Toplevel(self)
        login_window.title("Acesso Restrito - Equipamentos")
        login_window.grab_set()
        
        # Centralizar
        x = self.winfo_x() + (self.winfo_width() // 2) - 150
        y = self.winfo_y() + (self.winfo_height() // 2) - 75
        login_window.geometry(f"300x150+{x}+{y}")
        
        # Elementos da interface
        tk.Label(login_window, text="Sessão Bloqueada", font=('Arial', 14, 'bold'), bg=self.cores.CINZA_CLARO, fg=self.cores.AZUL_ALURA).pack(pady=5)
        
        frame = tk.Frame(login_window, bg=self.cores.CINZA_CLARO)
        frame.pack(pady=10)
        
        tk.Label(frame, text="Usuário:", bg=self.cores.CINZA_CLARO, fg=self.cores.AZUL_ALURA).grid(row=0, column=0, padx=5)
        user_entry = tk.Entry(frame)
        user_entry.grid(row=0, column=1)
        
        tk.Label(frame, text="Senha:", bg=self.cores.CINZA_CLARO, fg=self.cores.AZUL_ALURA).grid(row=1, column=0, padx=5)
        pass_entry = tk.Entry(frame, show="*")
        pass_entry.grid(row=1, column=1)
    
        def validar_login():
            if user_entry.get() == "admin" and pass_entry.get() == "seguranca123":
                self.revelar_aba_equipamentos()
                self.notebook.select(self.equip_frame)  # Navegar para aba
                login_window.destroy()
            else:
                messagebox.showerror("Acesso Negado", "Credenciais inválidas!")
                self.notebook.select(0)  # Voltar para aba segura
        
        btn = tk.Button(login_window, text="Desbloquear", command=validar_login)
        btn.pack(pady=10)
        
        # Forçar foco
        user_entry.focus_set()

    # ===== NOVO MÉTODO PARA MOSTRAR AUDITORIA =====
    def mostrar_auditoria(self):
        janela = tk.Toplevel()
        janela.title("Histórico de Alterações do Sistema")
        janela.geometry("1200x600")
        
        # Treeview com scroll
        frame = tk.Frame(janela, bg=self.cores.CINZA_CLARO)
        frame.pack(expand=True, fill='both', padx=10, pady=10)
        
        colunas = ("ID", "Tabela", "Item ID", "Ação", "Detalhes", "Data", "Usuário")
        tree = ttk.Treeview(frame, columns=colunas, show="headings", height=20)
        
        # Configurar colunas
        larguras = [50, 100, 80, 120, 400, 150, 100]
        for col, larg in zip(colunas, larguras):
            tree.heading(col, text=col)
            tree.column(col, width=larg, anchor='center')
        
        # Buscar dados
        self.cursor.execute('SELECT * FROM auditoria ORDER BY id DESC LIMIT 500')
        for registro in self.cursor.fetchall():
            tree.insert("", "end", values=registro)
        
        # Scrollbars
        scroll_y = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        scroll_x = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        
        # Layout
        tree.grid(row=0, column=0, sticky='nsew')
        scroll_y.grid(row=0, column=1, sticky='ns')
        scroll_x.grid(row=1, column=0, sticky='ew')
        
        # Configurar expansão
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

    def gerar_relatorio_eventos_andamento(self):
        try:
            self.cursor.execute('''
                SELECT id, nome_evento, responsavel, data_inicio, data_fim 
                FROM eventos 
                WHERE status = 'Agendado'
            ''')
            dados = self.cursor.fetchall()
            
            if not dados:
                messagebox.showinfo("Info", "Nenhum evento em andamento!")
                return
                
            # ========== PADRÃO VISUAL ========== 
            data_hora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            caminho = os.path.join(
                APPLICATION_DIR,
                "Relatórios",
                "Relatórios de Eventos",
                f"Relatorio_Eventos_Andamento_{data_hora}.pdf"
            )
            
            doc = SimpleDocTemplate(caminho, pagesize=A4, leftMargin=1.5*cm, rightMargin=1.5*cm)
            elementos = []
            estilos = getSampleStyleSheet()
            
            # Cabeçalho Padrão
            estilo_cabecalho = ParagraphStyle(
                'Cabecalho',
                parent=estilos["Title"],
                fontSize=12,
                textColor=colors.HexColor(self.AZUL_ALURA),
                alignment=TA_CENTER
            )
            
            elementos.append(Paragraph("SEAGBH - Relatório de Eventos em Andamento", estilo_cabecalho))
            elementos.append(Paragraph(f"<font size='9' color='#666666'>Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}</font>", estilos["BodyText"]))
            elementos.append(Spacer(1, 15))
            
            # Tabela Padronizada
            cabecalho = ["ID", "Evento", "Responsável", "Início", "Término"]
            dados_tabela = [cabecalho] + dados
            
            tabela = Table(dados_tabela, colWidths=[1.2*cm, 6*cm, 4*cm, 3*cm, 3*cm])
            estilo = TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor(self.AZUL_ALURA)),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,-1), 9),
                ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor(self.CINZA_MEDIO)),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor(self.CINZA_CLARO)])
            ])
            
            tabela.setStyle(estilo)
            elementos.append(tabela)
            elementos.append(Spacer(1, 10))
            elementos.append(Paragraph(f"<font size='8' color='#888888'>Total de eventos: {len(dados)}</font>", estilos["BodyText"]))
            # ========== FIM PADRÃO ==========
            
            doc.build(elementos)
            messagebox.showinfo("Sucesso", f"Relatório gerado em:\n{os.path.abspath(caminho)}")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao gerar relatório:\n{str(e)}")

    def abrir_selecao_relatorio_detalhado(self):
        # 1) Cria a janela popup (dobro do tamanho original)
        popup = tk.Toplevel(self)
        popup.title("Selecione Eventos para Relatório Detalhado")
        popup.geometry("800x800")
        popup.transient(self)
        popup.grab_set()

        # 2) Define estilo “Report.TCheckbutton” inspirado no Primary.TButton
        style = ttk.Style(popup)
        style.configure("Report.TCheckbutton",
            font=("Segoe UI", 14, "bold"),
            background=self.cores.AZUL_MEDIO,
            foreground=self.cores.BRANCO,
            padding=10,
            relief="raised",
            indicatoron=False,         # remove o quadradinho
        )
        style.map("Report.TCheckbutton",
            background=[
                ("active", self.cores.AZUL_ALURA),
                ("selected", self.cores.VERDE_ALURA),
                ("!selected", self.cores.AZUL_MEDIO),
            ],
            foreground=[
                ("selected", self.cores.BRANCO),
                ("!selected", self.cores.BRANCO),
            ]
        )

        # 3) Frame com scroll para acomodar muitos checkbuttons
        container = ttk.Frame(popup, padding=10)
        container.pack(expand=True, fill="both")

        canvas = tk.Canvas(container, bg=self.cores.CINZA_CLARO, highlightthickness=0)
        vsb = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)

        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=vsb.set)

        canvas.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        # 4) “Emitir Todos” no topo
        var_todos = tk.BooleanVar(value=False)
        check_vars = []

        chk_all = ttk.Checkbutton(
            scroll_frame,
            text="📑  Emitir Todos",
            variable=var_todos,
            style="Report.TCheckbutton",
            command=lambda: [v.set(var_todos.get()) for v in check_vars]
        )
        chk_all.pack(fill="x", pady=(0, 15))

        # 5) Carrega eventos em andamento do banco
        self.cursor.execute("""
            SELECT id, nome_evento
            FROM eventos
            WHERE status = 'Agendado'
        ORDER BY nome_evento
        """)
        eventos = self.cursor.fetchall()  # lista de tuples (id, nome)

        # 6) Gera um Report.TCheckbutton para cada evento
        vars_por_evento = []
        for ev_id, ev_nome in eventos:
            v = tk.BooleanVar()
            chk = ttk.Checkbutton(
                scroll_frame,
                text=f"🔹  {ev_nome}",
                variable=v,
                style="Report.TCheckbutton"
            )
            chk.pack(fill="x", pady=5)
            check_vars.append(v)
            vars_por_evento.append((ev_id, v))

        # 7) Callback de emissão
        def on_emitir():
            selecionados = [ev_id for ev_id, var in vars_por_evento if var.get()]
            if var_todos.get():
                selecionados = [ev_id for ev_id, _ in eventos]
            popup.destroy()
            if not selecionados:
                messagebox.showwarning("Aviso", "Nenhum evento selecionado!")
                return
            self._emitir_relatorios_detalhados(selecionados)

        btn = ttk.Button(
            popup,
            text="✔️ Emitir Selecionados",
            command=on_emitir,
            style="Primary.TButton",
            width=25
        )
        btn.pack(pady=20)

    def _emitir_relatorios_detalhados(self, lista_ids):
            """
            Gera um ou vários relatórios detalhados em PDF para a lista de IDs de eventos.
            Parâmetros:
                lista_ids (list): Lista de IDs de eventos a serem processados.
            """
            from tkinter import messagebox
            gerados = 0

            if not lista_ids:
                messagebox.showwarning(
                    title="Aviso",
                    message="Nenhum evento selecionado para geração de relatório!"
                )
                return

            for evento_id in lista_ids:
                try:
                    evento = self._obter_detalhes_evento(evento_id)

                    # Busca equipamentos associados
                    self.cursor.execute(
                        "SELECT eq.codigo_barras, eq.nome"
                        " FROM movimentacoes m"
                        " JOIN equipamentos eq ON m.equipamento_id = eq.id"
                        " WHERE m.evento_id = ? AND m.tipo = 'saida'",
                        (evento_id,)
                    )
                    equipamentos = self.cursor.fetchall()

                    # Monta resumo por categoria
                    resumo = {}
                    for codigo, nome in equipamentos:
                        categoria = nome.split()[0]
                        resumo[categoria] = resumo.get(categoria, 0) + 1

                    # Cria pasta de saída
                    pasta = os.path.join(APPLICATION_DIR, "Relatórios", "Relatórios de Eventos")
                    os.makedirs(pasta, exist_ok=True)
                    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                    safe_nome = evento['nome_evento'].replace(" ", "_")
                    filename = f"{safe_nome} - Relatório_detalhado - {ts}.pdf"
                    caminho = os.path.join(pasta, filename)

                    # Prepara documento
                    doc = SimpleDocTemplate(caminho, pagesize=A4)
                    estilos = getSampleStyleSheet()
                    title_style = estilos["Title"]
                    body = estilos["BodyText"]
                    heading3 = estilos["Heading3"]
                    elementos = []

                    # Cabeçalho
                    elementos.append(Paragraph(f"RELATÓRIO DETALHADO: {evento['nome_evento']}", title_style))
                    elementos.append(Paragraph(f"Responsável: {evento['responsavel']}", body))
                    elementos.append(Paragraph(f"Período: {evento['data_inicio']} a {evento['data_fim']}", body))
                    elementos.append(Spacer(1, 12))

                    # Resumo de equipamentos
                    elementos.append(Paragraph("Resumo de Equipamentos:", heading3))
                    for cat, cnt in resumo.items():
                        elementos.append(Paragraph(f"• {cnt} {cat}", body))
                    elementos.append(Spacer(1, 12))

                    # Lista em colunas com quebra de linha: usar Paragraph nos cells
                    elementos.append(Paragraph("Equipamentos Detalhados:", heading3))
                    # Cria células com Paragraph para habilitar wrap
                    cell_pars = [Paragraph(f"• {nome} ({codigo})", body) for codigo, nome in equipamentos]
                    # Quebra em linhas de 3 colunas
                    rows = [cell_pars[i:i+3] for i in range(0, len(cell_pars), 3)]
                    # Preenche células vazias
                    for row in rows:
                        while len(row) < 3:
                            row.append(Paragraph("", body))
                    tabela = Table(rows, colWidths=[6*cm]*3, hAlign='LEFT')
                    tabela.setStyle(TableStyle([
                        ('VALIGN', (0,0), (-1,-1), 'TOP'),
                        ('LEFTPADDING', (0,0), (-1,-1), 4),
                        ('RIGHTPADDING', (0,0), (-1,-1), 4),
                        ('TOPPADDING', (0,0), (-1,-1), 2),
                        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
                        ('WORDWRAP', (0,0), (-1,-1), 'CJK')
                    ]))
                    elementos.append(tabela)

                    # Gera PDF
                    doc.build(elementos)
                    gerados += 1
                except Exception as e:
                    messagebox.showerror(
                        "Erro ao gerar relatório",
                        f"Falha no evento {evento_id}: {e}"
                    )
            messagebox.showinfo(
                title="Relatórios Gerados",
                message=f"{gerados} relatório(s) gerado(s) com sucesso!"
            )

    def gerar_relatorio_evento_detalhado_unico(self, evento_id, nome_evento):
            """
            Gera um PDF detalhado para um único evento:
            1) Título fixo
            2) Nome do evento em linha normal
            3) Responsável e período como bullets
            4) Resumo agrupado
            5) Lista de equipamentos em 3 colunas
            """
            # 1) Busca dados do evento
            self.cursor.execute('''
                SELECT responsavel, data_inicio, data_fim
                FROM eventos
                WHERE id = ?
            ''', (evento_id,))
            row = self.cursor.fetchone()
            if not row:
                return
            responsavel, dt_ini, dt_fim = row

            # 2) Busca equipamentos
            self.cursor.execute('''
                SELECT eq.nome, eq.codigo_barras
                FROM movimentacoes m
                JOIN equipamentos eq ON m.equipamento_id = eq.id
                WHERE m.evento_id = ? AND m.tipo = 'saida'
            ''', (evento_id,))
            equipamentos = self.cursor.fetchall()

            # 3) Agrupa primeiras duas palavras como categoria
            from collections import Counter
            resumo_keys = []
            for nome, _ in equipamentos:
                parts = nome.split()
                chave = " ".join(parts[:2]) if len(parts) >= 2 else parts[0]
                resumo_keys.append(chave)
            resumo_counts = Counter(resumo_keys)

            # 4) Prepara caminho seguro
            import re, os
            from datetime import datetime
            safe_nome = re.sub(r'[\\/*?:"<>|]', '_', nome_evento)
            ts = datetime.now().strftime("%d_%m_%Y_%H-%M-%S")
            pasta = os.path.join(APPLICATION_DIR, "Relatórios", "Relatórios de Eventos")
            os.makedirs(pasta, exist_ok=True)
            filename = f"{safe_nome} - Relatório_detalhado - {ts}.pdf"
            caminho = os.path.join(pasta, filename)

            # 5) Monta PDF
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.enums import TA_CENTER
            from reportlab.lib.units import cm
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors

            doc = SimpleDocTemplate(caminho, pagesize=A4,
                                    leftMargin=1.5*cm, rightMargin=1.5*cm)
            estilos = getSampleStyleSheet()
            body = estilos["BodyText"]
            elementos = []

            # --- Cabeçalho ajustado ---
            elementos.append(Paragraph("Relatório detalhado do Evento", 
                                    ParagraphStyle(
                                        name="TituloFixo", 
                                        parent=estilos["Title"],
                                        alignment=TA_CENTER)))
            elementos.append(Spacer(1, 6))
            elementos.append(Paragraph(nome_evento, estilos["Heading2"]))
            elementos.append(Spacer(1, 6))
            elementos.append(Paragraph(f"• Responsável: {responsavel}", body))
            elementos.append(Paragraph(f"• Período: {dt_ini} a {dt_fim}", body))
            elementos.append(Spacer(1, 12))

            # --- Resumo ---
            elementos.append(Paragraph("Resumo de Equipamentos:", estilos["Heading3"]))
            for cat, cnt in resumo_counts.items():
                elementos.append(Paragraph(f"• {cnt} {cat}", body))
            elementos.append(Spacer(1, 12))

            # --- Lista em 3 colunas ---
            cells = [f"• {n} ({c})" for n, c in equipamentos]
            rows = [cells[i:i+3] for i in range(0, len(cells), 3)]
            for row in rows:
                while len(row) < 3:
                    row.append("")
            tabela = Table(rows, colWidths=[6*cm]*3, hAlign='LEFT')
            tabela.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('LEFTPADDING', (0,0), (-1,-1), 2), ('RIGHTPADDING', (0,0), (-1,-1), 2),
                ('TOPPADDING', (0,0), (-1,-1), 2), ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ]))
            elementos.append(tabela)

            doc.build(elementos)

    def gerar_relatorio_eventos_detalhado(self):
        try:
            # === busca raw_equip concatenado ===
            self.cursor.execute('''
                SELECT e.id, e.nome_evento, e.responsavel, e.data_inicio, e.data_fim,
                    GROUP_CONCAT(eq.nome || ' (' || eq.codigo_barras || ')', ', ')
                FROM eventos e
                LEFT JOIN movimentacoes m ON e.id = m.evento_id
                LEFT JOIN equipamentos eq ON m.equipamento_id = eq.id
                WHERE e.status = 'Agendado'
                GROUP BY e.id
            ''')
            dados = self.cursor.fetchall()
            if not dados:
                messagebox.showinfo("Info", "Nenhum evento em andamento!")
                return

            # === setup do PDF ===
            data_hora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            caminho = os.path.join(APPLICATION_DIR, "Relatórios", "Relatórios de Eventos",
                                f"Relatorio_Eventos_Detalhado_{data_hora}.pdf")
            doc = SimpleDocTemplate(caminho, pagesize=A4)
            estilos = getSampleStyleSheet()
            estilo_titulo = ParagraphStyle(
                'TituloEvento',
                parent=estilos["Heading2"],
                textColor=colors.HexColor(self.AZUL_ALURA),
                fontSize=12,
                spaceAfter=6
            )
            body = estilos["BodyText"]

            elementos = []
            elementos.append(Paragraph("<b>RELATÓRIO DETALHADO DE EVENTOS EM ANDAMENTO</b>", estilos["Title"]))
            elementos.append(Spacer(1, 12))

            for evento in dados:
                evento_id, nome_ev, resp, dt_ini, dt_fim, raw_equip = evento

                # cabeçalho
                elementos.append(Paragraph(f"Evento #{evento_id} – {nome_ev}", estilo_titulo))
                elementos.append(Paragraph(f"• Responsável: {resp}", body))
                elementos.append(Paragraph(f"• Período: {dt_ini} a {dt_fim}", body))
                elementos.append(Spacer(1, 6))

                # resumo
                elementos.append(Paragraph("• Equipamentos (resumo):", body))
                if raw_equip:
                    itens = raw_equip.split(', ')
                    nomes = [re.sub(r' \(\d+\)$', '', it) for it in itens]
                    contagem = Counter(nomes)
                    for nome_gen, qtd in contagem.items():
                        elementos.append(Paragraph(f"   – {qtd}× {nome_gen}", body))
                else:
                    elementos.append(Paragraph("   nenhum", body))
                elementos.append(Spacer(1, 10))

                # lista detalhada EM TRÊS COLUNAS
                if raw_equip:
                    itens = raw_equip.split(', ')
                    # organiza em linhas de 3
                    linhas = []
                    for i in range(0, len(itens), 3):
                        grupo = itens[i:i+3]
                        if len(grupo) < 3:
                            grupo += [""]*(3-len(grupo))
                        linhas.append(grupo)
                    # cria células como Paragraphs com bullet
                    estilo_equip = ParagraphStyle(
                        'EquipDetalhe',
                        parent=body,
                        leftIndent=5,  # indent interno
                        bulletIndent=0
                    )
                    table_data = []
                    for linha in linhas:
                        row = []
                        for cel in linha:
                            if cel:
                                row.append(Paragraph(f"• {cel}", estilo_equip))
                            else:
                                row.append(Paragraph("", estilo_equip))
                        table_data.append(row)
                    # monta Table 3 colunas
                    tbl = Table(table_data, colWidths=[6*cm, 6*cm, 6*cm], hAlign="LEFT")
                    tbl.setStyle(TableStyle([
                        ("VALIGN", (0,0), (-1,-1), "TOP"),
                        ("LEFTPADDING", (0,0), (-1,-1), 0),
                        ("RIGHTPADDING", (0,0), (-1,-1), 10),
                        # sem linhas visíveis
                    ]))
                    elementos.append(tbl)
                elementos.append(Spacer(1, 12))
                # fim do evento

            # grava
            doc.build(elementos)
            messagebox.showinfo("Sucesso", f"Relatório gerado em:\n{os.path.abspath(caminho)}")

        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao gerar relatório:\n{e}")

    def gerar_relatorio_manutencao(self):
        try:
            self.cursor.execute('''
                SELECT e.codigo_barras, e.nome, m.local_manutencao, m.data_saida 
                FROM manutencao m
                JOIN equipamentos e ON m.equipamento_id = e.id
                WHERE m.status = 'Em manutenção'
            ''')
            dados = self.cursor.fetchall()

            if not dados:
                messagebox.showinfo("Info", "Nenhum equipamento em manutenção!")
                return

            # Criar PDF
            data_hora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            caminho = os.path.join(
                APPLICATION_DIR,
                "Relatórios",
                "Relatórios de Manutenção",
                f"Relatorio_Manutencao_{data_hora}.pdf"
            )
            
            doc = SimpleDocTemplate(caminho, pagesize=A4)
            elementos = []
            estilos = getSampleStyleSheet()

            # Título
            titulo = Paragraph(
                "<b>RELATÓRIO DE EQUIPAMENTOS EM MANUTENÇÃO</b>",
                estilos["Title"]
            )
            elementos.append(titulo)
            elementos.append(Spacer(1, 15))

            # Tabela Padronizada
            cabecalho = ["Código", "Equipamento", "Local", "Data Saída"]
            dados_tabela = [cabecalho] + dados
            
            tabela = Table(dados_tabela, colWidths=[3.5*cm, 6*cm, 5*cm, 4*cm])
            estilo = TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor(self.AZUL_ALURA)),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,-1), 9),
                ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor(self.CINZA_MEDIO)),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor(self.CINZA_CLARO)])
            ])
            
            tabela.setStyle(estilo)
            elementos.append(tabela)
            
            doc.build(elementos)
            messagebox.showinfo("Sucesso", f"Relatório gerado em:\n{os.path.abspath(caminho)}")

        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao gerar relatório:\n{str(e)}")


    def abrir_janela_evento(self):
        self.janela_evento = tk.Toplevel()
        self.janela_evento.title("Gestão Completa de Evento")
        
        # Frame principal
        main_frame = tk.Frame(self.janela_evento)
        main_frame.pack(padx=20, pady=20)

        # Seção de informações do evento
        tk.Label(main_frame, text="Dados do Evento", font='Arial 12 bold').grid(row=0, column=0, sticky='w')
        
        campos = [
            ("Nome do Evento:", 'nome_evento'),
            ("Responsável:", 'responsavel_evento'),
            ("Data Início (DD/MM/AAAA):", 'data_inicio'),
            ("Data Fim (DD/MM/AAAA):", 'data_fim')
        ]
        
        for i, (texto, var) in enumerate(campos, start=1):
            tk.Label(main_frame, text=texto).grid(row=i, column=0, sticky='e', padx=5, pady=2)
            entry = tk.Entry(main_frame, width=40)
            entry.grid(row=i, column=1, padx=5, pady=2)
            setattr(self, f"evento_{var}", entry)

        # Seção de equipamentos
        tk.Label(main_frame, text="Equipamentos do Evento", font='Arial 12 bold').grid(row=5, column=0, columnspan=2, pady=10)
        
        # Combobox para seleção de equipamentos
        tk.Label(main_frame, text="Selecionar Equipamento:").grid(row=6, column=0)
        self.combo_equipamentos = ttk.Combobox(main_frame, state='readonly')
        self.combo_equipamentos.grid(row=6, column=1)
        self.carregar_equipamentos_combo()
        
        # Botões
        tk.Button(main_frame, text="Adicionar Equipamento", command=self.adicionar_equipamento_evento,
                bg='#2196F3', fg='white').grid(row=8, column=0, columnspan=2, pady=10)
        
        # Tabela de equipamentos do evento
        colunas = ("ID", "Equipamento")
        self.tabela_equip_evento = ttk.Treeview(main_frame, columns=colunas, show="headings", height=5)
        
        for col in colunas:
            self.tabela_equip_evento.heading(col, text=col)
            self.tabela_equip_evento.column(col, width=100)
        
        self.tabela_equip_evento.grid(row=9, column=0, columnspan=2)

        # Botão final
        tk.Button(main_frame, text="Salvar Evento", command=self.salvar_evento_completo,
                bg='#4CAF50', fg='white').grid(row=10, column=0, columnspan=2, pady=20)
        
        tk.Button(
        main_frame,
            text="📝 Bloco de Anotações",
            command=lambda eid=self.evento_id: self._abrir_bloco_notas(eid),
            bg=self.CINZA_MEDIO, fg=self.AZUL_ALURA
        ).grid(row=10, column=2, padx=10, pady=20)
        
        self.centralizar_janela(self.janela_evento)
        
    # Adicionar novo método de validação:
    def validar_data_evento(self, data_inicio, data_fim):
        try:
            inicio = datetime.strptime(data_inicio, "%d/%m/%Y")
            fim = datetime.strptime(data_fim, "%d/%m/%Y")
            if inicio > fim:
                raise ValueError("Data inicial posterior à final")
            return True
        except ValueError as e:
            messagebox.showerror("Erro", f"Data inválida: {str(e)}")
            return False

    def carregar_equipamentos_combo(self):
        self.cursor.execute('SELECT id, nome FROM equipamentos')
        equipamentos = [f"{id} - {nome}" for id, nome in self.cursor.fetchall()]
        self.combo_equipamentos['values'] = equipamentos

    def atualizar_lista_eventos(self):
        self.tabela_eventos.delete(*self.tabela_eventos.get_children())
        self.cursor.execute('''
            SELECT id, nome_evento, local_evento, responsavel, 
                data_inicio, data_fim, status 
            FROM eventos
            ORDER BY id DESC
        ''')
        
        for evento in self.cursor.fetchall():
            tag = 'andamento' if evento[6] == 'Agendado' else 'concluido'
            self.tabela_eventos.insert("", "end", values=evento, tags=(tag,))

    def obter_id_por_codigo(self, codigo):
        """
        Tenta primeiro por correspondência exata de texto.
        Se não achar, converte ambos para inteiro e compara,
        assim '41' e '0041' batem corretamente.
        """
        codigo = str(codigo).strip()

        # 1) busca exata
        self.cursor.execute(
            "SELECT id FROM equipamentos WHERE codigo_barras = ?",
            (codigo,)
        )
        row = self.cursor.fetchone()

        # 2) se não achou, tenta por valor numérico (ignora zeros à esquerda)
        if not row:
            try:
                num = int(codigo)
                self.cursor.execute(
                    "SELECT id FROM equipamentos WHERE CAST(codigo_barras AS INTEGER) = ?",
                    (num,)
                )
                row = self.cursor.fetchone()
            except ValueError:
                row = None

        # 3) fallback: erro se não encontrar
        if not row:
            messagebox.showerror("Erro", f"Equipamento '{codigo}' não encontrado!")
            return None

        return row[0]

    def limpar_campos_evento(self):
        self.nome_evento.delete(0, tk.END)
        self.local_evento.delete(0, tk.END)
        self.responsavel_evento.delete(0, tk.END)
        self.data_inicio.delete(0, tk.END)
        self.data_fim.delete(0, tk.END)
        self.codigo_evento.delete(0, tk.END)
        self.tabela_equip_evento.delete(*self.tabela_equip_evento.get_children())

    def mostrar_detalhes_evento(self):
        selecionado = self.tabela_eventos.selection()
        if not selecionado:
            messagebox.showwarning("Aviso", "Selecione um evento!")
            return
            
        # Obter ID diretamente da coluna correta
        evento_id = self.tabela_eventos.item(selecionado)['values'][0]
        
        # Debug: Mostrar ID selecionado
        print(f"ID do evento selecionado: {evento_id}")
        
        self.mostrar_detalhes_evento_por_id(evento_id)
    
        # Buscar dados do evento
        self.cursor.execute('''
            SELECT e.*, GROUP_CONCAT(eq.nome || ' (' || m.quantidade || ')', ', ')
            FROM eventos e
            LEFT JOIN movimentacoes m ON e.id = m.evento_id
            LEFT JOIN equipamentos eq ON m.equipamento_id = eq.id
            WHERE e.id = ?
            GROUP BY e.id
        ''', (evento_id,))
        
        evento = self.cursor.fetchone()
    
        # Criar janela de detalhes
        janela = tk.Toplevel()
        janela.title(f"Detalhes do Evento #{evento_id}")
        janela.geometry("800x600")
        
        # Frame principal
        main_frame = tk.Frame(janela)
        main_frame.pack(expand=True, fill='both', padx=20, pady=20)
        
        # Informações do evento
        info_text = f"""
        Nome do Evento: {evento[1]}
        Local: {evento[2]}
        Responsável: {evento[3]}
        Período: {evento[4]} a {evento[5]}
        Status: {evento[6]}
        """
    
        tk.Label(main_frame, text=info_text, font=('Arial', 12), justify='left').pack(anchor='w')
        
        # Tabela de equipamentos
        tk.Label(main_frame, text="Equipamentos Alocados:", font=('Arial', 12, 'bold')).pack(pady=10)
        
        columns = ("Código", "Equipamento", "Status Retorno")
        tree = ttk.Treeview(main_frame, columns=columns, show="headings", height=8)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150, anchor='center')
        
        # Preencher com dados
        self.cursor.execute('''
            SELECT eq.codigo_barras, eq.nome, 
                CASE WHEN EXISTS (
                    SELECT 1 FROM movimentacoes 
                    WHERE tipo = 'retorno' 
                    AND equipamento_id = m.equipamento_id
                    AND evento_id = m.evento_id
                ) THEN 'Devolvido' ELSE 'Pendente' END
            FROM movimentacoes m
            JOIN equipamentos eq ON m.equipamento_id = eq.id
            WHERE m.evento_id = ? AND m.tipo = 'saida'
        ''', (evento_id,))
    
        for equip in self.cursor.fetchall():
            tree.insert("", "end", values=equip)
        
        scroll_y = ttk.Scrollbar(main_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll_y.set)
        
        tree.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")

    def mostrar_detalhes_evento_por_id(self, evento_id):
        try:
            # Verificação inicial do ID
            if not evento_id or not str(evento_id).isdigit():
                messagebox.showerror("Erro", "ID do evento inválido!")
                return

            # Verificar existência do evento
            self.cursor.execute('SELECT id, nome_evento FROM eventos WHERE id = ?', (evento_id,))
            resultado = self.cursor.fetchone()
            
            if not resultado:
                messagebox.showerror("Erro", f"Evento ID {evento_id} não existe!")
                return
                
            print(f"Consultando detalhes para: ID {resultado[0]} - {resultado[1]}")

            # Buscar dados principais do evento
            self.cursor.execute('''
                SELECT 
                    nome_evento,
                    local_evento,
                    responsavel,
                    data_inicio,
                    data_fim,
                    status
                FROM eventos 
                WHERE id = ?
            ''', (evento_id,))
            dados_evento = self.cursor.fetchone()

            if not dados_evento:
                messagebox.showerror("Erro", "Dados do evento corrompidos!")
                return

            # Buscar equipamentos (consulta corrigida)
            self.cursor.execute('''
                SELECT
                    eq.codigo_barras,
                    eq.nome,
                    CASE WHEN EXISTS (
                        SELECT 1 
                        FROM movimentacoes r 
                        WHERE r.tipo = 'retorno'
                        AND r.equipamento_id = m.equipamento_id
                        AND r.evento_id = m.evento_id
                    ) THEN 'Devolvido' ELSE 'Pendente' END AS status
                FROM movimentacoes m
                JOIN equipamentos eq ON m.equipamento_id = eq.id
                WHERE m.evento_id = ?
                AND m.tipo = 'saida'
            ''', (evento_id,))
            equipamentos = self.cursor.fetchall()

            # Criar janela
            janela = tk.Toplevel()
            janela.title(f"Detalhes do Evento #{evento_id}")
            janela.geometry("1000x700")

            # Frame principal
            main_frame = tk.Frame(janela)
            main_frame.pack(expand=True, fill='both', padx=20, pady=20)

            # Informações do evento
            info_text = f"""
            Nome do Evento: {dados_evento[0]}
            Local: {dados_evento[1]}
            Responsável: {dados_evento[2]}
            Período: {dados_evento[3]} a {dados_evento[4]}
            Status: {dados_evento[5]}
            """
            tk.Label(main_frame, text=info_text, font=('Arial', 14), justify='left').pack(anchor='w', pady=10)

            # Tabela de equipamentos
            tk.Label(main_frame, text="Equipamentos Alocados:", font=('Arial', 14, 'bold')).pack(pady=10)

            columns = ("Código", "Equipamento", "Status")
            tree = ttk.Treeview(main_frame, columns=columns, show="headings", height=12)

            # Configurar colunas
            tree.heading("Código", text="Código")
            tree.heading("Equipamento", text="Equipamento")
            tree.heading("Status", text="Status")

            tree.column("Código", width=150, anchor='center')
            tree.column("Equipamento", width=300, anchor='w')
            tree.column("Status", width=150, anchor='center')

            # Adicionar dados com tratamento de nulos
            for equip in equipamentos:
                codigo = equip[0] if equip[0] else "N/A"
                nome = equip[1] if equip[1] else "Não especificado"
                status = equip[2] if equip[2] else "Pendente"
                tree.insert("", "end", values=(codigo, nome, status))

            # Mensagem se não houver equipamentos (corrigido para 3 colunas)
            if not equipamentos:
                tree.insert("", "end", values=("Nenhum equipamento registrado", "", ""))

            # Scrollbars
            scroll_y = ttk.Scrollbar(main_frame, orient="vertical", command=tree.yview)
            scroll_x = ttk.Scrollbar(main_frame, orient="horizontal", command=tree.xview)
            tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

            # Layout
            tree.pack(side="left", fill="both", expand=True)
            scroll_y.pack(side="right", fill="y")
            scroll_x.pack(side="bottom", fill="x")

        except Exception as e:
            messagebox.showerror("Erro", f"Falha crítica ao carregar detalhes: {str(e)}")

    def abrir_edicao_evento(self):
        selecionado = self.tabela_eventos.selection()
        if not selecionado:
            messagebox.showwarning("Aviso", "Selecione um evento!")
            return
    
        evento_id = self.tabela_eventos.item(selecionado)['values'][0]
        self.cursor.execute('SELECT status FROM eventos WHERE id = ?', (evento_id,))
        status = self.cursor.fetchone()[0]
        
        if status == 'Concluído':
            messagebox.showinfo("Info", "Eventos concluídos não podem ser editados!")
            return
    
        # Janela de edição
        self.janela_edicao = tk.Toplevel()
        self.janela_edicao.title(f"Editar Evento #{evento_id}")
        self.janela_edicao.geometry("1000x700")
        
        # Frame principal
        main_frame = tk.Frame(self.janela_edicao)
        main_frame.pack(expand=True, fill='both', padx=20, pady=20)
    
        # Dados do evento
        self.cursor.execute('''
            SELECT nome_evento, local_evento, responsavel, data_inicio, data_fim 
            FROM eventos WHERE id = ?
        ''', (evento_id,))
        dados_evento = self.cursor.fetchone()
        
        # Campos editáveis
        campos = [
            ("Nome do Evento:", dados_evento[0]),
            ("Local do Evento:", dados_evento[1]),
            ("Responsável:", dados_evento[2]),
            ("Data Início (DD/MM/AAAA):", dados_evento[3]),
            ("Data Fim (DD/MM/AAAA):", dados_evento[4])
        ]
    
        self.variaveis_edicao = {}
        for i, (label, valor) in enumerate(campos):
            tk.Label(main_frame, text=label, font=('Arial', 12)).grid(row=i, column=0, padx=10, pady=5, sticky='e')
            entry = tk.Entry(
                main_frame,
                font=('Arial', 12),
                width=60  # Largura aumentada
            )
            entry.insert(0, valor)
            entry.grid(row=i, column=1, padx=10, pady=5, sticky='ew')
            self.variaveis_edicao[label] = entry
        
        # Seção de equipamentos
        tk.Label(main_frame, text="Equipamentos do Evento:", font=('Arial', 14, 'bold')).grid(row=5, columnspan=2, pady=10)
        
        # Tabela de equipamentos
        columns = ("Código", "Equipamento", "Ações")
        self.tree_equip_edicao = ttk.Treeview(main_frame, columns=columns, show="headings", height=8)
    
        for col in columns:
            self.tree_equip_edicao.heading(col, text=col)
            self.tree_equip_edicao.column(col, width=150, anchor='center')
        
        # Preencher equipamentos
        self.cursor.execute('''
            SELECT eq.codigo_barras, eq.nome 
            FROM movimentacoes m
            JOIN equipamentos eq ON m.equipamento_id = eq.id
            WHERE m.evento_id = ? AND m.tipo = 'saida'
        ''', (evento_id,))
    
        for equip in self.cursor.fetchall():
            self.tree_equip_edicao.insert("", "end", values=(equip[0], equip[1], "Remover"))
        
        # Botões de ação
        btn_frame = tk.Frame(main_frame)
        btn_frame.grid(row=6, columnspan=2, pady=15)
        
        tk.Button(btn_frame, text="➕ Adicionar Equipamento", 
                command=lambda: self.adicionar_equipamento_edicao(evento_id),
                bg=self.VERDE_ALURA, fg='white').pack(side='left', padx=10)
        
        tk.Button(btn_frame, text="➖ Remover Selecionado", 
                command=lambda: self.remover_equipamento_edicao(evento_id),
                bg=self.VERMELHO_ALURA, fg='white').pack(side='left', padx=10)
        
        tk.Button(btn_frame, text="💾 Salvar Alterações", 
                command=lambda: self.salvar_edicao_evento(evento_id),
                bg=self.AZUL_MEDIO, fg='white').pack(side='left', padx=10)
        
        tk.Button(
            btn_frame,
            text="📝 Bloco de Anotações",
            command=lambda eid=evento_id: self._abrir_bloco_notas(eid),
            bg=self.CINZA_MEDIO, fg=self.AZUL_ALURA
        ).pack(side='left', padx=10)
        
        self.tree_equip_edicao.grid(row=7, columnspan=2, sticky='nsew')

        self.centralizar_janela(self.janela_edicao)

    def adicionar_equipamento_edicao(self, evento_id):
        """
        Abre um popup que permanece aberto para adicionar múltiplos
        equipamentos por código (scan ou digitação + Enter). Só fecha ao
        clicar em OK ou Cancelar.
        """
        # 1) Cria popup modal
        popup = tk.Toplevel(self.janela_edicao)
        popup.title(f"Adicionar Equipamento - Evento #{evento_id}")
        popup.geometry("400x400")
        popup.transient(self.janela_edicao)
        popup.grab_set()

        # 2) Frame de conteúdo
        frame = ttk.Frame(popup, padding=10)
        frame.pack(fill="both", expand=True)

        # 3) Label e Entry para o código
        lbl = ttk.Label(frame, text="Código de Barras:")
        lbl.pack(anchor="w", pady=(0,5))
        entry = ttk.Entry(frame, font=("Arial", 12))
        entry.pack(fill="x", pady=(0,10))
        entry.focus_set()

        # 4) Treeview temporário para pré-visualizar inserções
        cols = ("Código", "Nome", "")
        tree_tmp = ttk.Treeview(frame, columns=cols, show="headings", height=6)
        for col in cols:
            tree_tmp.heading(col, text=col)
            tree_tmp.column(col, anchor="w", width=100 if col != "" else 60)
        tree_tmp.pack(fill="both", expand=True, pady=(0,10))

        # 5) Botões OK e Cancelar
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x")
        btn_ok = ttk.Button(
            btn_frame, text="OK",
            command=lambda: popup.destroy()
        )
        btn_ok.pack(side="right", padx=5)
        btn_cancel = ttk.Button(
            btn_frame, text="Cancelar",
            command=lambda: (  # desfaz inserções temporárias
                self._recarregar_tree_equip_edicao(evento_id),
                popup.destroy()
            )
        )
        btn_cancel.pack(side="right")

        # Função interna para adicionar sem fechar popup
        def adicionar(event=None):
            codigo = entry.get().strip()
            if not codigo:
                return

            # --- 1) Valida ID e duplicatas ---
            equip_id = self.obter_id_por_codigo(codigo)
            if equip_id is None:
                messagebox.showwarning(
                    "Aviso", f"Código {codigo} não encontrado!",
                    parent=popup
                )
                entry.delete(0, tk.END)
                entry.focus_set()
                return

            # Verifica se já foi adicionado na edição
            for item in self.tree_equip_edicao.get_children():
                if self.tree_equip_edicao.item(item)['values'][0] == codigo:
                    messagebox.showwarning(
                        "Aviso", f"Equipamento {codigo} já adicionado!",
                        parent=popup
                    )
                    entry.delete(0, tk.END)
                    entry.focus_set()
                    return

            # --- 2) Verifica manutenção ---
            if self.esta_em_manutencao(equip_id):
                aviso = tk.Toplevel(popup)
                aviso.overrideredirect(True)
                x, y = self.winfo_pointerx(), self.winfo_pointery()
                aviso.geometry(f"+{x}+{y}")
                tk.Label(
                    aviso,
                    text="⚠️ Equipamento em manutenção!",
                    bg="yellow", fg="red",
                    font=("Arial", 12, "bold")
                ).pack(ipadx=10, ipady=5)
                aviso.after(2000, aviso.destroy)
                entry.delete(0, tk.END)
                entry.focus_set()
                return

            # --- 3) Insere na base e na Treeview principal e temporária ---
            try:
                self.cursor.execute(
                    '''INSERT INTO movimentacoes
                    (evento_id, equipamento_id, data_movimentacao, tipo)
                    VALUES (?, ?, ?, 'saida')''',
                    (evento_id, equip_id, datetime.now().strftime("%d/%m/%Y %H:%M"))
                )
                self.conn.commit()
            except Exception as e:
                self.conn.rollback()
                messagebox.showerror(
                    "Erro", f"Falha ao adicionar equipamento: {e}",
                    parent=popup
                )
                return

            # Busca nome e insere nas duas Treeviews
            nome = self.cursor.execute(
                'SELECT nome FROM equipamentos WHERE id = ?', (equip_id,)
            ).fetchone()[0]
            self.tree_equip_edicao.insert("", "end", values=(codigo, nome, "Remover"))
            tree_tmp.insert("", "end", values=(codigo, nome, ""))

            # Prepara próximo scan
            entry.delete(0, tk.END)
            entry.focus_set()

        # 6) Bind de Enter na Entry
        entry.bind("<Return>", adicionar)

    def remover_equipamento_edicao(self, evento_id):
        """
        Remove um equipamento da edição de um evento,
        deletando tanto a saída quanto qualquer retorno pendente.
        """
        sel = self.tree_equip_edicao.selection()
        if not sel:
            return

        item = sel[0]
        codigo = self.tree_equip_edicao.item(item)['values'][0]

        # --- 1) obtém o ID do equipamento ---
        equip_id = self.obter_id_por_codigo(codigo)
        if equip_id is None:
            # se, por algum motivo, não achar o código, apenas remove da lista visual
            self.tree_equip_edicao.delete(item)
            return

        try:
            # --- 2) deleta MOVIMENTAÇÕES desse evento+equipamento ---
            self.cursor.execute(
                '''DELETE FROM movimentacoes 
                WHERE evento_id = ? 
                    AND equipamento_id = ? 
                    AND tipo = 'saida' ''',
                (evento_id, equip_id)
            )
            self.cursor.execute(
                '''DELETE FROM movimentacoes 
                WHERE evento_id = ? 
                    AND equipamento_id = ? 
                    AND tipo = 'retorno' ''',
                (evento_id, equip_id)
            )
            self.conn.commit()

            # --- 3) remove da Treeview ---
            self.tree_equip_edicao.delete(item)
        except Exception as e:
            self.conn.rollback()
            messagebox.showerror(
                "Erro", 
                f"Falha ao remover equipamento: {e}",
                parent=self.janela_edicao
            )

    def validar_e_adicionar_equipamento_edicao(self, evento_id, codigo):
        # limpa espaços
        codigo = codigo.strip()
        if not codigo:
            messagebox.showwarning("Aviso", "Digite um código de barras!")
            return

        # 1) verificar existência e obter nome
        self.cursor.execute(
            'SELECT id, nome FROM equipamentos WHERE codigo_barras = ?',
            (codigo,)
        )
        resultado = self.cursor.fetchone()
        if not resultado:
            messagebox.showerror("Erro", "Equipamento não cadastrado!")
            return
        equip_id, nome_equip = resultado

        # 2) verificar se já saiu sem retorno
        self.cursor.execute('''
            SELECT COUNT(*) FROM movimentacoes
            WHERE equipamento_id = ?
            AND tipo = 'saida'
            AND NOT EXISTS (
                SELECT 1 FROM movimentacoes r
                WHERE r.tipo = 'retorno'
                    AND r.equipamento_id = ?
                    AND r.evento_id = movimentacoes.evento_id
            )
        ''', (equip_id, equip_id))
        if self.cursor.fetchone()[0] > 0:
            messagebox.showerror("Erro", "Equipamento já está em outro evento!")
            return

        # 3) registrar saída para este evento
        self.cursor.execute('''
            INSERT INTO movimentacoes
            (evento_id, equipamento_id, data_movimentacao, tipo)
            VALUES (?, ?, ?, 'saida')
        ''', (evento_id, equip_id, datetime.now().strftime("%d/%m/%Y %H:%M")))
        self.conn.commit()

        # 4) inserir na Treeview de edição com Código – Nome – Ações
        self.tree_equip_edicao.insert(
            "", "end",
            values=(codigo, nome_equip, "Remover")
        )


    def salvar_edicao_evento(self, evento_id):
        novos_dados = [
            self.variaveis_edicao["Nome do Evento:"].get(),
            self.variaveis_edicao["Local do Evento:"].get(),
            self.variaveis_edicao["Responsável:"].get(),
            self.variaveis_edicao["Data Início (DD/MM/AAAA):"].get(),
            self.variaveis_edicao["Data Fim (DD/MM/AAAA):"].get()
        ]
        
        try:
            self.cursor.execute('''
                UPDATE eventos SET
                    nome_evento = ?,
                    local_evento = ?,
                    responsavel = ?,
                    data_inicio = ?,
                    data_fim = ?
                WHERE id = ?
            ''', (*novos_dados, evento_id))
            
            self.conn.commit()
            self.atualizar_lista_eventos()
            messagebox.showinfo("Sucesso", "Alterações salvas com sucesso!")
            self.janela_edicao.destroy()
            
        except Exception as e:
            self.conn.rollback()
            messagebox.showerror("Erro", f"Falha ao salvar edição: {str(e)}")    

    def registrar_retorno_equipamentos(self):
        selecionado = self.tabela_eventos.selection()
        if not selecionado:
            messagebox.showwarning("Aviso", "Selecione um evento na tabela!")
            return

        evento_id = self.tabela_eventos.item(selecionado)['values'][0]

        # --- Janela de retorno ---
        popup = tk.Toplevel(self)
        popup.title("Registrar Retorno de Equipamentos")
        popup.geometry("800x800")
        popup.transient(self)
        popup.grab_set()

        frame = ttk.Frame(popup, padding=15)
        frame.pack(fill="both", expand=True)

        # Lista de pendentes
        lbl_pend = ttk.Label(frame, text="Pendentes de Retorno:", font=("Segoe UI", 12, "bold"))
        lbl_pend.grid(row=0, column=0, sticky="w")
        list_pend = tk.Listbox(frame, height=15)
        list_pend.grid(row=1, column=0, sticky="nsew", padx=(0,10), pady=5)

        # Lista de já devolvidos
        lbl_dev = ttk.Label(frame, text="Já Devolvidos:", font=("Segoe UI", 12, "bold"))
        lbl_dev.grid(row=0, column=1, sticky="w")
        list_dev = tk.Listbox(frame, height=15)
        list_dev.grid(row=1, column=1, sticky="nsew", padx=(10,0), pady=5)

        # Campo de entrada de código
        lbl_entry = ttk.Label(frame, text="Código de Barras:")
        lbl_entry.grid(row=2, column=0, sticky="w", pady=(10,0))
        entry_codigo = ttk.Entry(frame)
        entry_codigo.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0,10))
        entry_codigo.focus_set()  # já foca pra leitura

        # grades expansíveis
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(1, weight=1)

        def carregar_listas():
            list_pend.delete(0, tk.END)
            list_dev.delete(0, tk.END)

            # pendentes
            self.cursor.execute("""
                SELECT eq.codigo_barras, eq.nome
                FROM movimentacoes m
                JOIN equipamentos eq ON m.equipamento_id = eq.id
                WHERE m.evento_id = ?
                AND m.tipo = 'saida'
                AND NOT EXISTS (
                    SELECT 1 FROM movimentacoes r
                        WHERE r.evento_id = m.evento_id
                        AND r.equipamento_id = m.equipamento_id
                        AND r.tipo = 'retorno'
                )
            """, (evento_id,))
            for codigo, nome in self.cursor.fetchall():
                list_pend.insert(tk.END, f"{nome} ({codigo})")

            # já devolvidos
            self.cursor.execute("""
                SELECT eq.codigo_barras, eq.nome, r.data_movimentacao
                FROM movimentacoes r
                JOIN equipamentos eq ON r.equipamento_id = eq.id
                WHERE r.evento_id = ?
                AND r.tipo = 'retorno'
                ORDER BY r.id
            """, (evento_id,))
            for codigo, nome, dt in self.cursor.fetchall():
                list_dev.insert(tk.END, f"{nome} ({codigo}) – {dt}")

        def on_codigo_enter(event):
            codigo = entry_codigo.get().strip()
            if not codigo:
                return
            # verifica se está pendente
            itens = list_pend.get(0, tk.END)
            if not any(f"({codigo})" in it for it in itens):
                messagebox.showwarning("Aviso", f"Código {codigo} não está pendente!", parent=popup)
                entry_codigo.delete(0, tk.END)
                return

            # registra retorno
            self.cursor.execute("""
                INSERT INTO movimentacoes (
                evento_id, equipamento_id, data_movimentacao, tipo
                ) VALUES (
                ?, (SELECT id FROM equipamentos WHERE codigo_barras = ?),
                datetime('now','localtime'), 'retorno'
                )
            """, (evento_id, codigo))
            self.conn.commit()
            entry_codigo.delete(0, tk.END)
            carregar_listas()

            # se não sobrar pendentes, marca evento como concluído
            if list_pend.size() == 0:
                self.cursor.execute("UPDATE eventos SET status = 'Concluído' WHERE id = ?", (evento_id,))
                self.conn.commit()
                messagebox.showinfo("Concluído",
                    "Todos os equipamentos foram devolvidos.\n"
                    "Evento marcado como Concluído.", parent=popup)
                self.atualizar_lista_eventos()
                popup.destroy()

        # bind Enter no entry
        entry_codigo.bind("<Return>", on_codigo_enter)

        # inicia populações
        carregar_listas()

    def validar_e_registrar_retorno(self, codigo, evento_id, listbox):
        try:
            # Verificar se o equipamento pertence ao evento
            self.cursor.execute('''
                SELECT m.id, eq.nome 
                FROM movimentacoes m
                JOIN equipamentos eq ON m.equipamento_id = eq.id
                WHERE m.evento_id = ? 
                AND eq.codigo_barras = ?
                AND m.tipo = 'saida'
                AND NOT EXISTS (
                    SELECT 1 FROM movimentacoes 
                    WHERE tipo = 'retorno' 
                    AND equipamento_id = m.equipamento_id
                    AND evento_id = m.evento_id
                )
            ''', (evento_id, codigo))
            
            movimentacao = self.cursor.fetchone()
        
            if movimentacao:
                # Registrar retorno (SEM QUANTIDADE)
                self.cursor.execute('''
                    INSERT INTO movimentacoes 
                    (evento_id, equipamento_id, data_movimentacao, tipo)
                    VALUES (?, ?, ?, 'retorno')
                ''', (evento_id, self.obter_id_por_codigo(codigo), datetime.now().strftime("%d/%m/%Y %H:%M")))
                
                self.conn.commit()
                listbox.insert(tk.END, f"{codigo} - {movimentacao[1]} (Devolvido)")
            else:
                messagebox.showwarning("Aviso", "Equipamento não pertence ao evento ou já devolvido!")
        
        except Exception as e:
            self.conn.rollback()
            messagebox.showerror("Erro", f"Falha ao registrar retorno: {str(e)}")

    def finalizar_evento(self, evento_id, janela):
        # Verificar se todos foram devolvidos
        self.cursor.execute('''
            SELECT COUNT(*) 
            FROM movimentacoes 
            WHERE evento_id = ? 
            AND tipo = 'saida'
            AND NOT EXISTS (
                SELECT 1 FROM movimentacoes 
                WHERE tipo = 'retorno' 
                AND equipamento_id = movimentacoes.equipamento_id
                AND evento_id = movimentacoes.evento_id
            )
        ''', (evento_id,))
        
        pendentes = self.cursor.fetchone()[0]
    
        if pendentes == 0:
            self.cursor.execute('''
                UPDATE eventos 
                SET status = 'Concluído' 
                WHERE id = ?
            ''', (evento_id,))
            self.conn.commit()
            messagebox.showinfo("Sucesso", "Evento finalizado com sucesso!")
            janela.destroy()
            self.atualizar_lista_eventos()
        else:
            messagebox.showwarning("Aviso", f"Ainda há {pendentes} equipamentos pendentes!")

    def mostrar_historico_completo(self):
        janela = tk.Toplevel()
        janela.title("Histórico Completo de Eventos")
        janela.geometry("1080x720")
        
        main_frame = tk.Frame(janela)
        main_frame.pack(expand=True, fill='both', padx=20, pady=20)
        
        # Treeview para histórico
        columns = ("ID", "Evento", "Local", "Responsável", "Início", "Fim", "Status")
        tree = ttk.Treeview(main_frame, columns=columns, show="headings", height=20)
        
        widths = [50, 200, 150, 150, 100, 100, 100]
        for col, width in zip(columns, widths):
            tree.heading(col, text=col)
            tree.column(col, width=width, anchor='center')
        
        # Buscar todos os eventos
        self.cursor.execute('SELECT * FROM eventos')
        for evento in self.cursor.fetchall():
            tree.insert("", "end", values=evento, tags=(evento[6].lower(),)) 
        
        # Configurar estilo
        style = ttk.Style()
        style.map("Treeview",
            background=[('selected', '#cfd8dc')],
            foreground=[('selected', '#000000')])
        
        tree.tag_configure('concluído', background='#e8f5e9')
        tree.tag_configure('agendado', background='#fffde7')
        tree.tag_configure('em andamento', background='#ffebee')
        
        # Scrollbars
        scroll_y = ttk.Scrollbar(main_frame, orient="vertical", command=tree.yview)
        scroll_x = ttk.Scrollbar(main_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        
        # Layout
        tree.grid(row=0, column=0, sticky='nsew')
        scroll_y.grid(row=0, column=1, sticky='ns')
        scroll_x.grid(row=1, column=0, sticky='ew')
        
        # Configurar expansão
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Botão de detalhes
        btn_frame = tk.Frame(janela)
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="Ver Detalhes", 
             command=lambda: self.mostrar_detalhes_historico(tree),
             bg='#2196F3', fg='white').pack(side='left', padx=10)
        
        # Alterar a consulta SQL:
        self.cursor.execute('''
            SELECT 
                id,           -- Coluna 0: ID numérico
                nome_evento,   -- Coluna 1: Nome do evento
                local_evento,  -- Coluna 2: Local
                responsavel,   -- Coluna 3: Responsável
                data_inicio,   -- Coluna 4: Data de início
                data_fim,      -- Coluna 5: Data de fim
                status         -- Coluna 6: Status
            FROM eventos 
            WHERE status = 'Concluído'  -- Filtro opcional
        ''')
        
    def mostrar_detalhes_historico(self, tree):
        selecionado = tree.selection()
        if selecionado:
            # Pegar ID da coluna correta (ajustar índice conforme a tabela)
            valores = tree.item(selecionado)['values']
            evento_id = valores[0]
            
            self.mostrar_detalhes_evento_por_id(evento_id)

    def validar_periodo_evento(data_inicio, data_fim):
        try:
            inicio = datetime.strptime(data_inicio, "%d/%m/%Y")
            fim = datetime.strptime(data_fim, "%d/%m/%Y")
            
            if inicio > fim:
                return False, "Data inicial maior que final"
                
            if (fim - inicio).days > 30:
                return False, "Período máximo de 30 dias"
                
            return True, ""
            
        except ValueError:
            return False, "Formato inválido (DD/MM/AAAA)"
        
    # =============================================
    # MÉTODOS DE MANUTENÇÃO:
    # =============================================
    def cadastrar_saida_manutencao(self):
        """
        Cadastra a saída de um equipamento para manutenção,
        bloqueando se já estiver em manutenção.
        """
        codigo = self.entry_codigo_manutencao.get().strip()
        if not codigo:
            return

        # 1) obtém o ID do equipamento
        equip_id = self.obter_id_por_codigo(codigo)
        if equip_id is None:
            return

        # 2) verifica se já está em manutenção
        if self.esta_em_manutencao(equip_id):
            aviso = tk.Toplevel(self)
            aviso.overrideredirect(True)
            x, y = self.winfo_pointerx(), self.winfo_pointery()
            aviso.geometry(f"+{x}+{y}")
            tk.Label(
                aviso,
                text="⚠️ Equipamento já está em manutenção!",
                bg="yellow", fg="red",
                font=("Arial", 12, "bold")
            ).pack(ipadx=10, ipady=5)
            aviso.after(2000, aviso.destroy)
            return

        # 3) insere o registro de manutenção
        try:
            self.cursor.execute(
                '''INSERT INTO manutencao
                (equipamento_id, data_saida, local_manutencao, status)
                VALUES (?, ?, ?, 'Em manutenção')''',
                (equip_id,
                datetime.now().strftime("%d/%m/%Y %H:%M"),
                self.entry_local_manutencao.get().strip())
            )
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            messagebox.showerror("Erro", f"Falha ao cadastrar manutenção: {e}")
            return

        # 4) atualiza a lista de manutenção e limpa campos
        self.atualizar_lista_manutencao()
        self.entry_codigo_manutencao.delete(0, tk.END)
        self.entry_local_manutencao.delete(0, tk.END)
        messagebox.showinfo("Sucesso", "Saída para manutenção cadastrada!")

    def registrar_retorno_manutencao(self):
        """
        Marca como concluída a manutenção selecionada.
        Se o item já não estiver com status 'Em manutenção',
        exibe um aviso temporário.
        """
        # 1) Verifica se algo está selecionado
        selecionado = self.tabela_manutencao.selection()
        if not selecionado:
            messagebox.showwarning("Aviso", "Selecione um equipamento na lista!")
            return

        # 2) Obtém o ID da linha de manutenção
        manutencao_id = self.tabela_manutencao.item(selecionado)['values'][0]

        # 3) Verifica o status atual no banco
        self.cursor.execute(
            "SELECT status, equipamento_id FROM manutencao WHERE id = ?",
            (manutencao_id,)
        )
        row = self.cursor.fetchone()
        if not row:
            messagebox.showerror("Erro", "Registro de manutenção não encontrado!")
            return

        status_atual, equipamento_id = row

        # 4) Se não estiver realmente em manutenção, exibe popup de 2s e aborta
        if status_atual != 'Em manutenção':
            aviso = tk.Toplevel(self)
            aviso.overrideredirect(True)
            x, y = self.winfo_pointerx(), self.winfo_pointery()
            aviso.geometry(f"+{x}+{y}")
            tk.Label(
                aviso,
                text="⚠️ Este equipamento não está em manutenção!",
                bg="yellow",
                fg="red",
                font=("Arial", 12, "bold")
            ).pack(ipadx=10, ipady=5)
            aviso.after(2000, aviso.destroy)
            return

        # 5) Se tudo OK, atualiza o status para Concluído
        try:
            self.cursor.execute(
                "UPDATE manutencao SET status = 'Concluído' WHERE id = ?",
                (manutencao_id,)
            )
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            messagebox.showerror("Erro", f"Falha ao registrar retorno: {e}")
            return

        # 6) Atualiza as listas de manutenção e de inventário
        self.atualizar_lista_manutencao()
        self.listar_todos()  # recarrega o inventário para reexibir o equipamento

        # 7) Confirmação
        messagebox.showinfo("Sucesso", "Retorno registrado com sucesso!")

    def atualizar_lista_manutencao(self):
        self.tabela_manutencao.delete(*self.tabela_manutencao.get_children())
        self.cursor.execute('''
            SELECT m.id, e.codigo_barras, e.nome, 
                m.data_saida, m.local_manutencao, m.status
            FROM manutencao m
            JOIN equipamentos e ON m.equipamento_id = e.id
            ORDER BY m.id DESC
        ''')
        
        for item in self.cursor.fetchall():
            tag = 'em_manutencao' if item[5] == 'Em manutenção' else 'concluido'
            self.tabela_manutencao.insert("", "end", values=item, tags=(tag,))

    def criar_marca_dagua_fixa(self):
        
        # Frame minimalista
        self.marca_frame = tk.Frame(self)  # Usar self em vez de self.root
        lbl_marca = tk.Label(
            self.marca_frame,
            text="By Gabriel do Amaral Valverde | SEAGBH v1.1",
            font=('Arial', 8),
            fg=self.cores.AZUL_ALURA,
            bg=self.cores.CINZA_CLARO
        )
        
        lbl_marca.pack()
        
        # Posicionamento preciso
        self.marca_frame.place(
            relx=1.0,
            rely=1.0,
            anchor='se',
            x=-15,  # Margem direita aumentada
            y=-2   # Margem inferior aumentada
        )

        # Garantir camada superior sem sobrepor elementos
        self.marca_frame.lower()  # Envia para trás de todos os elementos

    def cadastrar(self):
        dados = {
            'codigo': self.codigo_barras.get().strip(),
            'nome': self.nome.get().strip(),
            'descricao': self.descricao.get().strip(),
            'localizacao': self.localizacao.get().strip()
        }
        
        if not dados['codigo'] or not dados['nome']:
            messagebox.showerror("Erro", "Código e nome são obrigatórios!")
            return
        
        try:
            self.cursor.execute('''
                INSERT INTO equipamentos 
                (codigo_barras, nome, descricao, localizacao, data_cadastro)
                VALUES (?, ?, ?, ?, ?)
            ''', (dados['codigo'], dados['nome'], dados['descricao'], 
                dados['localizacao'], datetime.now().strftime("%d/%m/%Y %H:%M")))
            
            self.conn.commit()
            self.criar_backup()
            self.mostrar_popup_temporario("Equipamento cadastrado com sucesso!")  # Novo pop-up
            self.listar_todos()  # Atualização imediata
            self.limpar_campos()
        
        except sqlite3.IntegrityError:
            messagebox.showerror("Erro", "Código já cadastrado!")

    def mostrar_popup_temporario(self, mensagem):
        popup = tk.Toplevel(self)
        popup.configure(bg=self.AZUL_ALURA)
        popup.title("Sucesso")
        popup.geometry("300x100")
        popup.attributes("-topmost", True)
        
        label = tk.Label(popup, 
            text=mensagem,
            bg=self.cores.AZUL_ALURA, fg=self.cores.BRANCO, 
            font=('Arial', 12),
            padx=20, 
            pady=10
        )
        label.pack()
        popup.after(1000, popup.destroy)

    def consultar(self):
        codigo = self.codigo_barras.get().strip()
        if not codigo:
            messagebox.showwarning("Aviso", "Digite um código!")
            return
            
        self.cursor.execute('SELECT * FROM equipamentos WHERE codigo_barras = ?', (codigo,))
        item = self.cursor.fetchone()
        
        if item:
            janela = tk.Toplevel()
            for i, (label, valor) in enumerate(zip(
                ["ID:", "Código:", "Nome:", "Descrição:", "Localização:", "Quantidade:", "Data:"], item)):
                tk.Label(janela, text=label, font='Arial 12 bold').grid(row=i, column=0, sticky='e', padx=10, pady=2)
                tk.Label(janela, text=valor).grid(row=i, column=1, sticky='w', padx=10, pady=2)
        else:
            messagebox.showinfo("Info", "Item não encontrado!")

    # Dentro do método listar_todos (atualizado):
    def listar_todos(self):
        self.tabela.delete(*self.tabela.get_children())
        self.cursor.execute("""
            SELECT id, codigo_barras, nome, localizacao, data_cadastro
            FROM equipamentos
            WHERE id NOT IN (
                SELECT equipamento_id
                FROM manutencao
                WHERE status = 'Em manutenção'
            )
        """)

        agora = datetime.now()
        for item in self.cursor.fetchall():
            data_cadastro = datetime.strptime(item[4], "%d/%m/%Y %H:%M")
            diferenca = (agora - data_cadastro).total_seconds()
            
            if diferenca < 120:  # 2 minutos em segundos
                self.tabela.insert("", "end", values=item, tags=('novo',))
            else:
                self.tabela.insert("", "end", values=item)

        self.tabela.tag_configure('novo', background=self.VERDE_ALURA)

    def ocultar_novos_itens(self):
        for item in self.tabela.get_children():
            self.tabela.detach(item)  # Oculta sem deletar
        
    def abrir_edicao(self):
        selecionado = self.tabela.selection()
        if not selecionado:
            messagebox.showwarning("Aviso", "Selecione um item!")
            return
        
        item_id = self.tabela.item(selecionado)['values'][0]
        self.cursor.execute('SELECT * FROM equipamentos WHERE id = ?', (item_id,))
        item = self.cursor.fetchone()
    
        if item:
            janela = tk.Toplevel()
            janela.title("Editar Item")
            janela.geometry("900x600")  # Triplo do tamanho original (300x200 estimado)
        
            # Frame principal com expansão
            main_frame = tk.Frame(janela)
            main_frame.pack(expand=True, fill='both', padx=20, pady=20)
            
            # Configurar grid para centralização
            main_frame.grid_columnconfigure(1, weight=1)
            
            # Fonte aumentada
            fonte_label = ('Arial', 14, 'bold')
            fonte_entry = ('Arial', 14)
        
            # Campos ampliados
            campos = [
                ("Nome:", 0, item[2]),
                ("Descrição:", 1, item[3]),
                ("Localização:", 2, item[4]),
            ]
        
            for label_text, row, valor in campos:
                tk.Label(main_frame, text=label_text, font=fonte_label).grid(
                    row=row, column=0, padx=15, pady=20, sticky='e')
            
                entry = tk.Entry(main_frame, font=fonte_entry, width=40)
                entry.insert(0, valor)
                entry.grid(row=row, column=1, padx=15, pady=20, sticky='ew')
            
                if label_text == "Quantidade:":
                    validate_cmd = (janela.register(self.validar_quantidade), '%P')
                    entry.config(
                        validate='key',
                        validatecommand=validate_cmd
                    )
                    setattr(self, 'edit_quantidade', entry)
                else:
                    setattr(self, f'edit_{label_text.lower().replace(":", "")}', entry)
        
            # Botão Salvar ampliado
            btn_salvar = tk.Button(
                main_frame,
                text="SALVAR ALTERAÇÕES",
                command=lambda: self.salvar_edicao(
                    item[0],
                    self.edit_nome.get(),
                    self.edit_descrição.get(),
                    self.edit_localização.get(),
                    janela
                ),
                font=('Arial', 14, 'bold'),
                bg='#4CAF50',
                fg='white',
                padx=20,
                pady=15
            )
            btn_salvar.grid(row=4, column=0, columnspan=2, pady=30, sticky='nsew')

    def salvar_edicao(self, item_id, nome, desc, local, janela):
        if not nome:
            messagebox.showerror("Erro", "Nome é obrigatório!")
            return
        
        try:
            self.cursor.execute('''
                UPDATE equipamentos SET
                nome = ?,
                descricao = ?,
                localizacao = ?
            WHERE id = ?''', (nome, desc, local, item_id))
            self.conn.commit()
            self.criar_backup()
            janela.destroy()
            self.listar_todos()

            # Registrar na auditoria
            detalhes = f"Nome: {nome} | Local: {local} | Descrição: {desc}"
            self.registrar_auditoria(
                tabela="equipamentos",
                item_id=item_id,
                acao="EDIÇÃO",
                detalhes=detalhes
            )

            messagebox.showinfo("Sucesso", "Alterações salvas!")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao atualizar: {str(e)}")

    def remover_item(self):
        """
        Remove um equipamento, apagando antes todos os registros
        relacionados em movimentacoes e manutencao para evitar
        violação de restrição de chave estrangeira.
        """
        # 1) Verifica se algo está selecionado na Treeview
        selecionado = self.tabela.selection()
        if not selecionado:
            messagebox.showwarning("Aviso", "Selecione um equipamento!")
            return

        # 2) Confirmação dupla: mensagem e PIN de segurança
        if not messagebox.askyesno(
            "Confirmar Exclusão",
            "Tem certeza que deseja excluir este equipamento e todos os registros relacionados?"
        ):
            return

        pin = simpledialog.askstring(
            "Verificação Final",
            "Digite o código de segurança de 4 dígitos:",
            show='*'
        )
        if pin != "2025":
            messagebox.showerror("Acesso Negado", "Código de segurança incorreto!")
            return

        # 3) Executa as deleções em cascata manualmente
        try:
            item_id = self.tabela.item(selecionado)['values'][0]

            # Apaga todas as movimentações ligadas a este equipamento
            self.cursor.execute(
                'DELETE FROM movimentacoes WHERE equipamento_id = ?',
                (item_id,)
            )
            # Apaga todas as manutenções ligadas a este equipamento
            self.cursor.execute(
                'DELETE FROM manutencao WHERE equipamento_id = ?',
                (item_id,)
            )
            # Finalmente apaga o próprio equipamento
            self.cursor.execute(
                'DELETE FROM equipamentos WHERE id = ?',
                (item_id,)
            )

            self.conn.commit()
            self.criar_backup()

            # Atualiza a listagem na interface
            self.listar_todos()
            messagebox.showinfo("Sucesso", "Equipamento removido com sucesso!")

        except sqlite3.Error as e:
            self.conn.rollback()
            messagebox.showerror("Erro", f"Falha na exclusão: {e}")

    def exportar_pdf(self):
        try:
            self.cursor.execute('''
                SELECT id, codigo_barras, nome, descricao, localizacao, data_cadastro 
                FROM equipamentos
            ''')
            dados = self.cursor.fetchall()
        
            if not dados:
                messagebox.showwarning("Aviso", "Nenhum item cadastrado!")
                return

            data_hora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            caminho = os.path.join(
                APPLICATION_DIR,
                "Relatórios", 
                "Relatórios de Inventário",
                f"Relatorio_Inventario_{data_hora}.pdf"
            )
            
            doc = SimpleDocTemplate(
                caminho,
                pagesize=A4,
                leftMargin=1*cm,
                rightMargin=1*cm
            )
            elementos = []
            estilos = getSampleStyleSheet()
        
            # Estilo otimizado
            estilo_celula = ParagraphStyle(
                name='CelulaCentralizada',
                parent=estilos["BodyText"],
                fontSize=9,
                leading=10,
                alignment=TA_CENTER,
                wordWrap='CJK',
                textColor=colors.HexColor("#333333")
            )

            # Título com margem inferior
            titulo = Paragraph(
                "<font size='14' color='#2A5A78'><b>RELATÓRIO DE INVENTÁRIO - SEAGBH</b></font>",
                estilos["Title"]
            )
            elementos.append(titulo)
            elementos.append(Spacer(1, 15))

            # Configurações de coluna para A4
            col_widths = [
                1.2*cm,  # ID
                3.0*cm,  # Código
                4.0*cm,  # Nome
                6.5*cm,  # Descrição
                3.5*cm,  # Localização
                2.8*cm   # Data
            ]  # Total: 20cm (dentro dos 21cm do A4)

            # Cabeçalho com alinhamento específico
            cabecalho = [
                Paragraph("<font color='#FFFFFF'><b>ID</b></font>", estilo_celula),
                Paragraph("<font color='#FFFFFF'><b>CÓDIGO</b></font>", estilo_celula),
                Paragraph("<font color='#FFFFFF'><b>NOME</b></font>", estilo_celula),
                Paragraph("<font color='#FFFFFF'><b>DESCRIÇÃO</b></font>", estilo_celula),
                Paragraph("<font color='#FFFFFF'><b>LOCALIZAÇÃO</b></font>", estilo_celula),
                Paragraph("<font color='#FFFFFF'><b>DATA</b></font>", estilo_celula)
            ]

            dados_tabela = [cabecalho]
            for item in dados:
                # Formatar data completa
                data_formatada = datetime.strptime(item[5], "%d/%m/%Y %H:%M").strftime("%d/%m/%Y %H:%M")
                
                linha = [
                    Paragraph(f"{item[0]}", estilo_celula),
                    Paragraph(f"{item[1]}", estilo_celula),
                    Paragraph(f"{item[2]}", estilo_celula),
                    Paragraph(f"{item[3]}", estilo_celula),
                    Paragraph(f"{item[4]}", estilo_celula),
                    Paragraph(data_formatada, estilo_celula)
                ]
                dados_tabela.append(linha)

            # Estilo de tabela profissional
            estilo_tabela = TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2A5A78")),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('FONTSIZE', (0,0), (-1,-1), 9),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#DEE2E6")),
                ('LEFTPADDING', (0,0), (-1,-1), 5),
                ('RIGHTPADDING', (0,0), (-1,-1), 5),
                ('BOTTOMPADDING', (0,0), (-1,0), 8)
            ])

            # Tabela com altura automática
            tabela = Table(
                dados_tabela,
                colWidths=col_widths,
                style=estilo_tabela,
                repeatRows=1,
                hAlign='CENTER'
            )

            elementos.append(tabela)
            doc.build(elementos)
            messagebox.showinfo("Sucesso", f"PDF gerado em:\n{os.path.abspath(caminho)}")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao gerar PDF: {str(e)}")

    def remover_evento(self):
        selecionado = self.tabela_eventos.selection()
        if not selecionado:
            messagebox.showwarning("Aviso", "Selecione um evento!")
            return
        
        # Primeira etapa de confirmação
        if not messagebox.askyesno(
            "Confirmar Exclusão", 
            "Tem certeza que deseja excluir este evento e todos os registros relacionados?"
        ):
            return
        
        # Segunda etapa - Mesmo PIN
        pin = simpledialog.askstring(
            "Verificação Final",
            "Digite o código de segurança de 4 dígitos:",
            show='*'
        )
        
        if pin != "2025":
            messagebox.showerror("Acesso Negado", "Código de segurança incorreto!")
            return
        
        try:
            evento_id = self.tabela_eventos.item(selecionado)['values'][0]
            self.cursor.execute('DELETE FROM eventos WHERE id = ?', (evento_id,))
            self.conn.commit()
            self.atualizar_lista_eventos()
            messagebox.showinfo("Sucesso", "Evento excluído com sucesso!")
            
        except sqlite3.Error as e:
            self.conn.rollback()
            messagebox.showerror("Erro", f"Falha na exclusão: {str(e)}")

    def janela_adicionar_equipamentos(self, evento_id):
        """
        Janela pop-up onde o usuário faz a leitura/entrada de códigos
        e vê a lista de equipamentos já adicionados ao evento.
        """
        janela = tk.Toplevel(self)
        janela.title(f"Adicionar Equipamentos - Evento #{evento_id}")
        janela.geometry("600x400")
        main_frame = tk.Frame(janela, bg=self.cores.CINZA_CLARO)
        main_frame.pack(expand=True, fill='both', padx=20, pady=20)

        # Entrada de código de barras
        self.entry_codigo = tk.Entry(main_frame, font=('Arial', 14), width=40)
        self.entry_codigo.pack(pady=10, fill='x', expand=True)

        # Botões de ação
        btn_frame = tk.Frame(main_frame, bg=self.cores.CINZA_CLARO)
        btn_frame.pack(pady=20)

        # ➕ Adicionar equipamento
        tk.Button(
            btn_frame,
            text="➕ Adicionar",
            command=lambda: self.validar_e_adicionar_equipamento(evento_id, janela),
            bg=self.VERDE_ALURA, fg='white', font=('Arial', 12)
        ).pack(side='left', padx=10)

        # ✅ Finalizar cadastro — NÃO marca o evento como concluído
        tk.Button(
            btn_frame,
            text="✅ Finalizar Cadastro",
            command=lambda: self._concluir_criacao_evento(evento_id, janela),
            bg='#4CAF50', fg='white', font=('Arial', 12, 'bold')
        ).pack(side='left', padx=10)

        # Lista de equipamentos já adicionados
        self.lista_equipamentos = tk.Listbox(main_frame, font=('Arial', 12), height=10)
        scrollbar = tk.Scrollbar(main_frame, command=self.lista_equipamentos.yview)
        self.lista_equipamentos.config(yscrollcommand=scrollbar.set)
        self.lista_equipamentos.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

    def _concluir_criacao_evento(self, evento_id, janela):
        """
        Fecha a janela de adição sem alterar o status do evento,
        que permanece como 'Agendado'.
        """
        janela.destroy()
        # Atualiza a Treeview de eventos para exibir o novo evento
        self.atualizar_lista_eventos()

    def validar_e_adicionar_equipamento(self, evento_id, janela):
        """
        Lê o código da Entry, verifica no banco se existe e está disponível,
        registra a saída e coloca o item na listbox.
        """
        codigo = self.entry_codigo.get().strip()
        if not codigo:
            messagebox.showwarning("Aviso", "Digite um código!")
            return

        try:
            # Verifica existência
            self.cursor.execute(
                'SELECT id, nome FROM equipamentos WHERE codigo_barras = ?',
                (codigo,)
            )
            resultado = self.cursor.fetchone()
            if not resultado:
                messagebox.showerror("Erro", "Equipamento não cadastrado!")
                return
            equip_id, nome = resultado

            # Verifica se já saiu sem retorno (NOTE que usamos apenas UM parâmetro agora)
            self.cursor.execute('''
                SELECT COUNT(*) FROM movimentacoes
                WHERE equipamento_id = ? AND tipo = 'saida'
                AND NOT EXISTS (
                    SELECT 1 FROM movimentacoes r
                        WHERE r.tipo = 'retorno'
                        AND r.equipamento_id = movimentacoes.equipamento_id
                        AND r.evento_id = movimentacoes.evento_id
                )
            ''', (equip_id,))
            if self.cursor.fetchone()[0] > 0:
                messagebox.showerror("Erro", "Equipamento já está em outro evento!")
                return

            # Registra saída
            self.cursor.execute('''
                INSERT INTO movimentacoes
                (evento_id, equipamento_id, data_movimentacao, tipo)
                VALUES (?, ?, ?, 'saida')
            ''', (
                evento_id,
                equip_id,
                datetime.now().strftime("%d/%m/%Y %H:%M")
            ))
            self.conn.commit()

            # Atualiza listbox e limpa Entry
            self.lista_equipamentos.insert(tk.END, f"{codigo} - {nome}")
            self.entry_codigo.delete(0, tk.END)

        except sqlite3.Error as e:
            self.conn.rollback()
            messagebox.showerror("Falha ao adicionar equipamento:", str(e))
        
    def finalizar_evento(self, evento_id, janela):
        try:
            # Verificar se há equipamentos pendentes
            self.cursor.execute('''
                SELECT COUNT(*) 
                FROM movimentacoes 
                WHERE evento_id = ? 
                AND tipo = 'saida'
                AND NOT EXISTS (
                    SELECT 1 FROM movimentacoes 
                    WHERE tipo = 'retorno' 
                    AND equipamento_id = movimentacoes.equipamento_id
                    AND evento_id = movimentacoes.evento_id
                )
            ''', (evento_id,))
            
            pendentes = self.cursor.fetchone()[0]
        
            if pendentes == 0:
                # Atualizar status para "Concluído"
                self.cursor.execute('''
                    UPDATE eventos 
                    SET status = 'Concluído' 
                    WHERE id = ?
                ''', (evento_id,))
                self.conn.commit()
                
                # Fechar janela e atualizar lista
                janela.destroy()
                self.atualizar_lista_eventos()
                messagebox.showinfo("Sucesso", "Evento finalizado com sucesso!")
            else:
                messagebox.showwarning("Aviso", f"Ainda há {pendentes} equipamentos pendentes!")
            
        except Exception as e:
            self.conn.rollback()
            messagebox.showerror("Erro", f"Falha ao finalizar evento: {str(e)}")

    def atualizar_lista_eventos(self):
        # 1) Limpa todos os itens existentes
        self.tabela_eventos.delete(*self.tabela_eventos.get_children())

        # 2) Busca do banco — continua ordenando por ID (descendente) se quiser
        self.cursor.execute('''
            SELECT id, nome_evento, local_evento, responsavel, 
                data_inicio, data_fim, status 
            FROM eventos
            ORDER BY id DESC
        ''')
        for evento in self.cursor.fetchall():
            tag = 'concluido' if evento[6] == 'Concluído' else 'agendado'
            self.tabela_eventos.insert("", "end", values=evento, tags=(tag,))

        # ─── A PARTIR DAQUI, REORDENAÇÃO DINÂMICA ───

        # 3) Captura a lista de todos os IDs de item, na ordem atual do Treeview
        all_iids = list(self.tabela_eventos.get_children())

        # 4) Separa em duas listas conforme a tag (status)
        em_andamento = []
        concluidos   = []
        for iid in all_iids:
            # obtém a tag associada (pode usar get_tags()[0] se multitag)
            tags = self.tabela_eventos.item(iid, 'tags')
            if 'concluido' in tags:
                concluidos.append(iid)
            else:
                em_andamento.append(iid)

        # 5) Move itens de volta: primeiro ‘agendado’, depois ‘concluido’
        for iid in em_andamento + concluidos:
            self.tabela_eventos.move(iid, '', 'end')

    def registrar_auditoria(self, tabela, item_id, acao, detalhes=""):
        try:
            self.cursor.execute('''
                INSERT INTO auditoria 
                (tabela, item_id, acao, detalhes, data)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                tabela,
                item_id,
                acao.upper(),
                detalhes,
                datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            ))
            self.conn.commit()
        except Exception as e:
            print(f"Erro ao registrar auditoria: {str(e)}")

    # ====== NOVOS MÉTODOS ======
    def fazer_backup(self):
        try:
            # Verificação preliminar de permissões
            if not os.access(".", os.W_OK):
                raise PermissionError("Sem permissão de escrita no diretório atual")

            data = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = os.path.join("Backups")
            
            # Criar diretório se não existir
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
                print(f"Diretório de backup criado: {backup_dir}")

            # Nome do arquivo compactado
            zip_name = os.path.join(backup_dir, f"backup_{data}.zip")
            
            # Criar ZIP com compactação máxima
            with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
                # Adicionar banco de dados
                zipf.write("seaghb.db", arcname="seaghb.db")
                
                # Adicionar metadados (opcional)
                zipf.writestr("metadata.txt", 
                    f"""SEAGBH Backup
    Data: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
    Versão Sistema: 1.0
    Tamanho Original: {os.path.getsize('seaghb.db')} bytes
    """)

            # Rotação de backups (mantém últimos 7)
            backups = sorted(
                [os.path.join(backup_dir, f) for f in os.listdir(backup_dir) if f.endswith('.zip')],
                key=os.path.getctime,
                reverse=True
            )
            
            for old_backup in backups[7:]:
                try:
                    os.remove(old_backup)
                    print(f"Backup antigo removido: {old_backup}")
                except Exception as e:
                    print(f"Erro ao remover backup: {str(e)}")

            print(f"Backup realizado com sucesso: {zip_name}")
            return True

        except PermissionError as pe:
            messagebox.showerror("Erro de Permissão", 
                f"Falha no backup:\n{str(pe)}\nVerifique as permissões de escrita.")
            return False
            
        except Exception as e:
            messagebox.showerror("Erro Grave", 
                f"Falha crítica no backup:\n{str(e)}")
            return False
    
    # ====== NOVO MÉTODO PARA ABRIR MENU DE UTILITÁRIOS ======
    def abrir_menu_utilitarios(self):
        janela = tk.Toplevel()
        janela.title("Utilitários do Sistema")
        janela.geometry("300x240")  # ajustei a altura para caber o novo botão
        
        # Container principal
        main_frame = tk.Frame(janela, padx=20, pady=20)
        main_frame.pack(expand=True, fill='both')
        
        # Botões do menu
        botoes = [
            ("📜 Histórico de Alterações", self.mostrar_auditoria),
            ("🔄 Restaurar Backup",         self.criar_utilitario_restauracao),
            ("🔍 Ver Atrasos",             self.checar_eventos_atrasados),   # ← novo
            ("🛡️ Verificar Permissões",    self.verificar_permissoes)
        ]
        
        for texto, comando in botoes:
            btn = ttk.Button(
                main_frame,
                text=texto,
                command=comando,
                style="Neutral.TButton",
                width=25
            )
            btn.pack(pady=5)

        # Botão de fechar
        btn_fechar = ttk.Button(
            main_frame,
            text="✖️ Fechar",
            command=janela.destroy,
            style="Danger.TButton",
            width=25
        )
        btn_fechar.pack(pady=(10,0))

    # ====== NOVO MÉTODO DE VERIFICAÇÃO ======
    def verificar_permissoes(self):
        problemas = []
        
        # Verificar permissão de escrita nos backups
        backup_dir = "Backups"
        if not os.access(backup_dir, os.W_OK) if os.path.exists(backup_dir) else False:
            problemas.append(f"Sem permissão de escrita em: {backup_dir}")
        
        # Verificar permissão no banco de dados
        if not os.access("seaghb.db", os.W_OK):
            problemas.append("Sem permissão de escrita no banco de dados")
        
        # Verificar permissão de execução
        if not os.access(".", os.X_OK):
            problemas.append("Sem permissão de execução no diretório atual")
        
        # Resultado
        if problemas:
            msg = "Problemas críticos encontrados:\n\n" + "\n".join(problemas)
            messagebox.showerror("Verificação de Permissões", msg)
        else:
            messagebox.showinfo("Verificação de Permissões", 
                            "Todas as permissões necessárias estão OK!")
            
    def esta_em_manutencao(self, equipamento_id):
        """
        Retorna True se o equipamento estiver com status 'Em manutenção'.
        """
        self.cursor.execute(
            "SELECT status FROM manutencao WHERE equipamento_id = ?",
            (equipamento_id,)
        )
        row = self.cursor.fetchone()
        return bool(row and row[0] == 'Em manutenção')
           
    def verificar_inatividade_continua(self):
        if self.autenticado_equipamentos:
            if time.time() - self.ultima_atividade > self.tempo_inatividade:
                self.bloquear_aba_equipamentos()
        self.after(1000, self.verificar_inatividade_continua)  # Verificar a cada 1s

    def criar_utilitario_restauracao(self):
        janela = tk.Toplevel()
        janela.title("Restauração de Backup")
        janela.geometry("500x400")
        janela.grab_set()

        list_frame = tk.Frame(janela)
        list_frame.pack(expand=True, fill='both', padx=20, pady=10)

        # Listbox para mostrar backups
        self.lista_backups = tk.Listbox(
            list_frame,
            font=("Consolas", 11),
            bg=self.cores.BRANCO,
            fg=self.cores.AZUL_ALURA,
            selectbackground=self.cores.AZUL_MEDIO,
            activestyle="dotbox",
            selectmode="single"
        )

        scroll_y = ttk.Scrollbar(list_frame)
        scroll_x = ttk.Scrollbar(list_frame, orient="horizontal")

        self.lista_backups.config(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        scroll_y.config(command=self.lista_backups.yview)
        scroll_x.config(command=self.lista_backups.xview)

        self.lista_backups.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")

        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)

        # Carregar arquivos de backup .db
        self.atualizar_lista_backups()

        # Botões
        btn_frame = ttk.Frame(janela)
        btn_frame.pack(pady=10)

        ttk.Button(
            btn_frame,
            text="✔ Restaurar Selecionado",
            command=lambda: self.executar_restauracao(janela),
            style="Success.TButton"
        ).pack(side="left", padx=10)

        ttk.Button(
            btn_frame,
            text="✖ Cancelar",
            command=janela.destroy,
            style="Danger.TButton"
        ).pack(side="right", padx=10)

        self.centralizar_janela(janela)

    def atualizar_lista_backups(self):
        self.lista_backups.delete(0, tk.END)
        backup_dir = os.path.join(APPLICATION_DIR, "Backups")
        arquivos = sorted(
            [f for f in os.listdir(backup_dir) if f.endswith(".db")],
            key=lambda f: os.path.getctime(os.path.join(backup_dir, f)),
            reverse=True
        )
        for nome in arquivos:
            self.lista_backups.insert(tk.END, nome)

    def executar_restauracao(self, janela):
        selecionado = self.lista_backups.curselection()
        if not selecionado:
            messagebox.showwarning("Aviso", "Selecione um backup na lista!")
            return

        nome_arquivo = self.lista_backups.get(selecionado)
        caminho_backup = os.path.join(APPLICATION_DIR, "Backups", nome_arquivo)

        if not messagebox.askyesno(
            "Confirmação Final",
            "⚠️ Esta ação irá:\n\n1. Substituir os dados atuais\n2. Fechar o app\n\nDeseja continuar?"
        ):
            return

        try:
            self.conn.close()
            shutil.copy(caminho_backup, get_db_path())
            messagebox.showinfo("Sucesso", "Backup restaurado com sucesso! Reinicie o aplicativo.")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Erro", f"Falha na restauração:\n{str(e)}")

    def centralizar_janela(self, janela):
        # Centralizar janela na tela
        janela.update_idletasks()
        largura = janela.winfo_width()
        altura = janela.winfo_height()
        x = (janela.winfo_screenwidth() // 2) - (largura // 2)
        y = (janela.winfo_screenheight() // 2) - (altura // 2)
        janela.geometry(f'+{x}+{y}')
            
    def listar_backups(self):
        backup_dir = "Backups"
        if not os.path.exists(backup_dir):
            return []
            
        return sorted(
            [f for f in os.listdir(backup_dir) if f.endswith('.zip')],
            key=lambda x: os.path.getctime(os.path.join(backup_dir, x)),
            reverse=True
        )

    def checar_eventos_atrasados(self):
        """
        Abre um popup listando eventos cuja data_fim já passou
        e que ainda tenham equipamentos sem retorno.
        """
        hoje = datetime.now().strftime("%d/%m/%Y")
        # Consulta: eventos vencidos e com saída sem retorno
        self.cursor.execute('''
            SELECT e.id, e.nome_evento, e.data_fim, COUNT(m.equipamento_id) as pendentes
            FROM eventos e
            JOIN movimentacoes m ON m.evento_id = e.id AND m.tipo = 'saida'
            LEFT JOIN (
                SELECT evento_id, equipamento_id
                FROM movimentacoes
                WHERE tipo = 'retorno'
            ) r ON r.evento_id = m.evento_id AND r.equipamento_id = m.equipamento_id
            WHERE strftime(
                '%Y-%m-%d',
                substr(e.data_fim,7,4) || '-' ||
                substr(e.data_fim,4,2) || '-' ||
                substr(e.data_fim,1,2)
                ) < date('now')
            AND r.equipamento_id IS NULL
            GROUP BY e.id
            HAVING pendentes > 0;
        ''')
        atrasados = self.cursor.fetchall()
        if not atrasados:
            return  # nada a alertar

        # Cria popup
        popup = tk.Toplevel(self)
        popup.title("⚠️ Eventos Atrasados")
        popup.geometry("600x300")
        popup.grab_set()

        lbl = tk.Label(
            popup,
            text="Eventos vencidos com equipamentos pendentes:",
            font=("Segoe UI", 14, "bold"),
            fg=self.cores.VERMELHO_ALURA
        )
        lbl.pack(pady=(10,5))

        # Treeview para mostrar resultados
        cols = ("ID", "Evento", "Data Fim", "Pendências")
        tree = ttk.Treeview(popup, columns=cols, show="headings", height=8)
        for col, w in zip(cols, (50, 250, 100, 100)):
            tree.heading(col, text=col)
            tree.column(col, width=w, anchor="center")
        tree.pack(expand=True, fill="both", padx=10)

        for evento_id, nome, data_fim, pend in atrasados:
            tree.insert("", "end", values=(evento_id, nome, data_fim, pend))

        # Botão de fechar
        btn = ttk.Button(popup, text="OK", command=popup.destroy, style="Neutral.TButton")
        btn.pack(pady=10)
                 
    def limpar_campos_evento(self):
        self.nome_evento.delete(0, tk.END)
        self.local_evento.delete(0, tk.END)
        self.responsavel_evento.delete(0, tk.END)
        self.data_inicio.delete(0, tk.END)
        self.data_fim.delete(0, tk.END)

    def _abrir_bloco_notas(self, evento_id=None):
        """
        Bloco de notas que:
        • Na edição (evento_id fornecido): salva direto no banco.
        • Na criação (evento_id None): salva em self._conteudo_notas.
        Fecha e salva tanto com o botão “Salvar” quanto clicando no “X”.
        """
        # 1) Cria o popup
        popup = tk.Toplevel(self)
        popup.title("Bloco de Anotações")
        popup.geometry("600x400")
        popup.transient(self)
        popup.grab_set()

        # 2) Frame interno e Text widget
        frame = ttk.Frame(popup, padding=10)
        frame.pack(fill="both", expand=True)
        text_widget = tk.Text(frame, wrap="word", font=("Segoe UI", 11))
        text_widget.pack(fill="both", expand=True, padx=5, pady=(0,10))

        # 3) Carrega conteúdo anterior
        if evento_id is None:
            # criação: usa buffer temporário
            text_widget.insert("1.0", self._conteudo_notas)
        else:
            # edição: traz do banco
            self.cursor.execute("SELECT notas FROM eventos WHERE id = ?", (evento_id,))
            nota_bd = self.cursor.fetchone()[0] or ""
            text_widget.insert("1.0", nota_bd)

        # 4) Funções internas de salvar / fechar
        def _salvar_e_fechar():
            conteudo = text_widget.get("1.0", "end-1c")
            if evento_id is None:
                # criação: guarda em memória
                self._conteudo_notas = conteudo
            else:
                # edição: grava no banco
                self.cursor.execute(
                    "UPDATE eventos SET notas = ? WHERE id = ?",
                    (conteudo, evento_id)
                )
                self.conn.commit()
            popup.destroy()

        def _cancelar_e_fechar():
            # descartar mudanças em criação, retorna ao texto anterior
            popup.destroy()

        # 5) Override do botão “X” da janela
        popup.protocol("WM_DELETE_WINDOW", _salvar_e_fechar)

        # 6) Botões Salvar e Cancelar
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x", pady=(0,5))
        ttk.Button(btn_frame, text="Cancelar", command=_cancelar_e_fechar).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="Salvar",   command=_salvar_e_fechar).pack(side="right")

    def _salvar_notas(self, conteudo):
        """Salva o conteúdo das notas num arquivo .txt via diálogo."""
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files","*.txt"),("All files","*.*")]
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(conteudo)
            messagebox.showinfo("Sucesso", "Anotações salvas com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível salvar:\n{e}")

if __name__ == "__main__":
    app = SEAGBH()  # Já constrói a interface internamente
    splash = SplashScreen(app)
    app.mainloop()