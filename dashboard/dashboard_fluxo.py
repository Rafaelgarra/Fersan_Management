import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os
import sys

# ======================================================
# CONFIGURAÇÃO INICIAL
# ======================================================
st.set_page_config(
    page_title="Dashboard Financeiro FERSAN",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Lógica de caminhos para funcionar no EXE e no VSCode
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Tenta achar o arquivo em locais diferentes (segurança)
caminhos_tentativa = [
    os.path.join(BASE_DIR, "FLUXO_CAIXA_FERSAN.xlsx"),
    os.path.join(os.getcwd(), "FLUXO_CAIXA_FERSAN.xlsx"),
    os.path.join(BASE_DIR, "..", "FLUXO_CAIXA_FERSAN.xlsx")
]

ARQUIVO_EXCEL = None
for c in caminhos_tentativa:
    if os.path.exists(c):
        ARQUIVO_EXCEL = c
        break

if ARQUIVO_EXCEL is None:
    ARQUIVO_EXCEL = caminhos_tentativa[0] # Padrão para mostrar o erro

ABA_EXCEL = "FLUXO DE CAIXA"

# ======================================================
# FUNÇÃO DE CARGA
# ======================================================
@st.cache_data
def carregar_dados():
    df_raw = None 

    if not os.path.exists(ARQUIVO_EXCEL):
        st.error(f"❌ Arquivo não encontrado: {ARQUIVO_EXCEL}")
        st.stop()

    try:
        df_raw = pd.read_excel(
            ARQUIVO_EXCEL,
            sheet_name=ABA_EXCEL,
            header=1
        )
    except Exception as e:
        st.error(f"Erro ao ler Excel: {e}")
        st.stop()

    # --- CORREÇÃO AQUI: LER 8 COLUNAS (0 a 8 e 9 a 17) ---
    try:
        # Tenta ler com o layout novo (8 colunas)
        df_ent = df_raw.iloc[:, 0:8].copy()
        df_sai = df_raw.iloc[:, 9:17].copy()
        
        # Lista com 8 nomes
        colunas_padrao = ["DATA", "TIPO", "DESCRIÇÃO", "VALOR", "BANCO", "STATUS", "REFERENCIA", "OBSERVAÇÃO"]
        df_ent.columns = colunas_padrao
        df_sai.columns = colunas_padrao

    except Exception:
        # Se der erro (arquivo antigo com 7 colunas), usa o fallback
        df_ent = df_raw.iloc[:, 0:7].copy()
        df_sai = df_raw.iloc[:, 9:16].copy()
        colunas_antigas = ["DATA", "TIPO", "DESCRIÇÃO", "VALOR", "BANCO", "STATUS", "REFERENCIA"]
        df_ent.columns = colunas_antigas
        df_sai.columns = colunas_antigas
        # Cria a coluna que falta vazia
        df_ent["OBSERVAÇÃO"] = ""
        df_sai["OBSERVAÇÃO"] = ""

    # 4. JUNTA AS DUAS EM UMA SÓ
    df = pd.concat([df_ent, df_sai], ignore_index=True)

    # 5. LIMPEZA
    df = df.dropna(subset=['DATA'])
    
    # Converte tipos
    df['DATA'] = pd.to_datetime(df['DATA'], errors='coerce')
    df['VALOR'] = pd.to_numeric(df['VALOR'], errors='coerce').fillna(0)
    
    # Remove datas inválidas que sobraram
    df = df.dropna(subset=['DATA'])

    # Colunas auxiliares
    df['ANO'] = df['DATA'].dt.year
    df['MES'] = df['DATA'].dt.month
    df['DIA'] = df['DATA'].dt.day
    df['TIPO'] = df['TIPO'].astype(str).str.upper().str.strip()

    return df


# ======================================================
# INTERFACE PRINCIPAL
# ======================================================
st.title("📊 Dashboard Financeiro – FERSAN")
st.caption(f"Lendo de: {ARQUIVO_EXCEL}")

df = carregar_dados()

# ======================================================
# SIDEBAR - FILTROS
# ======================================================
st.sidebar.header("⚙️ Configurações")

if st.sidebar.button("🔄 Atualizar Dados"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.header("🔎 Filtros")

if not df.empty:
    anos = sorted(df['ANO'].unique())
    meses = sorted(df['MES'].unique())

    # Seleção de Ano
    ano_sel = st.sidebar.selectbox("Ano", anos, index=len(anos)-1)
    
    # Seleção de Mês
    mes_sel = st.sidebar.selectbox("Mês", meses, index=len(meses)-1)
    
    # Seleção de Dia
    dias_disponiveis = sorted(df[(df['ANO'] == ano_sel) & (df['MES'] == mes_sel)]['DIA'].unique().tolist())
    dia_sel = st.sidebar.selectbox("Dia", ["Todos"] + dias_disponiveis)

    # ======================================================
    # APLICA FILTROS
    # ======================================================
    df_f = df[(df['ANO'] == ano_sel) & (df['MES'] == mes_sel)]

    if dia_sel != "Todos":
        df_f = df_f[df_f['DIA'] == dia_sel]

    # ======================================================
    # KPIs
    # ======================================================
    entradas = df_f[df_f['TIPO'] == 'ENTRADA']['VALOR'].sum()
    saidas   = df_f[df_f['TIPO'] == 'SAIDA']['VALOR'].sum()
    saldo    = entradas - saidas

    c1, c2, c3 = st.columns(3)

    c1.metric("💰 Total de Entradas", f"R$ {entradas:,.2f}")
    c2.metric("💸 Total de Saídas",   f"R$ {saidas:,.2f}")
    c3.metric("📊 Saldo do Período",  f"R$ {saldo:,.2f}", delta_color="normal")

    st.divider()

    # ======================================================
    # GRÁFICOS
    # ======================================================
    if not df_f.empty:
        # 1. Barras
        df_graf = df_f.groupby(['DATA', 'TIPO'])['VALOR'].sum().reset_index()

        fig_bar = px.bar(
            df_graf, x="DATA", y="VALOR", color="TIPO",
            title="Entradas x Saídas (Diário)", barmode="group", text_auto='.2s',
            color_discrete_map={'ENTRADA': '#00CC96', 'SAIDA': '#EF553B'}
        )
        st.plotly_chart(fig_bar, use_container_width=True)

        # 2. Linha (Saldo Acumulado)
        df_saldo = df_f.sort_values('DATA').copy()
        df_saldo['MOV'] = df_saldo.apply(lambda r: r['VALOR'] if r['TIPO'] == 'ENTRADA' else -r['VALOR'], axis=1)
        df_saldo['SALDO_ACUMULADO'] = df_saldo['MOV'].cumsum()

        fig_saldo = px.line(
            df_saldo, x="DATA", y="SALDO_ACUMULADO",
            title="Evolução do Saldo (Acumulado no Período)", markers=True
        )
        fig_saldo.update_traces(line_color='#636EFA')
        st.plotly_chart(fig_saldo, use_container_width=True)

        # ======================================================
        # TABELA DETALHADA (ATUALIZADA)
        # ======================================================
        st.subheader("📄 Detalhamento dos Lançamentos")
        
        # Adicionei REFERENCIA e OBSERVAÇÃO na visualização
        colunas_visualizacao = ['DATA', 'TIPO', 'DESCRIÇÃO', 'VALOR', 'BANCO', 'STATUS', 'REFERENCIA', 'OBSERVAÇÃO']
        
        # Filtra apenas colunas que realmente existem no dataframe (segurança)
        cols_finais = [c for c in colunas_visualizacao if c in df_f.columns]
        
        df_display = df_f[cols_finais].sort_values('DATA')
        
        st.dataframe(
            df_display.style.format({"VALOR": "R$ {:,.2f}"}),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.warning("Nenhum dado encontrado para o período selecionado.")

else:
    st.warning("O arquivo Excel parece estar vazio ou sem dados válidos.")