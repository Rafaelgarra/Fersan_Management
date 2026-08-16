import pandas as pd
import os
import sys
import time
import threading
import warnings
import subprocess
import tkinter as tk
import webbrowser
import requests
import zipfile
import shutil
from tkinter import scrolledtext, messagebox, ttk
from packaging import version

warnings.filterwarnings("ignore", category=UserWarning)

VERSAO_ATUAL = "1.3.5"
REPO_USER = "Rafaelgarra"
REPO_NAME = "Fersan_Management"
NOME_EXECUTAVEL = "RoboFersan.exe"

URL_CHECK_UPDATE = f"https://api.github.com/repos/{REPO_USER}/{REPO_NAME}/releases/latest"

if getattr(sys, 'frozen', False):
    CAMINHO_BASE = os.path.dirname(sys.executable)
else:
    CAMINHO_BASE = os.path.dirname(os.path.abspath(__file__))

PASTA_INPUT = os.path.join(CAMINHO_BASE, 'extratos_bancarios')
ARQUIVO_FINAL = os.path.join(CAMINHO_BASE, 'FLUXO_CAIXA_FERSAN.xlsx')

# ======================================================
# PALETA DE CORES – FERSAN DESIGN SYSTEM
# ======================================================
C_NAVY      = "#061B3A"
C_NAVY_DARK = "#031126"
C_PRIMARY   = "#087FEA"
C_ACCENT    = "#16C7E8"
C_POSITIVE  = "#32D583"
C_NEGATIVE  = "#F04438"
C_SURFACE   = "#F5F8FC"
C_WHITE     = "#FFFFFF"
C_TEXT      = "#172033"
C_MUTED     = "#64748B"
C_BORDER    = "#DDE3EE"
C_BG        = "#EEF2F8"

def limpar_valor(valor):
    try:
        if isinstance(valor, (int, float)): return float(valor)
        v_str = str(valor).strip()
        if ',' in v_str and '.' in v_str:
            v_str = v_str.replace('.', '').replace(',', '.')
        elif ',' in v_str:
            v_str = v_str.replace(',', '.')
        return float(v_str)
    except:
        return 0.0

def carregar_dados_existentes(log_func):
    if not os.path.exists(ARQUIVO_FINAL):
        return pd.DataFrame()

    log_func("📂 Lendo histórico...", "info")
    try:
        try:
            df_full = pd.read_excel(ARQUIVO_FINAL, sheet_name="FLUXO DE CAIXA", header=1)
        except:
            df_full = pd.read_excel(ARQUIVO_FINAL, sheet_name="FLUXO DE CAIXA", header=2)

        df_full.columns = df_full.columns.astype(str).str.upper().str.strip()

        try:
            df_ent = df_full.iloc[:, 0:8].copy()
            df_ent.columns = ["DATA", "TIPO", "DESCRIÇÃO", "VALOR ", "BANCO", "STATUS", "REFERENCIA", "OBSERVAÇÃO"]
        except Exception:
            df_ent = df_full.iloc[:, 0:7].copy()
            df_ent.columns = ["DATA", "TIPO", "DESCRIÇÃO", "VALOR ", "BANCO", "STATUS", "REFERENCIA"]
            df_ent["OBSERVAÇÃO"] = ""

        df_ent = df_ent[df_ent["DATA"].notna()]

        try:
            df_sai = df_full.iloc[:, 9:17].copy()
            df_sai.columns = ["DATA", "TIPO", "DESCRIÇÃO", "VALOR ", "BANCO", "STATUS", "REFERENCIA", "OBSERVAÇÃO"]
        except Exception:
            df_sai = df_full.iloc[:, 9:16].copy()
            df_sai.columns = ["DATA", "TIPO", "DESCRIÇÃO", "VALOR ", "BANCO", "STATUS", "REFERENCIA"]
            df_sai["OBSERVAÇÃO"] = ""

        df_sai = df_sai[df_sai["DATA"].notna()]

        df_historico = pd.concat([df_ent, df_sai], ignore_index=True)
        df_historico['DATA'] = pd.to_datetime(df_historico['DATA'], errors='coerce')
        df_historico = df_historico.dropna(subset=['DATA'])

        log_func(f" ↳ {len(df_historico)} registros recuperados.", "success")
        return df_historico
    except Exception as e:
        log_func(f"⚠️ Erro ao ler histórico (Pode ser layout antigo): {e}", "warning")
        return pd.DataFrame()

def processar_arquivo_individual(caminho, log_func):
    try:
        if caminho.lower().endswith('.csv'):
            try:
                df = pd.read_csv(caminho, sep=',')
                if 'RELEASE_DATE' not in df.columns and ';' in open(caminho).readline():
                      df = pd.read_csv(caminho, sep=';')
            except:
                df = pd.read_csv(caminho)
        else:
            df = pd.read_excel(caminho, skiprows=3)

        df.columns = [str(c).upper().strip() for c in df.columns]

        col_data = next((c for c in df.columns if 'DATE' in c or 'DATA' in c), None)
        col_val  = next((c for c in df.columns if 'NET_AMOUNT' in c or 'VALOR' in c or 'IMPORTE' in c), None)
        col_desc = next((c for c in df.columns if 'TYPE' in c or 'TIPO' in c or 'DESCRICAO' in c), None)
        col_ref  = next((c for c in df.columns if 'REFERENCE' in c or 'REF' in c), None)

        if not (col_data and col_val):
            return pd.DataFrame()

        lista = []
        for _, row in df.iterrows():
            try:
                val = limpar_valor(row[col_val])
                data = pd.to_datetime(row[col_data], dayfirst=True, errors='coerce')
                if pd.isna(data): continue

                lista.append({
                    "DATA": data,
                    "TIPO": "ENTRADA" if val > 0 else "SAIDA",
                    "DESCRIÇÃO": row[col_desc] if col_desc else "Movimentação",
                    "VALOR ": abs(val),
                    "BANCO": "MERCADO PAGO",
                    "STATUS": "COMPLETO",
                    "REFERENCIA": f"REF: {row.get(col_ref, '')}" if col_ref else "",
                    "OBSERVAÇÃO": ""
                })
            except: continue

        return pd.DataFrame(lista)
    except Exception as e:
        log_func(f"❌ Erro leitura {os.path.basename(caminho)}: {e}", "error")
        return pd.DataFrame()

class AutoUpdater:
    def __init__(self, current_version, api_url, root_window):
        self.current_version = current_version
        self.api_url = api_url
        self.root = root_window

    def verificar_atualizacao(self):
        try:
            response = requests.get(self.api_url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                tag_remota = data['tag_name'].replace('v', '')

                if version.parse(tag_remota) > version.parse(self.current_version):
                    assets = data.get('assets', [])

                    for asset in assets:
                        if asset['name'].lower().endswith('.zip'):
                            return asset['browser_download_url'], tag_remota, "ZIP"

                    for asset in assets:
                        if asset['name'].lower().endswith('.exe'):
                            return asset['browser_download_url'], tag_remota, "EXE"

            return None, None, None
        except Exception as e:
            print(f"Erro update: {e}")
            return None, None, None

    def realizar_atualizacao(self, download_url, nova_versao, tipo_arquivo, callback_progresso=None):
        try:
            msg_tipo = "completa (inclui novas funções)" if tipo_arquivo == "ZIP" else "rápida"
            resp = messagebox.askyesno(
                "🔄 Atualização Disponível",
                f"✨ A versão {nova_versao} está disponível!\n\nTipo: Atualização {msg_tipo}.\n\nDeseja atualizar agora?"
            )
            if not resp: return

            if not getattr(sys, 'frozen', False):
                messagebox.showinfo("Aviso", "Atualização só funciona no arquivo compilado (.exe).")
                return

            app_path = sys.executable
            app_dir = os.path.dirname(app_path)

            tmp_dir = os.path.join(app_dir, "temp_update")
            if os.path.exists(tmp_dir): shutil.rmtree(tmp_dir)
            os.makedirs(tmp_dir)

            nome_arquivo = f"update.{tipo_arquivo.lower()}"
            caminho_download = os.path.join(tmp_dir, nome_arquivo)

            resposta = requests.get(download_url, stream=True)
            total_size = int(resposta.headers.get('content-length', 0))

            with open(caminho_download, 'wb') as f:
                baixado = 0
                for chunk in resposta.iter_content(chunk_size=4096):
                    f.write(chunk)
                    baixado += len(chunk)

                    if callback_progresso and total_size > 0:
                        porcentagem = (baixado / total_size) * 100
                        callback_progresso(porcentagem, f"Baixando atualização... {int(porcentagem)}%")

            bat_script = os.path.join(app_dir, "updater.bat")

            if tipo_arquivo == "ZIP":
                with zipfile.ZipFile(caminho_download, 'r') as zip_ref:
                    zip_ref.extractall(tmp_dir)

                os.remove(caminho_download)

                cmd = f"""
                @echo off
                timeout /t 3 /nobreak > NUL
                echo Atualizando arquivos...

                xcopy "{tmp_dir}\\*" "{app_dir}\\" /E /H /C /I /Y

                rmdir /s /q "{tmp_dir}"

                start "" "{app_path}"
                del "%~f0"
                """

            else:
                nome_original = os.path.basename(app_path)
                novo_exe = os.path.join(app_dir, f"update_{nome_original}")
                shutil.move(caminho_download, novo_exe)
                shutil.rmtree(tmp_dir)

                cmd = f"""
                @echo off
                timeout /t 2 /nobreak > NUL
                del "{nome_original}"
                ren "{os.path.basename(novo_exe)}" "{nome_original}"
                start "" "{nome_original}"
                del "%~f0"
                """

            with open(bat_script, "w") as bat:
                bat.write(cmd)

            messagebox.showinfo("Reiniciando", "O aplicativo será fechado para aplicar a atualização.")
            subprocess.Popen([bat_script], shell=True)
            self.root.destroy()
            sys.exit()

        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao atualizar: {e}")


class RoboFinanceiroApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Fersan Management – Robô Financeiro")
        self.root.geometry("680x620")
        self.root.configure(bg=C_BG)
        self.root.resizable(False, False)

        self.processo_dash = None
        self.root.protocol("WM_DELETE_WINDOW", self.ao_fechar)

        self._build_ui()
        self.root.after(2000, self.checar_updates_bg)
        self.root.after(500, self.atualizar_status_pasta)

    def _build_ui(self):
        # ── HEADER ──────────────────────────────────────────────────────
        frame_header = tk.Frame(self.root, bg=C_NAVY, height=80)
        frame_header.pack(fill=tk.X)
        frame_header.pack_propagate(False)

        inner_header = tk.Frame(frame_header, bg=C_NAVY)
        inner_header.pack(expand=True)

        lbl_logo = tk.Label(
            inner_header,
            text="⚡ Fersan",
            font=("Segoe UI", 20, "bold"),
            bg=C_NAVY, fg=C_WHITE
        )
        lbl_logo.pack(side=tk.LEFT, padx=(0, 0))

        lbl_logo2 = tk.Label(
            inner_header,
            text="_Management",
            font=("Segoe UI", 20),
            bg=C_NAVY, fg=C_ACCENT
        )
        lbl_logo2.pack(side=tk.LEFT)

        lbl_slogan = tk.Label(
            frame_header,
            text="Financial Intelligence. Simplified.",
            font=("Segoe UI", 8),
            bg=C_NAVY, fg=C_MUTED
        )
        lbl_slogan.pack()

        # ── PILARES ─────────────────────────────────────────────────────
        frame_pilares = tk.Frame(self.root, bg=C_NAVY_DARK)
        frame_pilares.pack(fill=tk.X)

        pilares = [
            ("⚙️", "AUTOMAÇÃO", "Extratos bancários"),
            ("🏦", "CONSOLIDAÇÃO", "Dados centralizados"),
            ("📊", "INTELIGÊNCIA", "Fluxo de caixa"),
        ]
        for emoji, titulo, sub in pilares:
            col = tk.Frame(frame_pilares, bg=C_NAVY_DARK, padx=10, pady=6)
            col.pack(side=tk.LEFT, expand=True)
            tk.Label(col, text=emoji, font=("Segoe UI", 12), bg=C_NAVY_DARK, fg=C_WHITE).pack()
            tk.Label(col, text=titulo, font=("Segoe UI", 7, "bold"), bg=C_NAVY_DARK, fg=C_ACCENT).pack()
            tk.Label(col, text=sub, font=("Segoe UI", 7), bg=C_NAVY_DARK, fg=C_MUTED).pack()

        # ── STATUS DA PASTA ─────────────────────────────────────────────
        frame_status = tk.Frame(self.root, bg=C_BG, padx=20, pady=12)
        frame_status.pack(fill=tk.X)

        card_pasta = tk.Frame(frame_status, bg=C_WHITE, relief=tk.FLAT, bd=0, padx=12, pady=10)
        card_pasta.pack(fill=tk.X)
        card_pasta.configure(highlightbackground=C_BORDER, highlightthickness=1)

        row_pasta = tk.Frame(card_pasta, bg=C_WHITE)
        row_pasta.pack(fill=tk.X)

        lbl_pasta_icon = tk.Label(row_pasta, text="📁", font=("Segoe UI", 14), bg=C_WHITE)
        lbl_pasta_icon.pack(side=tk.LEFT, padx=(0, 8))

        pasta_info = tk.Frame(row_pasta, bg=C_WHITE)
        pasta_info.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(pasta_info, text="Pasta de Extratos Bancários", font=("Segoe UI", 9, "bold"), bg=C_WHITE, fg=C_TEXT).pack(anchor="w")
        tk.Label(pasta_info, text=".../extratos_bancarios/", font=("Segoe UI", 8), bg=C_WHITE, fg=C_MUTED).pack(anchor="w")

        self.lbl_contador = tk.Label(row_pasta, text="• 0 arquivos", font=("Segoe UI", 9, "bold"), bg=C_WHITE, fg=C_MUTED)
        self.lbl_contador.pack(side=tk.RIGHT, padx=(0, 4))

        self.btn_abrir_pasta = tk.Button(
            row_pasta, text="Abrir ↗",
            font=("Segoe UI", 8, "bold"),
            bg=C_BG, fg=C_PRIMARY,
            activebackground=C_BORDER,
            activeforeground=C_PRIMARY,
            relief=tk.FLAT, bd=0,
            cursor="hand2",
            command=self.abrir_pasta_extratos,
            padx=8, pady=3
        )
        self.btn_abrir_pasta.pack(side=tk.RIGHT, padx=4)

        # ── BOTÕES DE AÇÃO ───────────────────────────────────────────────
        frame_actions = tk.Frame(self.root, bg=C_BG, padx=20, pady=4)
        frame_actions.pack(fill=tk.X)

        self.btn_processar = tk.Button(
            frame_actions,
            text="▶  INICIAR CONSOLIDAÇÃO",
            font=("Segoe UI", 12, "bold"),
            bg=C_PRIMARY, fg=C_WHITE,
            activebackground="#0066CC",
            activeforeground=C_WHITE,
            relief=tk.FLAT, bd=0,
            height=2, cursor="hand2",
            command=self.iniciar_thread
        )
        self.btn_processar.pack(fill=tk.X, pady=(0, 6))

        self.btn_dashboard = tk.Button(
            frame_actions,
            text="📊  ABRIR DASHBOARD",
            font=("Segoe UI", 11, "bold"),
            bg=C_NAVY, fg=C_WHITE,
            activebackground="#0A2952",
            activeforeground=C_WHITE,
            relief=tk.FLAT, bd=0,
            height=2, cursor="hand2",
            command=self.abrir_dashboard
        )
        self.btn_dashboard.pack(fill=tk.X)

        # ── BARRA DE PROGRESSO ───────────────────────────────────────────
        frame_prog = tk.Frame(self.root, bg=C_BG, padx=20, pady=8)
        frame_prog.pack(fill=tk.X)

        self.lbl_progresso = tk.Label(
            frame_prog, text="Aguardando...",
            font=("Segoe UI", 9), bg=C_BG, fg=C_MUTED, anchor="w"
        )
        self.lbl_progresso.pack(fill=tk.X)

        style = ttk.Style()
        style.theme_use('default')
        style.configure(
            "Fersan.Horizontal.TProgressbar",
            troughcolor=C_BORDER,
            background=C_PRIMARY,
            bordercolor=C_BORDER,
            thickness=8
        )
        self.progress = ttk.Progressbar(
            frame_prog, orient="horizontal",
            length=640, mode="determinate",
            style="Fersan.Horizontal.TProgressbar"
        )
        self.progress.pack(fill=tk.X, pady=(2, 0))

        # ── CONSOLE DE LOG (DARK) ────────────────────────────────────────
        frame_log = tk.Frame(self.root, bg=C_BG, padx=20, pady=4)
        frame_log.pack(fill=tk.BOTH, expand=True)

        lbl_console = tk.Label(
            frame_log, text="Console de Atividades",
            font=("Segoe UI", 8, "bold"),
            bg=C_BG, fg=C_MUTED, anchor="w"
        )
        lbl_console.pack(fill=tk.X, pady=(0, 4))

        self.log_area = scrolledtext.ScrolledText(
            frame_log,
            font=("Consolas", 9),
            state='disabled',
            bg=C_NAVY_DARK,
            fg="#A8C7F0",
            insertbackground=C_ACCENT,
            selectbackground=C_PRIMARY,
            relief=tk.FLAT,
            bd=0,
            padx=10, pady=8
        )
        self.log_area.pack(fill=tk.BOTH, expand=True)

        # Define tags de colorização do console
        self.log_area.tag_configure("info",    foreground="#A8C7F0")
        self.log_area.tag_configure("success", foreground=C_POSITIVE)
        self.log_area.tag_configure("warning", foreground="#FBBF24")
        self.log_area.tag_configure("error",   foreground=C_NEGATIVE)
        self.log_area.tag_configure("accent",  foreground=C_ACCENT)

        # ── FOOTER ───────────────────────────────────────────────────────
        frame_footer = tk.Frame(self.root, bg=C_NAVY, height=28)
        frame_footer.pack(fill=tk.X, side=tk.BOTTOM)
        frame_footer.pack_propagate(False)

        tk.Label(
            frame_footer,
            text=f"v{VERSAO_ATUAL}  ·  Fersan_Management  ·  Layout 8 Colunas",
            font=("Segoe UI", 7),
            bg=C_NAVY, fg=C_MUTED
        ).pack(side=tk.LEFT, padx=12, pady=6)

        tk.Label(
            frame_footer,
            text="Financial Intelligence. Simplified.",
            font=("Segoe UI", 7, "italic"),
            bg=C_NAVY, fg=C_ACCENT
        ).pack(side=tk.RIGHT, padx=12, pady=6)

    # ── HELPERS ─────────────────────────────────────────────────────────
    def atualizar_status_pasta(self):
        """Atualiza o card de status da pasta de extratos."""
        try:
            if os.path.exists(PASTA_INPUT):
                arquivos = [
                    f for f in os.listdir(PASTA_INPUT)
                    if f.lower().endswith(('.xlsx', '.xls', '.csv'))
                ]
                count = len(arquivos)
                if count == 0:
                    self.lbl_contador.config(text="• 0 arquivos", fg=C_MUTED)
                elif count == 1:
                    self.lbl_contador.config(text=f"• {count} arquivo pronto", fg=C_POSITIVE)
                else:
                    self.lbl_contador.config(text=f"• {count} arquivos prontos", fg=C_POSITIVE)
            else:
                self.lbl_contador.config(text="• pasta não encontrada", fg=C_NEGATIVE)
        except Exception:
            pass
        self.root.after(3000, self.atualizar_status_pasta)

    def abrir_pasta_extratos(self):
        """Abre a pasta de extratos no Explorer."""
        if not os.path.exists(PASTA_INPUT):
            os.makedirs(PASTA_INPUT)
        if sys.platform == "win32":
            os.startfile(PASTA_INPUT)
        else:
            subprocess.Popen(["xdg-open", PASTA_INPUT])

    def checar_updates_bg(self):
        threading.Thread(target=self._processo_update, daemon=True).start()

    def _processo_update(self):
        updater = AutoUpdater(VERSAO_ATUAL, URL_CHECK_UPDATE, self.root)
        url, nova_versao, tipo = updater.verificar_atualizacao()

        if url:
            self.root.after(0, lambda: updater.realizar_atualizacao(url, nova_versao, tipo, self.atualizar_barra))

    def abrir_dashboard(self):
        try:
            if self.processo_dash is not None:
                try:
                    self.processo_dash.kill()
                    self.log("🔄 Reiniciando servidor do Dashboard...", "accent")
                except:
                    pass

            if getattr(sys, 'frozen', False):
                executavel_dash = os.path.join(CAMINHO_BASE, "launcher_dashboard.exe")
                if not os.path.exists(executavel_dash):
                    executavel_dash = os.path.join(sys._MEIPASS, "launcher_dashboard.exe")
                cmd = [executavel_dash]
                cwd = CAMINHO_BASE
            else:
                caminho_py = os.path.join(CAMINHO_BASE, "dashboard", "dashboard_fluxo.py")
                cmd = ["streamlit", "run", caminho_py, "--server.port=8501", "--server.headless=true"]
                cwd = CAMINHO_BASE

            self.log("🚀 Iniciando Dashboard...", "accent")

            self.processo_dash = subprocess.Popen(
                cmd,
                cwd=cwd,
                shell=False,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )

            url = "http://localhost:8501"
            self.log(f"🔗 Disponível em: {url}", "success")
            self.log("⏳ Abrindo navegador em 3 segundos...", "info")
            self.root.after(3000, lambda: webbrowser.open(url))

        except Exception as e:
            messagebox.showerror("Erro Dash", str(e))
            self.log(f"Erro Dash: {e}", "error")

    def ao_fechar(self):
        if self.processo_dash is not None:
            try:
                self.processo_dash.terminate()
            except Exception:
                pass
        self.root.destroy()
        sys.exit()

    def log(self, mensagem, nivel="info"):
        self.log_area.config(state='normal')
        prefixo = {
            "info":    "  »  ",
            "success": "  ✓  ",
            "warning": "  ⚠  ",
            "error":   "  ✗  ",
            "accent":  "  ◆  ",
        }.get(nivel, "  »  ")
        self.log_area.insert(tk.END, prefixo + mensagem + "\n", nivel)
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')

    def iniciar_thread(self):
        self.btn_processar.config(state=tk.DISABLED, bg="#4A6FA5", text="⏳  PROCESSANDO...")
        self.progress['value'] = 0
        threading.Thread(target=self.executar_processamento).start()

    def atualizar_barra(self, valor, texto):
        self.progress['value'] = valor
        self.lbl_progresso.config(text=f"{texto}  ({int(valor)}%)")
        self.root.update_idletasks()

    def executar_processamento(self):
        self.log("Iniciando motor de processamento...", "accent")

        if not os.path.exists(PASTA_INPUT):
            os.makedirs(PASTA_INPUT)
            self.log("Pasta criada. Adicione os arquivos de extrato.", "warning")
            self.finalizar(False, "Pasta criada!\n\nAdicione os arquivos de extrato bancário e execute novamente.")
            return

        self.atualizar_barra(5, "Lendo histórico...")

        abas_existentes = {}
        if os.path.exists(ARQUIVO_FINAL):
            try:
                todas_abas = pd.read_excel(ARQUIVO_FINAL, sheet_name=None)
                for nome_aba, df_aba in todas_abas.items():
                    if nome_aba != "FLUXO DE CAIXA":
                        abas_existentes[nome_aba] = df_aba
                self.log(f" ℹ️  Abas manuais encontradas: {list(abas_existentes.keys())}", "info")
            except Exception as e:
                self.log(f"Aviso: Não consegui ler outras abas ({e})", "warning")

        df_mestre = carregar_dados_existentes(self.log)

        arquivos = [os.path.join(PASTA_INPUT, f) for f in os.listdir(PASTA_INPUT) if f.lower().endswith(('.xlsx', '.xls', '.csv'))]

        if not arquivos:
            self.log("ERRO: Pasta de extratos está vazia.", "error")
            self.finalizar(True, "Nenhum arquivo encontrado na pasta de extratos.")
            return

        self.log(f"Arquivos encontrados: {len(arquivos)}", "info")
        novos = []
        total = len(arquivos)

        for i, arq in enumerate(arquivos):
            nome = os.path.basename(arq)
            self.atualizar_barra(10 + ((i + 1) / total * 70), f"Lendo: {nome}")
            self.log(f"Lendo: {nome}...", "info")
            temp = processar_arquivo_individual(arq, self.log)
            if not temp.empty: novos.append(temp)

        if not novos and df_mestre.empty:
            self.finalizar(True, "Nenhum dado válido encontrado nos arquivos.")
            return

        self.atualizar_barra(85, "Consolidando dados...")
        if novos:
            df_novos = pd.concat(novos, ignore_index=True)
            if not df_mestre.empty:
                df_mestre['DATA'] = pd.to_datetime(df_mestre['DATA'], errors='coerce')
                df_total = pd.concat([df_mestre, df_novos], ignore_index=True)
            else:
                df_total = df_novos
        else:
            df_total = df_mestre

        mask_manual = df_total['BANCO'].str.upper() != "MERCADO PAGO"
        df_manuais = df_total[mask_manual]
        df_auto = df_total[~mask_manual]

        qtd_antes = len(df_auto)
        df_auto = df_auto.drop_duplicates(subset=['DATA', 'DESCRIÇÃO', 'VALOR ', 'REFERENCIA'], keep='last')
        df_total = pd.concat([df_manuais, df_auto], ignore_index=True)

        qtd_dup = qtd_antes - len(df_auto)
        if qtd_dup > 0:
            self.log(f"Duplicatas removidas: {qtd_dup}", "warning")
        else:
            self.log("Nenhuma duplicata encontrada.", "success")

        self.atualizar_barra(95, "Salvando Excel...")

        df_total['VALOR '] = pd.to_numeric(df_total['VALOR '], errors='coerce').fillna(0.0)
        df_total = df_total.fillna("")

        df_total.sort_values('DATA', inplace=True)
        df_ent = df_total[df_total['TIPO'] == 'ENTRADA']
        df_sai = df_total[df_total['TIPO'] == 'SAIDA']

        try:
            with pd.ExcelWriter(ARQUIVO_FINAL, engine='xlsxwriter') as writer:
                wb = writer.book
                ws = wb.add_worksheet("FLUXO DE CAIXA")
                writer.sheets["FLUXO DE CAIXA"] = ws

                fmt_titulo = wb.add_format({'bold': True, 'font_size': 14, 'align': 'center', 'font_color': '#FFFFFF', 'bg_color': C_NAVY})
                fmt_head   = wb.add_format({'bold': True, 'bg_color': C_PRIMARY, 'font_color': 'white', 'border': 1, 'align': 'center'})
                fmt_money  = wb.add_format({'num_format': 'R$ #,##0.00'})
                fmt_date   = wb.add_format({'num_format': 'dd/mm/yyyy', 'align': 'center'})

                ws.merge_range('A1:H1', "ENTRADAS (CRÉDITO)", fmt_titulo)
                ws.merge_range('J1:Q1', "SAÍDAS (DÉBITO)", fmt_titulo)

                cols = ["DATA", "TIPO", "DESCRIÇÃO", "VALOR ", "BANCO", "STATUS", "REFERENCIA", "OBSERVAÇÃO"]
                for i, c in enumerate(cols):
                    ws.write(1, i, c, fmt_head)
                    ws.write(1, i + 9, c, fmt_head)

                for r, row in enumerate(df_ent.values):
                    ws.write_row(r+2, 0, row)
                    ws.write(r+2, 0, row[0], fmt_date)
                    ws.write(r+2, 3, row[3], fmt_money)

                for r, row in enumerate(df_sai.values):
                    ws.write_row(r+2, 9, row)
                    ws.write(r+2, 9, row[0], fmt_date)
                    ws.write(r+2, 12, row[3], fmt_money)

                ws.set_column('A:A', 12); ws.set_column('J:J', 12)
                ws.set_column('C:C', 40); ws.set_column('L:L', 40)
                ws.set_column('G:H', 25); ws.set_column('P:Q', 25)

                if abas_existentes:
                    self.log(f"Restaurando {len(abas_existentes)} abas manuais...", "info")
                    for nome_aba, df_aba in abas_existentes.items():
                        df_aba.to_excel(writer, sheet_name=nome_aba, index=False)

            self.atualizar_barra(100, "Concluído!")
            self.log(f"✅ Arquivo salvo: {os.path.basename(ARQUIVO_FINAL)}", "success")
            self.log(f"   ↳ {len(df_ent)} entradas  |  {len(df_sai)} saídas  |  Total: {len(df_total)} registros", "success")
            self.finalizar(False, f"✅ Consolidação concluída com sucesso!\n\n📊 {len(df_ent)} entradas  |  💸 {len(df_sai)} saídas\n📁 {len(df_total)} registros no total.")

        except PermissionError:
            self.log("ERRO: O arquivo Excel está aberto. Feche-o e tente novamente.", "error")
            self.finalizar(True, "⚠️ O arquivo FLUXO_CAIXA_FERSAN.xlsx está aberto em outro programa.\n\nFeche-o e tente novamente.")
        except Exception as e:
            self.log(f"Erro: {e}", "error")
            self.finalizar(True, str(e))

    def finalizar(self, erro, msg):
        self.btn_processar.config(state=tk.NORMAL, bg=C_PRIMARY, text="▶  INICIAR CONSOLIDAÇÃO")
        if erro:
            messagebox.showerror("Erro", msg)
            self.lbl_progresso.config(text="Erro na consolidação.")
        else:
            messagebox.showinfo("✅ Concluído", msg)
        self.progress['value'] = 0
        self.atualizar_status_pasta()


if __name__ == "__main__":
    root = tk.Tk()
    app = RoboFinanceiroApp(root)
    root.mainloop()