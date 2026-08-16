import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
import sys
import io

# ======================================================
# CONFIGURAÇÃO INICIAL DA PÁGINA
# ======================================================
st.set_page_config(
    page_title="Fersan Management – Portal Financeiro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ======================================================
# DESIGN SYSTEM – CSS INJETADO (Enterprise Fintech)
# ======================================================
st.markdown("""
<style>
/* ── Tipografia Corporativa ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}

/* ── Canvas Principal (Fundo Escuro Corporativo) ── */
.stApp {
    background-color: #0E1117 !important;
}
.main .block-container {
    background-color: #0E1117 !important;
    padding-top: 1.8rem;
    padding-bottom: 3rem;
    padding-left: 2.5rem;
    padding-right: 2.5rem;
    max-width: 1560px;
}

/* ── Sidebar (Dark Navy Shell) ── */
[data-testid="stSidebar"] {
    background-color: #031126 !important;
    border-right: 1px solid #071B36 !important;
    min-width: 260px !important;
    max-width: 300px !important;
}
[data-testid="stSidebar"] * {
    color: #CBD5E1 !important;
}
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
    color: #F8FAFC !important;
}

/* ── Menu Navegação Sidebar ── */
.sidebar-section-label {
    font-size: 10px;
    font-weight: 700;
    color: #64748B !important;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin: 20px 0 8px 6px;
}
[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label {
    background-color: transparent !important;
    color: #CBD5E1 !important;
    font-weight: 500 !important;
    font-size: 13.5px !important;
    padding: 8px 12px !important;
    border-radius: 8px !important;
    margin-bottom: 2px !important;
    transition: all 0.15s ease;
}
[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label:hover {
    background-color: #0B2447 !important;
    color: #F8FAFC !important;
}
[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label[data-baseweb="radio"] > div:first-child {
    display: none;
}
[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label:has(input:checked) {
    background: rgba(37, 99, 235, 0.22) !important;
    color: #FFFFFF !important;
    border-left: 3px solid #38BDF8 !important;
    border-radius: 4px 8px 8px 4px !important;
}
[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label:has(input:checked) * {
    color: #FFFFFF !important;
    font-weight: 600 !important;
}

/* ── Cabeçalho do Canvas ── */
.page-header {
    margin-bottom: 24px;
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    flex-wrap: wrap;
    gap: 16px;
    border-bottom: 1px solid #1E293B;
    padding-bottom: 16px;
}
.page-title {
    font-size: 26px;
    font-weight: 800;
    color: #F8FAFC;
    margin: 0;
    padding: 0;
    letter-spacing: -0.02em;
}
.page-meta {
    font-size: 13px;
    color: #94A3B8;
    margin-top: 6px;
    display: flex;
    align-items: center;
    gap: 12px;
}
.badge-source {
    background: #1E293B;
    color: #94A3B8;
    padding: 3px 8px;
    border-radius: 6px;
    font-weight: 500;
    font-size: 11px;
    border: 1px solid #334155;
}

/* ── Títulos de Seção no Canvas (Alto Contraste) ── */
.canvas-section-title {
    font-size: 15px;
    font-weight: 700;
    color: #F8FAFC;
    margin: 24px 0 12px 0;
    letter-spacing: -0.01em;
    display: flex;
    align-items: center;
    gap: 8px;
}

/* ── Cards de KPI (Superfície Branca Neutra + Semântica) ── */
.kpi-card {
    background: #FFFFFF;
    border-radius: 12px;
    padding: 20px 22px;
    border: 1px solid #E2E8F0;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.kpi-card:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}
.kpi-card-hero-pos {
    border-left: 4px solid #22C55E !important;
}
.kpi-card-hero-neg {
    border-left: 4px solid #EF4444 !important;
}
.kpi-card-rec {
    border-left: 4px solid #22C55E !important;
}
.kpi-card-desp {
    border-left: 4px solid #EF4444 !important;
}
.kpi-card-trans {
    border-left: 4px solid #2563EB !important;
}

.kpi-header-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
}
.kpi-label {
    font-size: 11px;
    font-weight: 700;
    color: #64748B;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.kpi-badge {
    font-size: 10px;
    font-weight: 600;
    padding: 2px 6px;
    border-radius: 4px;
}
.kpi-badge-green { background: #DCFCE7; color: #16A34A; }
.kpi-badge-red   { background: #FEE2E2; color: #DC2626; }
.kpi-badge-blue  { background: #DBEAFE; color: #1D4ED8; }

.kpi-value {
    font-size: 26px;
    font-weight: 800;
    line-height: 1.15;
    letter-spacing: -0.02em;
    margin-bottom: 6px;
}
.val-green { color: #16A34A; }
.val-red   { color: #DC2626; }
.val-blue  { color: #1D4ED8; }
.val-dark  { color: #0F172A; }

.kpi-subtext {
    font-size: 12px;
    color: #64748B;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 4px;
}

/* ── Container de Gráficos (Branco Neutro) ── */
.chart-card {
    background: #FFFFFF;
    border-radius: 12px;
    border: 1px solid #E2E8F0;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    padding: 16px 20px 12px 20px;
    margin-bottom: 16px;
}
.chart-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
}
.chart-title {
    font-size: 14px;
    font-weight: 700;
    color: #0F172A;
}
.chart-desc {
    font-size: 12px;
    color: #64748B;
    font-weight: 400;
}

/* ── Resumo por Banco Componente ── */
.bank-row {
    padding: 12px 0;
    border-bottom: 1px solid #F1F5F9;
}
.bank-row:last-child {
    border-bottom: none;
    padding-bottom: 4px;
}
.bank-meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6px;
}
.bank-name {
    font-size: 13px;
    font-weight: 700;
    color: #0F172A;
    display: flex;
    align-items: center;
    gap: 6px;
}
.bank-val-box {
    text-align: right;
}
.bank-value {
    font-size: 13px;
    font-weight: 700;
    color: #0F172A;
}
.bank-pct {
    font-size: 11px;
    font-weight: 500;
    color: #64748B;
    margin-left: 6px;
}
.progress-track {
    background-color: #F1F5F9;
    border-radius: 6px;
    height: 7px;
    width: 100%;
    overflow: hidden;
}
.progress-bar-fill {
    background: linear-gradient(90deg, #2563EB, #0EA5E9);
    height: 100%;
    border-radius: 6px;
}

/* ── Tabela Estilo Corporativo (Fundo Claro de Card) ── */
[data-testid="stDataFrame"] {
    border: 1px solid #E2E8F0 !important;
    border-radius: 12px !important;
    background: #FFFFFF !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;
}
</style>
""", unsafe_allow_html=True)

# ======================================================
# UTILITÁRIOS DE FORMATAÇÃO (BRL / pt-BR)
# ======================================================
def format_brl(valor: float) -> str:
    """Formata valor monetário com padrão brasileiro R$ 0.000,00"""
    if pd.isna(valor):
        return "R$ 0,00"
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def format_int(valor: int) -> str:
    """Formata número inteiro com separador de milhar pt-BR"""
    if pd.isna(valor):
        return "0"
    return f"{int(valor):,}".replace(",", ".")

# ======================================================
# RESOLUÇÃO DE CAMINHOS DO ARQUIVO EXCEL
# ======================================================
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

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
    ARQUIVO_EXCEL = caminhos_tentativa[0]

ABA_EXCEL = "FLUXO DE CAIXA"

# ======================================================
# FUNÇÃO DE CARGA E NORMALIZAÇÃO DE DADOS
# ======================================================
@st.cache_data
def carregar_dados():
    if not os.path.exists(ARQUIVO_EXCEL):
        return None, f"Arquivo não encontrado: {ARQUIVO_EXCEL}"

    try:
        df_raw = pd.read_excel(ARQUIVO_EXCEL, sheet_name=ABA_EXCEL, header=1)
    except Exception as e:
        return None, f"Erro ao abrir planilha Excel: {e}"

    try:
        df_ent = df_raw.iloc[:, 0:8].copy()
        df_sai = df_raw.iloc[:, 9:17].copy()
        colunas_padrao = ["DATA", "TIPO", "DESCRIÇÃO", "VALOR", "BANCO", "STATUS", "REFERENCIA", "OBSERVAÇÃO"]
        df_ent.columns = colunas_padrao
        df_sai.columns = colunas_padrao
    except Exception:
        try:
            df_ent = df_raw.iloc[:, 0:7].copy()
            df_sai = df_raw.iloc[:, 9:16].copy()
            colunas_antigas = ["DATA", "TIPO", "DESCRIÇÃO", "VALOR", "BANCO", "STATUS", "REFERENCIA"]
            df_ent.columns = colunas_antigas
            df_sai.columns = colunas_antigas
            df_ent["OBSERVAÇÃO"] = ""
            df_sai["OBSERVAÇÃO"] = ""
        except Exception as e:
            return None, f"Layout de colunas incompatível: {e}"

    df = pd.concat([df_ent, df_sai], ignore_index=True)
    df = df.dropna(subset=['DATA'])
    df['DATA']  = pd.to_datetime(df['DATA'], errors='coerce')
    df['VALOR'] = pd.to_numeric(df['VALOR'], errors='coerce').fillna(0)
    df = df.dropna(subset=['DATA'])
    df['ANO']  = df['DATA'].dt.year
    df['MES']  = df['DATA'].dt.month
    df['DIA']  = df['DATA'].dt.day
    df['TIPO'] = df['TIPO'].astype(str).str.upper().str.strip()
    df['BANCO'] = df['BANCO'].fillna("Não Informado").astype(str).str.strip()

    return df, None

df, erro_carga = carregar_dados()

# ======================================================
# SIDEBAR - DARK NAVY CORPORATE SHELL
# ======================================================
with st.sidebar:
    st.markdown("""
    <div style='padding: 12px 0 20px 0; border-bottom: 1px solid #071B36; margin-bottom: 16px;'>
        <div style='display: flex; align-items: center; gap: 12px;'>
            <div style='width: 36px; height: 36px; background: linear-gradient(135deg, #2563EB, #0EA5E9); border-radius: 8px; display: flex; align-items: center; justify-content: center; font-weight: 800; color: white; font-size: 20px; box-shadow: 0 2px 6px rgba(37,99,235,0.4);'>
                F
            </div>
            <div>
                <div style='font-size: 17px; font-weight: 800; color: #FFFFFF; line-height: 1.1;'>Fersan<span style='color: #38BDF8;'>_Management</span></div>
                <div style='font-size: 8px; font-weight: 700; color: #64748B; margin-top: 4px; letter-spacing: 0.12em;'>
                    FINANCIAL INTELLIGENCE
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div class='sidebar-section-label'>Navegação Principal</div>", unsafe_allow_html=True)
    
    opcoes_menu = [
        "Dashboard",
        "Lançamentos",
        "Contas Bancárias",
        "Extratos",
        "Conciliação",
        "Fluxo de Caixa",
        "Contas a Pagar",
        "Contas a Receber",
        "Relatórios",
        "Configurações"
    ]
    secao = st.radio("Menu", opcoes_menu, label_visibility="collapsed")
    
    st.markdown("<div class='sidebar-section-label'>Filtros Globais</div>", unsafe_allow_html=True)
    
    if df is not None and not df.empty:
        anos = sorted(df['ANO'].unique())
        meses_num = sorted(df['MES'].unique())
        nomes_meses = {1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"}
        
        ano_sel = st.selectbox("Ano de Referência", anos, index=len(anos)-1)
        mes_nome = st.selectbox("Mês de Referência", [nomes_meses[m] for m in meses_num], index=len(meses_num)-1)
        mes_sel = [k for k, v in nomes_meses.items() if v == mes_nome][0]
    else:
        ano_sel = 2025
        mes_sel = 12
        mes_nome = "Dezembro"

    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
    if st.button("🔄 Sincronizar Dados", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown("""
    <div style='margin-top: 30px; padding: 12px; background: #071B36; border-radius: 8px; font-size: 11px; color: #64748B;'>
        <div style='color: #22C55E; font-weight: 600; margin-bottom: 2px;'>✓ Sistema Conectado</div>
        Base: FLUXO_CAIXA_FERSAN.xlsx
    </div>
    """, unsafe_allow_html=True)

# ======================================================
# TRATAMENTO DE ERROS OU EMPTY STATE
# ======================================================
if erro_carga:
    st.error(f"❌ {erro_carga}")
    st.info("Verifique se a planilha 'FLUXO_CAIXA_FERSAN.xlsx' está na pasta e contém a aba 'FLUXO DE CAIXA'.")
    st.stop()

if df is None or df.empty:
    st.warning("⚠️ Nenhum dado encontrado na planilha.")
    st.stop()

# ======================================================
# FILTRAGEM DO DATASET
# ======================================================
df_f = df[(df['ANO'] == ano_sel) & (df['MES'] == mes_sel)]

entradas = df_f[df_f['TIPO'] == 'ENTRADA']['VALOR'].sum()
saidas   = df_f[df_f['TIPO'] == 'SAIDA']['VALOR'].sum()
saldo    = entradas - saidas
qtd_ops  = len(df_f)
ticket_medio = (entradas + saidas) / qtd_ops if qtd_ops > 0 else 0
periodo_str = f"{mes_nome}/{ano_sel}"
data_atualizacao = datetime.now().strftime("%H:%M")

# ======================================================
# CABEÇALHO DO DASHBOARD
# ======================================================
st.markdown(f"""
<div class="page-header">
    <div>
        <h1 class="page-title">Dashboard Financeiro</h1>
        <div class="page-meta">
            <span>Período: <strong style="color: #F8FAFC;">{periodo_str}</strong></span>
            <span>•</span>
            <span>{format_int(qtd_ops)} lançamentos</span>
            <span>•</span>
            <span>Atualizado às {data_atualizacao}</span>
            <span>•</span>
            <span class="badge-source">FLUXO_CAIXA_FERSAN.xlsx</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ======================================================
# TELA: DASHBOARD
# ======================================================
if secao == "Dashboard":

    # ── 1. KPI CARDS (Hierarquia Clara + Superfície Branca) ──
    c1, c2, c3, c4 = st.columns(4)
    
    saldo_class = "val-green" if saldo >= 0 else "val-red"
    hero_border = "kpi-card-hero-pos" if saldo >= 0 else "kpi-card-hero-neg"
    saldo_badge = "kpi-badge-green" if saldo >= 0 else "kpi-badge-red"
    saldo_badge_text = "Positivo" if saldo >= 0 else "Déficit"

    with c1:
        st.markdown(f"""
        <div class="kpi-card {hero_border}">
            <div class="kpi-header-row">
                <div class="kpi-label">Saldo do Período</div>
                <div class="kpi-badge {saldo_badge}">{saldo_badge_text}</div>
            </div>
            <div class="kpi-value {saldo_class}">{format_brl(saldo)}</div>
            <div class="kpi-subtext">Resultado líquido consolidado</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="kpi-card kpi-card-rec">
            <div class="kpi-header-row">
                <div class="kpi-label">Total de Receitas</div>
                <div class="kpi-badge kpi-badge-green">Entradas</div>
            </div>
            <div class="kpi-value val-green">{format_brl(entradas)}</div>
            <div class="kpi-subtext">Créditos registrados no mês</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="kpi-card kpi-card-desp">
            <div class="kpi-header-row">
                <div class="kpi-label">Total de Despesas</div>
                <div class="kpi-badge kpi-badge-red">Saídas</div>
            </div>
            <div class="kpi-value val-red">{format_brl(saidas)}</div>
            <div class="kpi-subtext">Débitos operacionais no mês</div>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        st.markdown(f"""
        <div class="kpi-card kpi-card-trans">
            <div class="kpi-header-row">
                <div class="kpi-label">Volume de Transações</div>
                <div class="kpi-badge kpi-badge-blue">{format_int(qtd_ops)} ops</div>
            </div>
            <div class="kpi-value val-dark">{format_int(qtd_ops)}</div>
            <div class="kpi-subtext">Ticket Médio: {format_brl(ticket_medio)}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    if not df_f.empty:
        # ── 2. GRÁFICO PRINCIPAL: FLUXO DE CAIXA DIÁRIO ──
        st.markdown("<div class='canvas-section-title'>📊 Fluxo de Caixa Diário</div>", unsafe_allow_html=True)
        
        df_graf = df_f.groupby(['DATA', 'TIPO'])['VALOR'].sum().reset_index()
        fig_bar = go.Figure()
        
        ent_data = df_graf[df_graf['TIPO'] == 'ENTRADA']
        sai_data = df_graf[df_graf['TIPO'] == 'SAIDA']
        
        if not ent_data.empty:
            fig_bar.add_trace(go.Bar(
                x=ent_data['DATA'], y=ent_data['VALOR'],
                name='Receitas', marker_color='#22C55E',
                hovertemplate='<b>%{x|%d/%m/%Y}</b><br>Receitas: <b>R$ %{y:,.2f}</b><extra></extra>'
            ))
        if not sai_data.empty:
            fig_bar.add_trace(go.Bar(
                x=sai_data['DATA'], y=sai_data['VALOR'],
                name='Despesas', marker_color='#EF4444',
                hovertemplate='<b>%{x|%d/%m/%Y}</b><br>Despesas: <b>R$ %{y:,.2f}</b><extra></extra>'
            ))
            
        fig_bar.update_layout(
            barmode='group',
            plot_bgcolor='#FFFFFF',
            paper_bgcolor='#FFFFFF',
            margin=dict(l=85, r=20, t=25, b=40),  # Margem l=85 elimina clipping no eixo Y!
            font=dict(family='Inter', color='#64748B', size=11),
            legend=dict(orientation='h', yanchor='bottom', y=1.04, xanchor='right', x=1),
            xaxis=dict(showgrid=False, tickformat='%d/%m', linecolor='#E2E8F0'),
            yaxis=dict(showgrid=True, gridcolor='#F1F5F9', tickformat=',.0f', tickprefix='R$ ', linecolor='#E2E8F0'),
            height=320
        )
        st.plotly_chart(fig_bar, use_container_width=True, theme=None, config={'displayModeBar': False, 'responsive': True})

        # ── 3. SEGUNDA LINHA: EVOLUÇÃO DO SALDO + DISTRIBUIÇÃO POR BANCO ──
        col_line, col_bank = st.columns([1.8, 1.2])
        
        with col_line:
            st.markdown("<div class='canvas-section-title'>📈 Evolução do Saldo Acumulado</div>", unsafe_allow_html=True)
            
            # Agrupar movimentações líquidas por dia para construir a evolução contínua correta
            df_dia = df_f.groupby(df_f['DATA'].dt.normalize()).apply(
                lambda g: g[g['TIPO'] == 'ENTRADA']['VALOR'].sum() - g[g['TIPO'] == 'SAIDA']['VALOR'].sum(),
                include_groups=False
            ).reset_index(name='MOV_LIQUIDA')
            df_dia.columns = ['DATA', 'MOV_LIQUIDA']
            df_dia = df_dia.sort_values('DATA')
            df_dia['SALDO_ACUMULADO'] = df_dia['MOV_LIQUIDA'].cumsum()
            
            fig_line = go.Figure()
            fig_line.add_trace(go.Scatter(
                x=df_dia['DATA'], y=df_dia['SALDO_ACUMULADO'],
                fill='tozeroy', fillcolor='rgba(37, 99, 235, 0.08)',
                line=dict(color='#2563EB', width=2),
                mode='lines+markers',
                marker=dict(size=4, color='#2563EB'),
                name='Saldo Acumulado',
                hovertemplate='<b>%{x|%d/%m/%Y}</b><br>Saldo Acumulado: <b>R$ %{y:,.2f}</b><extra></extra>'
            ))
            fig_line.update_layout(
                plot_bgcolor='#FFFFFF',
                paper_bgcolor='#FFFFFF',
                margin=dict(l=85, r=20, t=25, b=40),  # Margem l=85 elimina clipping!
                font=dict(family='Inter', color='#64748B', size=11),
                xaxis=dict(showgrid=False, tickformat='%d/%m', linecolor='#E2E8F0'),
                yaxis=dict(
                    showgrid=True,
                    gridcolor='#E2E8F0',
                    zeroline=True,
                    zerolinecolor='#64748B',
                    zerolinewidth=1.2,
                    tickformat=',.0f',
                    tickprefix='R$ ',
                    linecolor='#E2E8F0'
                ),
                height=300
            )
            st.plotly_chart(fig_line, use_container_width=True, theme=None, config={'displayModeBar': False, 'responsive': True})
            
        with col_bank:
            st.markdown("<div class='canvas-section-title'>🏦 Distribuição por Banco</div>", unsafe_allow_html=True)
            
            df_banco = df_f.groupby('BANCO')['VALOR'].sum().reset_index().sort_values('VALOR', ascending=False)
            total_bancos = df_banco['VALOR'].sum() if not df_banco.empty else 1
            
            # Regra dinâmica: Se houver apenas 1 categoria, não exibir anel monocromático vazio
            if len(df_banco) == 1:
                b_row = df_banco.iloc[0]
                st.markdown(f"""
                <div class="chart-card" style="height: 300px; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center;">
                    <div style="font-size: 38px; margin-bottom: 12px;">🏛️</div>
                    <div style="font-size: 18px; font-weight: 800; color: #0F172A;">{b_row['BANCO']}</div>
                    <div style="font-size: 22px; font-weight: 800; color: #2563EB; margin: 6px 0;">{format_brl(b_row['VALOR'])}</div>
                    <div style="font-size: 12px; font-weight: 600; color: #64748B; background: #EFF6FF; padding: 4px 10px; border-radius: 6px;">
                        100% da movimentação do período
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                cores_azul = ['#0B2447', '#2563EB', '#0EA5E9', '#38BDF8', '#93C5FD', '#BFDBFE']
                fig_donut = go.Figure(go.Pie(
                    labels=df_banco['BANCO'], values=df_banco['VALOR'],
                    hole=0.62, marker=dict(colors=cores_azul[:len(df_banco)]),
                    textinfo='percent', textfont=dict(size=11),
                    hovertemplate='<b>%{label}</b><br>Volume: <b>R$ %{value:,.2f}</b><br>Participação: <b>%{percent}</b><extra></extra>'
                ))
                fig_donut.update_layout(
                    plot_bgcolor='#FFFFFF',
                    paper_bgcolor='#FFFFFF',
                    margin=dict(l=10, r=10, t=10, b=10),
                    height=300,
                    showlegend=True,
                    font=dict(family='Inter', color='#64748B', size=11),
                    legend=dict(yanchor="middle", y=0.5, xanchor="left", x=1.0)
                )
                st.plotly_chart(fig_donut, use_container_width=True, theme=None, config={'displayModeBar': False, 'responsive': True})

        # ── 4. RESUMO CONSOLIDADO POR INSTITUIÇÃO (Card Branco Monolítico) ──
        st.markdown("<div class='canvas-section-title'>📑 Resumo Consolidado por Instituição</div>", unsafe_allow_html=True)
        
        # Gerar todas as linhas do banco dentro de um único card branco com hierarquia estrita
        linhas_bancos_html = ""
        for idx, row in df_banco.iterrows():
            banco_nome = row['BANCO']
            valor = row['VALOR']
            percent_total = (valor / total_bancos) * 100
            margin_bottom = "18px" if idx < len(df_banco) - 1 else "4px"
            
            linhas_bancos_html += (
                f'<div style="margin-bottom: {margin_bottom};">'
                f'<div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 2px;">'
                f'<span style="font-size: 13px; font-weight: 700; color: #172033;">🏦 {banco_nome}</span>'
                f'<span style="font-size: 14px; font-weight: 700; color: #2563EB;">{format_brl(valor)}</span>'
                f'</div>'
                f'<div style="display: flex; justify-content: flex-end; margin-bottom: 6px;">'
                f'<span style="font-size: 12px; font-weight: 500; color: #64748B;">{percent_total:.1f}%</span>'
                f'</div>'
                f'<div style="height: 6px; background: #E2E8F0; border-radius: 999px; overflow: hidden; width: 100%;">'
                f'<div style="width: {percent_total}%; height: 100%; background: #2563EB; border-radius: 999px;"></div>'
                f'</div>'
                f'</div>'
            )
            
        card_resumo_html = f'<div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 20px 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); margin-bottom: 20px;">{linhas_bancos_html}</div>'
        st.markdown(card_resumo_html, unsafe_allow_html=True)

# ======================================================
# TELA: LANÇAMENTOS
# ======================================================
elif secao == "Lançamentos":
    st.markdown("<div class='canvas-section-title'>📋 Transações Detalhadas do Período</div>", unsafe_allow_html=True)
    
    colunas_visualizacao = ['DATA', 'TIPO', 'DESCRIÇÃO', 'VALOR', 'BANCO', 'STATUS', 'REFERENCIA', 'OBSERVAÇÃO']
    cols_finais = [c for c in colunas_visualizacao if c in df_f.columns]
    
    df_tabela = df_f[cols_finais].sort_values('DATA', ascending=False).copy()
    
    # Barra de busca e filtros rápidos
    col_s1, col_s2 = st.columns([3, 1])
    with col_s1:
        busca = st.text_input("🔍 Buscar por descrição ou referência", "", placeholder="Ex: PIX, Fornecedor...")
    with col_s2:
        tipo_filtro = st.selectbox("Filtrar Tipo", ["Todos", "ENTRADA", "SAIDA"])
        
    if busca:
        df_tabela = df_tabela[
            df_tabela['DESCRIÇÃO'].astype(str).str.contains(busca, case=False, na=False) |
            df_tabela['REFERENCIA'].astype(str).str.contains(busca, case=False, na=False)
        ]
    if tipo_filtro != "Todos":
        df_tabela = df_tabela[df_tabela['TIPO'] == tipo_filtro]

    # Estilização das cores da palavra por Tipo (Entrada: Verde, Saída: Vermelho) e formatação pt-BR
    def style_tipo(val):
        v = str(val).upper().strip()
        if 'ENTRADA' in v:
            return 'color: #16A34A; font-weight: 700;'
        elif 'SAIDA' in v:
            return 'color: #DC2626; font-weight: 700;'
        return ''

    styler = df_tabela.style
    map_fn = getattr(styler, 'map', None) or getattr(styler, 'applymap')
    styled_df = map_fn(style_tipo, subset=['TIPO'])
    
    format_dict = {}
    if 'VALOR' in df_tabela.columns:
        format_dict['VALOR'] = lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    if 'DATA' in df_tabela.columns:
        format_dict['DATA'] = lambda x: x.strftime('%d/%m/%Y') if pd.notnull(x) else ""
        
    styled_df = styled_df.format(format_dict)

    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True,
        height=750
    )
    
    csv_buffer = io.StringIO()
    df_tabela.to_csv(csv_buffer, index=False, sep=';', decimal=',')
    st.download_button(
        label="📥 Exportar Transações Filtradas (CSV)",
        data=csv_buffer.getvalue().encode('utf-8-sig'),
        file_name=f"transacoes_{ano_sel}_{mes_sel}.csv",
        mime="text/csv",
        use_container_width=False
    )
else:
    st.markdown(f"<div class='canvas-section-title'>⚙️ {secao}</div>", unsafe_allow_html=True)
    st.info(f"O módulo **'{secao}'** está em desenvolvimento e estará disponível na próxima release.")
