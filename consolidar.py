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

VERSAO_ATUAL = "1.3.1"
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

    log_func("📂 Lendo histórico...")
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

        log_func(f" ↳ {len(df_historico)} registros recuperados.")
        return df_historico
    except Exception as e:
        log_func(f"⚠️ Erro ao ler histórico (Pode ser layout antigo): {e}")
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
        log_func(f"❌ Erro leitura {os.path.basename(caminho)}: {e}")
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
            print(f"Erro ao checar update: {e}")
            return None, None, None

    def realizar_atualizacao(self, download_url, nova_versao, tipo_arquivo):
        try:
            msg_tipo = "completa (inclui novas funções)" if tipo_arquivo == "ZIP" else "rápida"
            resp = messagebox.askyesno(
                "Atualização Disponível", 
                f"A versão {nova_versao} está disponível!\nTipo: Atualização {msg_tipo}.\nDeseja atualizar agora?"
            )
            if not resp: return

            if not getattr(sys, 'frozen', False):
                messagebox.showinfo("Erro", "Atualização só funciona no arquivo compilado (.exe).")
                return

            app_path = sys.executable
            app_dir = os.path.dirname(app_path)
            
            tmp_dir = os.path.join(app_dir, "temp_update")
            if os.path.exists(tmp_dir): shutil.rmtree(tmp_dir)
            os.makedirs(tmp_dir)

            nome_arquivo = f"update.{tipo_arquivo.lower()}"
            caminho_download = os.path.join(tmp_dir, nome_arquivo)
            
            resposta = requests.get(download_url, stream=True)
            with open(caminho_download, 'wb') as f:
                for chunk in resposta.iter_content(chunk_size=4096):
                    f.write(chunk)

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
        self.root.title("Robô Fersan - Consolidador Financeiro")
        self.root.geometry("600x550")
        self.root.configure(bg="#E8E8E8")

        self.processo_dash = None
        self.root.protocol("WM_DELETE_WINDOW", self.ao_fechar) 

        frame_top = tk.Frame(root, bg="#2F75B5", height=60)
        frame_top.pack(fill=tk.X)
        lbl_titulo = tk.Label(frame_top, text="FERSAN FINANCEIRO", font=("Segoe UI", 18, "bold"), bg="#2F75B5", fg="white")
        lbl_titulo.pack(pady=10)

        lbl_info = tk.Label(root, text=f"Pasta de Leitura: .../extratos_bancarios", font=("Segoe UI", 9), bg="#E8E8E8", fg="#555")
        lbl_info.pack(pady=10)

        self.btn_processar = tk.Button(root, text="INICIAR CONSOLIDAÇÃO", font=("Segoe UI", 12, "bold"), 
                                       bg="#4CAF50", fg="white", activebackground="#45a049",
                                       relief=tk.FLAT, height=2, width=30, cursor="hand2",
                                       command=self.iniciar_thread)
        self.btn_processar.pack(pady=5)

        self.btn_dashboard = tk.Button(
            root,
            text="📊 ABRIR DASHBOARD",
            font=("Segoe UI", 11, "bold"),
            bg="#2F75B5",
            fg="white",
            relief=tk.FLAT,
            height=2,
            width=30,
            cursor="hand2",
            command=self.abrir_dashboard
        )
        self.btn_dashboard.pack(pady=5)

        self.lbl_progresso = tk.Label(root, text="Aguardando...", bg="#E8E8E8", font=("Segoe UI", 9))
        self.lbl_progresso.pack(pady=(15, 0))
        
        self.progress = ttk.Progressbar(root, orient="horizontal", length=520, mode="determinate")
        self.progress.pack(pady=5)

        self.log_area = scrolledtext.ScrolledText(root, width=70, height=12, font=("Consolas", 9), state='disabled')
        self.log_area.pack(pady=10, padx=10)
        
        lbl_footer = tk.Label(root, text=f"v{VERSAO_ATUAL} - Novo Layout (8 Colunas)", bg="#E8E8E8", fg="#999")
        lbl_footer.pack(side=tk.BOTTOM, pady=5)

        self.root.after(2000, self.checar_updates_bg)

    def checar_updates_bg(self):
        threading.Thread(target=self._processo_update, daemon=True).start()

    def _processo_update(self):
        updater = AutoUpdater(VERSAO_ATUAL, URL_CHECK_UPDATE, self.root)
        url, nova_versao, tipo = updater.verificar_atualizacao()
        
        if url:
            self.root.after(0, lambda: updater.realizar_atualizacao(url, nova_versao, tipo))

    def abrir_dashboard(self):
        try:
            if self.processo_dash is not None:
                try:
                    self.processo_dash.kill()
                    self.log("🔄 Reiniciando servidor do Dashboard...")
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

            self.log("🚀 Iniciando Dashboard...")
            
            self.processo_dash = subprocess.Popen(
                cmd,
                cwd=cwd,
                shell=False,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )

            url = "http://localhost:8501"
            self.log(f"🔗 Disponível em: {url}")
            self.log("⏳ Abrindo navegador em 3 segundos...")
            self.root.after(3000, lambda: webbrowser.open(url))

        except Exception as e:
            messagebox.showerror("Erro Dash", str(e))
            self.log(f"Erro Dash: {e}")

    def ao_fechar(self):
        if self.processo_dash is not None:
            try:
                self.processo_dash.terminate() 
            except Exception:
                pass 
        self.root.destroy()
        sys.exit()

    def log(self, mensagem):
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, ">> " + mensagem + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')

    def iniciar_thread(self):
        self.btn_processar.config(state=tk.DISABLED, bg="#999999", text="PROCESSANDO...")
        self.progress['value'] = 0
        threading.Thread(target=self.executar_processamento).start()

    def atualizar_barra(self, valor, texto):
        self.progress['value'] = valor
        self.lbl_progresso.config(text=f"{texto} ({int(valor)}%)")
        self.root.update_idletasks()

    def executar_processamento(self):
        self.log("Iniciando motor de processamento...")
        
        if not os.path.exists(PASTA_INPUT):
            os.makedirs(PASTA_INPUT)
            self.log(f"Pasta Criada.")
            self.finalizar(False, "Pasta criada. Adicione arquivos.")
            return

        self.atualizar_barra(5, "Lendo histórico...")
        
        abas_existentes = {}
        if os.path.exists(ARQUIVO_FINAL):
            try:
                todas_abas = pd.read_excel(ARQUIVO_FINAL, sheet_name=None)
                for nome_aba, df_aba in todas_abas.items():
                    if nome_aba != "FLUXO DE CAIXA":
                        abas_existentes[nome_aba] = df_aba
                self.log(f" ℹ️ Abas manuais encontradas: {list(abas_existentes.keys())}")
            except Exception as e:
                self.log(f"Aviso: Não consegui ler outras abas ({e})")

        df_mestre = carregar_dados_existentes(self.log)
        
        arquivos = [os.path.join(PASTA_INPUT, f) for f in os.listdir(PASTA_INPUT) if f.lower().endswith(('.xlsx', '.xls', '.csv'))]
        
        if not arquivos:
            self.log("ERRO: Pasta vazia.")
            self.finalizar(True, "Nenhum arquivo encontrado.")
            return

        self.log(f"Arquivos: {len(arquivos)}")
        novos = []
        total = len(arquivos)
        
        for i, arq in enumerate(arquivos):
            nome = os.path.basename(arq)
            self.atualizar_barra(10 + ((i + 1) / total * 70), f"Lendo: {nome}")
            self.log(f"Lendo: {nome}...")
            temp = processar_arquivo_individual(arq, self.log)
            if not temp.empty: novos.append(temp)

        if not novos and df_mestre.empty:
            self.finalizar(True, "Nenhum dado válido.")
            return

        self.atualizar_barra(85, "Consolidando...")
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
        
        self.log(f"Duplicatas removidas: {qtd_antes - len(df_auto)}")

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
                
                fmt_titulo = wb.add_format({'bold': True, 'font_size': 14, 'align': 'center'})
                fmt_head = wb.add_format({'bold': True, 'bg_color': '#2F75B5', 'font_color': 'white', 'border': 1, 'align': 'center'})
                fmt_money = wb.add_format({'num_format': 'R$ #,##0.00'})
                fmt_date = wb.add_format({'num_format': 'dd/mm/yyyy', 'align': 'center'})

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
                    self.log(f"Restaurando {len(abas_existentes)} abas manuais...")
                    for nome_aba, df_aba in abas_existentes.items():
                        df_aba.to_excel(writer, sheet_name=nome_aba, index=False)

            self.atualizar_barra(100, "Concluído!")
            self.log(f"Arquivo salvo: {os.path.basename(ARQUIVO_FINAL)}")
            self.finalizar(False, "Sucesso!")

        except PermissionError:
            self.log("ERRO: Feche o arquivo Excel!")
            self.finalizar(True, "Excel aberto. Feche-o.")
        except Exception as e:
            self.log(f"Erro: {e}")
            self.finalizar(True, str(e))

    def finalizar(self, erro, msg):
        self.btn_processar.config(state=tk.NORMAL, bg="#4CAF50", text="INICIAR CONSOLIDAÇÃO")
        if erro:
            messagebox.showerror("Erro", msg)
            self.lbl_progresso.config(text="Erro.")
        else:
            messagebox.showinfo("Sucesso", msg)
        self.progress['value'] = 0

if __name__ == "__main__":
    root = tk.Tk()
    app = RoboFinanceiroApp(root)
    root.mainloop()