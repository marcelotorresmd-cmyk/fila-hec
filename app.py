# -*- coding: utf-8 -*-
"""
Portal de Visualização da Posição da Fila — Hospital Estadual Central
Visual: padrão Fundação Inova Capixaba (logo PNG original — nunca regenerar)
Base: Google Sheets "Fila HEC" + "Cadastro"
"""

import hashlib
import html
import time
from datetime import datetime

import bcrypt
import pandas as pd
import streamlit as st

# ================================================================
# CONFIGURAÇÃO
# ================================================================
st.set_page_config(
    page_title="Fila de Espera — HEC",
    page_icon="🏥",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# IDs das planilhas (devem estar com "Qualquer pessoa com o link: Leitor")
SHEET_FILA_ID = st.secrets.get("SHEET_FILA_ID", "1d1X3vGQGdRA5Wpg3cnfKIYSXRiE6VC1XoCTn1XBcTj0")
SHEET_CADASTRO_ID = st.secrets.get("SHEET_CADASTRO_ID", "1FRvVEvL4S3oCJJKA2OzrKnSOqiphRjZy-lq4cv65EXY")
ABA_FILA = "Página1"
ABA_CADASTRO = "Cadastro"

COLUNAS_FILA = [
    "ID_Registro", "Data_Cadastro_AIH", "Nome_Paciente", "Cartao_SUS", "CPF",
    "Data_Nascimento", "Especialidade", "Numero_AIH", "CID",
    "Status_Exames_Lab", "Status_Exames_Imagem", "Status_Avaliacao_Cardio",
    "Status_Avaliacao_PreAnestesica", "Escore_Prioridade",
]

# ================================================================
# VISUAL — PADRÃO INOVA (azul #344a80 / rosa #ec6a88 / gradiente magenta)
# ================================================================
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800&family=Poppins:wght@400;500;600&display=swap');
        html, body, .stApp, .stButton>button, h1, h2, h3, h4 {
            font-family: 'Poppins', sans-serif !important;
        }
        h1, h2, h3 { font-family: 'Montserrat', sans-serif !important; }

        .stApp {
            background: linear-gradient(180deg, #ffffff 0%, #f8f9fa 100%) !important;
            color: #263238 !important;
        }

        .stButton>button {
            background-color: #344a80 !important;
            color: #ffffff !important;
            border-radius: 8px !important;
            border: none !important;
            font-weight: 700 !important;
            font-size: 1rem !important;
            padding: 0.6rem 1.4rem !important;
            box-shadow: 0 4px 12px rgba(52, 74, 128, 0.25) !important;
            transition: all 0.2s ease-in-out;
            width: 100%;
        }
        .stButton>button:hover {
            background-color: #ec6a88 !important;
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(236, 106, 136, 0.4) !important;
        }

        .btn-gestor>button {
            background-color: transparent !important;
            color: #344a80 !important;
            border: 1px solid #344a80 !important;
            border-radius: 20px !important;
            padding: 0.3rem 1rem !important;
            font-size: 0.85rem !important;
            font-weight: 600 !important;
            box-shadow: none !important;
        }
        .btn-gestor>button:hover {
            background-color: #ec6a88 !important;
            color: #ffffff !important;
            border-color: #ec6a88 !important;
        }

        .glass-card {
            background: #ffffff;
            padding: 35px;
            border-radius: 16px;
            border: 1px solid #f0f0f0;
            box-shadow: 0 8px 28px rgba(35, 50, 86, 0.10);
            margin-bottom: 20px;
        }

        .highlight-queue {
            text-align: center;
            background: #ffffff;
            border-radius: 20px;
            padding: 40px 20px;
            border-top: 6px solid #ec6a88;
            border-bottom: 6px solid #344a80;
            box-shadow: 0 10px 30px rgba(35, 50, 86, 0.10);
            margin-bottom: 30px;
        }
        .highlight-queue h3 {
            color: #344a80; margin-bottom: 5px; font-size: 1.15rem;
            text-transform: uppercase; letter-spacing: 1.5px;
        }
        .highlight-queue h1 {
            font-size: 6rem;
            background: linear-gradient(145deg, #ab0846, #f55078);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
            margin: 0; font-weight: 900; line-height: 1;
        }
        .highlight-queue h2 { color: #344a80; font-size: 1.7rem; margin-top: 15px; }

        .legal-notice {
            background-color: #ffffff;
            border-left: 5px solid #ec6a88;
            padding: 22px 26px;
            font-size: 1rem;
            color: #263238 !important;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 12px rgba(35, 50, 86, 0.08);
            line-height: 1.7;
        }
        .legal-notice strong { color: #344a80; }

        footer { visibility: hidden; }
    </style>
""", unsafe_allow_html=True)

# ================================================================
# SEGURANÇA — FUNÇÕES
# ================================================================

def criptografar_dado(texto: str) -> str:
    """Hash SHA-256 apenas para comparação de identificadores (não usar em senha)."""
    return hashlib.sha256(str(texto).encode()).hexdigest()


def hash_senha(senha: str) -> str:
    return bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()


def verificar_senha(senha: str, hash_armazenado: str) -> bool:
    try:
        return bcrypt.checkpw(senha.encode(), hash_armazenado.encode())
    except (ValueError, TypeError):
        return False


def padronizar_cpf(cpf: str) -> str:
    """Mantém apenas dígitos do CPF."""
    return "".join(c for c in str(cpf or "") if c.isdigit())


def sanitizar(texto) -> str:
    """Escapa HTML antes de qualquer interpolação em st.markdown com HTML."""
    return html.escape(str(texto if texto is not None else ""))


def limitar_tentativas() -> bool:
    """Bloqueia login por 5 minutos após 5 tentativas falhas."""
    falhas = st.session_state.get("tentativas_login", 0)
    bloqueio_ate = st.session_state.get("bloqueio_ate", 0)
    if time.time() < bloqueio_ate:
        restante = int(bloqueio_ate - time.time())
        st.error(f"Muitas tentativas. Aguarde {restante} segundos antes de tentar novamente.")
        return False
    if falhas >= 5:
        st.session_state.bloqueio_ate = time.time() + 300
        st.session_state.tentativas_login = 0
        return False
    return True


def registrar_falha_login():
    st.session_state.tentativas_login = st.session_state.get("tentativas_login", 0) + 1


def limpar_sessao():
    """Remove dados sensíveis da sessão (logout)."""
    for chave in ["logado", "dados_paciente", "gestor", "novo_cpf"]:
        st.session_state.pop(chave, None)

# ================================================================
# DADOS — LEITURA DAS PLANILHAS (Google Sheets via CSV público)
# ================================================================

@st.cache_data(ttl=30, show_spinner="Atualizando base...")
def carregar_bases():
    url_fila = (
        f"https://docs.google.com/spreadsheets/d/{SHEET_FILA_ID}/gviz/tq"
        f"?tqx=out:csv&sheet={ABA_FILA}"
    )
    url_cadastro = (
        f"https://docs.google.com/spreadsheets/d/{SHEET_CADASTRO_ID}/gviz/tq"
        f"?tqx=out:csv&sheet={ABA_CADASTRO}"
    )
    try:
        df_fila = pd.read_csv(url_fila, dtype=str)
    except Exception:
        df_fila = pd.DataFrame(columns=COLUNAS_FILA)

    try:
        df_cadastro = pd.read_csv(url_cadastro, dtype=str)
    except Exception:
        df_cadastro = pd.DataFrame(columns=["Nome Completo", "CPF", "Nome na escala", "Telefone"])

    # Normalizações
    df_fila.columns = [c.strip() for c in df_fila.columns]
    df_cadastro.columns = [c.strip() for c in df_cadastro.columns]

    # Remove linhas fantasma: sem Nome_Paciente OU sem CPF
    if "Nome_Paciente" in df_fila.columns and "CPF" in df_fila.columns:
        df_fila = df_fila[
            df_fila["Nome_Paciente"].notna()
            & (df_fila["Nome_Paciente"].str.strip() != "")
            & df_fila["CPF"].notna()
            & (df_fila["CPF"].str.strip() != "")
        ].copy()
        df_fila["CPF_Digitos"] = df_fila["CPF"].apply(padronizar_cpf)
        df_fila["Escore_Num"] = pd.to_numeric(
            df_fila.get("Escore_Prioridade", "").astype(str).str.replace(",", "."), errors="coerce"
        )
        df_fila["Ordem_Cadastro"] = pd.to_datetime(
            df_fila.get("Data_Cadastro_AIH"), errors="coerce", dayfirst=True
        )

    return df_fila, df_cadastro


def calcular_fila(df_fila: pd.DataFrame) -> pd.DataFrame:
    """Ordena a fila por prioridade de espera (mais antigo primeiro)."""
    if df_fila.empty:
        return df_fila
    return df_fila.sort_values(
        by=["Ordem_Cadastro", "Escore_Num"],
        ascending=[True, False],
        na_position="last",
    ).reset_index(drop=True)

# ================================================================
# CABEÇALHO INSTITUCIONAL
# ================================================================

def renderizar_cabecalho():
    st.markdown("""
        <div style="display:flex; justify-content:space-between; align-items:flex-end;
                    margin-bottom:15px; flex-wrap:wrap; gap:10px;">
            <div>
                <h1 style="font-size:1.6rem; color:#344a80; margin:0;">
                    HOSPITAL ESTADUAL CENTRAL
                </h1>
                <p style="margin:0; color:#263238; font-size:0.95rem;">
                    Portal de Acompanhamento da Fila de Espera
                </p>
            </div>
            <div style="font-family:'Montserrat',sans-serif; font-weight:800;
                        color:#344a80; font-size:0.9rem;">
                FUNDAÇÃO <span style="color:#ec6a88;">INOVA</span> CAPIXABA
            </div>
        </div>
        <hr style="border:none; height:2px;
                   background:linear-gradient(90deg, #344a80, #ec6a88);
                   border-radius:2px; margin-bottom:25px;">
    """, unsafe_allow_html=True)


def renderizar_rodape():
    st.markdown("""
        <p style="text-align:center; color:#263238; font-size:0.8rem;
                  margin-top:40px; opacity:0.8;">
            Hospital Estadual Central — Acolher e Cuidar · SUS · Governo do Estado do Espírito Santo
        </p>
    """, unsafe_allow_html=True)

# ================================================================
# TELAS
# ================================================================

def tela_consulta_paciente():
    renderizar_cabecalho()

    st.markdown(
        '<div class="legal-notice">Este portal exibe a <strong>posição na fila de espera</strong> '
        'de cirurgias eletivas conforme dados oficiais do Hospital Estadual Central. '
        'Para consultar, informe seu <strong>CPF</strong> e a <strong>data de nascimento</strong> '
        'cadastrados. Nenhum dado pessoal é armazenado nesta consulta.</div>',
        unsafe_allow_html=True,
    )

    with st.form("form_consulta"):
        cpf_input = st.text_input("CPF", placeholder="000.000.000-00")
        nascimento_input = st.text_input("Data de Nascimento", placeholder="DD/MM/AAAA")
        enviado = st.form_submit_button("Consultar Minha Posição")

    if not enviado:
        renderizar_rodape()
        return

    cpf_digitos = padronizar_cpf(cpf_input)
    if len(cpf_digitos) != 11:
        st.error("Informe um CPF válido com 11 dígitos.")
        return

    df_fila, _ = carregar_bases()
    if df_fila.empty:
        st.error("Não foi possível ler a base de dados agora. Tente novamente em instantes.")
        return

    # Consulta exige CPF + nascimento (evita enumeração por CPF)
    nascimento_norm = nascimento_input.strip()
    mascara = (
        (df_fila["CPF_Digitos"] == cpf_digitos)
        & (
            df_fila["Data_Nascimento"].astype(str).str.strip().str[:10]
            == pd.to_datetime(nascimento_norm, dayfirst=True, errors="coerce").strftime("%Y-%m-%d")
        )
    )
    resultado = df_fila[mascara]

    if resultado.empty:
        st.warning("Paciente não localizado na fila. Verifique os dados ou procure a regulação do hospital.")
        return

    fila_ordenada = calcular_fila(df_fila)
    posicao = fila_ordenada.index[fila_ordenada["CPF_Digitos"] == cpf_digitos][0] + 1
    p = resultado.iloc[0]

    # Guarda APENAS os campos exibidos — nunca o CPF/CNS completos
    st.session_state.dados_paciente = {
        "nome": p["Nome_Paciente"],
        "posicao": int(posicao),
        "especialidade": p.get("Especialidade", "—"),
        "aih": p.get("Numero_AIH", "—"),
        "cid": p.get("CID", "") or "—",
        "lab": p.get("Status_Exames_Lab", "—"),
        "imagem": p.get("Status_Exames_Imagem", "—"),
        "cardio": p.get("Status_Avaliacao_Cardio", "—"),
        "pre_anestesica": p.get("Status_Avaliacao_PreAnestesica", "—"),
ecialidade" in st.session_state.dados_paciente else None
    )


def renderizar_resultado():
    d = st.session_state.dados_paciente
    nome = sanitizar(d["nome"].split()[0])  # apenas primeiro nome na tela

    st.markdown(f"""
        <div class="highlight-queue">
            <h3>Olá, {nome}! Sua posição na fila é</h3>
            <h1>{d['posicao']}º</h1>
            <h2>{sanitizar(d['especialidade'])}</h2>
        </div>
    """, unsafe_allow_html=True)

    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**AIH:** {sanitizar(d['aih'])}")
            st.markdown(f"**CID:** {sanitizar(d['cid'])}")
ecialidade")}")
        with col2:
            st.markdown(f"**Exames Laboratoriais:** {sanitizar(d['lab'])}")
            st.markdown(f"**Exames de Imagem:** {sanitizar(d['imagem'])}")
            st.markdown(f"**Avaliação Cardio:** {sanitizar(d['cardio'])}")
            st.markdown(f"**Pré-Anestésica:** {sanitizar(d['pre_anestesica'])}")

    st.markdown(
        '<div class="legal-notice"><strong>Acompanhe:</strong> a posição pode mudar conforme '
        'chamadas e desistências. Mantenha seus exames em dia. Em caso de piora do quadro, '
        'procure imediatamente o serviço de saúde ou a UPA mais próxima.</div>',
        unsafe_allow_html=True,
    )

    col_btn, _ = st.columns([1, 2])
    with col_btn:
        if st.button("Nova Consulta"):
            limpar_sessao()
            st.rerun()

    renderizar_rodape()


def tela_login_gestor():
    renderizar_cabecalho()

    if not limitar_tentativas():
        renderizar_rodape()
        return

    _, df_cadastro = carregar_bases()

    st.markdown("### 🔐 Área do Gestor")
    with st.form("form_gestor"):
        cpf_gestor = st.text_input("CPF do Gestor", placeholder="000.000.000-00")
        senha_gestor = st.text_input("Senha", type="password")
        entrar = st.form_submit_button("Entrar")

    if not entrar:
        renderizar_rodape()
        return

    cpf_digitos = padronizar_cpf(cpf_gestor)
    if df_cadastro.empty:
        st.error("Base de cadastro indisponível.")
        return

    col_cpf = next((c for c in df_cadastro.columns if "cpf" in c.lower()), None)
    col_senha_hash = next((c for c in df_cadastro.columns if "senha_hash" in c.lower()), None)
    if col_cpf is None:
        st.error("Planilha de cadastro sem coluna de CPF.")
        return

    registro = df_cadastro[
        df_cadastro[col_cpf].apply(padronizar_cpf) == cpf_digitos
    ]
    if registro.empty:
        registrar_falha_login()
        st.error("CPF ou senha incorretos.")
        return

    hash_alvo = None
    if col_senha_hash and registro.iloc[0].get(col_senha_hash):
        hash_alvo = str(registro.iloc[0][col_senha_hash]).strip()
    else:
        hash_alvo = st.secrets.get("SENHA_INICIAL_HASH", "")  # bcrypt do padrão inicial

    if hash_alvo and verificar_senha(senha_gestor, hash_alvo):
        st.session_state.gestor = {"cpf": cpf_digitos}
        st.session_state.tentativas_login = 0
        st.rerun()
    else:
        registrar_falha_login()
        st.error("CPF ou senha incorretos.")

    renderizar_rodape()


def tela_painel_gestor():
    renderizar_cabecalho()
    st.markdown("### 📊 Painel do Gestor")

    df_fila, _ = carregar_bases()
    fila = calcular_fila(df_fila)

    if fila.empty:
        st.info("Nenhum paciente com registro completo na fila no momento.")
    else:
        col1, col2, col3 = st.columns(3)
        col1.metric("Total na fila", len(fila))
        espec_counts = fila["Especialidade"].value_counts() if "Especialidade" in fila.columns else pd.Series()
        col2.metric("Especialidades", len(espec_counts))
        sem_exames = int(
            (fila.get("Status_Exames_Lab", "").astype(str).str.strip().eq("Pendente")).sum()
        )
        col3.metric("Aguardando exames", sem_exames)

        visivel = fila[
            [
                "Nome_Paciente", "CPF", "Especialidade", "Numero_AIH",
                "Status_Exames_Lab", "Status_Exames_Imagem",
                "Status_Avaliacao_Cardio", "Status_Avaliacao_PreAnestesica",
                "Escore_Prioridade",
            ]
        ].copy()
        visivel["CPF"] = visivel["CPF"].apply(
            lambda c: f"***.{padronizar_cpf(c)[-6:-3]}.***-{padronizar_cpf(c)[-2:]}"
            if padronizar_cpf(c) else "—"
        )
        st.dataframe(visivel, use_container_width=True, hide_index=True)

    col_btn, _ = st.columns([1, 3])
    with col_btn:
        if st.button("Sair", key="btn_sair"):
            limpar_sessao()
            st.rerun()

    renderizar_rodape()

# ================================================================
# ROTEAMENTO
# ================================================================
if "gestor" in st.session_state:
    tela_painel_gestor()
elif "dados_paciente" in st.session_state:
    renderizar_resultado()
else:
    tela_consulta_paciente()
    with st.container():
        st.markdown("<div style='margin-top:40px; text-align:center;'>", unsafe_allow_html=True)
        if st.button("Sou Gestor", key="btn_gestor"):
            st.session_state.tela_gestor = True
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
