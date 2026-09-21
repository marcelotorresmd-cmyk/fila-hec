# -*- coding: utf-8 -*-
"""Portal Fila de Espera — Hospital Estadual Central (padrão Inova Capixaba)."""
import hashlib, html, time
import bcrypt, pandas as pd, streamlit as st

st.set_page_config(page_title="Fila de Espera — HEC", page_icon="🏥", layout="centered")
SHEET_FILA = st.secrets.get("SHEET_FILA_ID", "1d1X3vGQGdRA5Wpg3cnfKIYSXRiE6VC1XoCTn1XBcTj0")
SHEET_CAD = st.secrets.get("SHEET_CADASTRO_ID", "1FRvVEvL4S3oCJJKA2OzrKnSOqiphRjZy-lq4cv65EXY")
ABA_FILA, ABA_CAD = "Página1", "Cadastro"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@600;800&family=Poppins:wght@400;600&display=swap');
html, body, .stApp { font-family:'Poppins',sans-serif !important; }
h1,h2,h3 { font-family:'Montserrat',sans-serif !important; }
.stApp { background:linear-gradient(180deg,#fff 0%,#f8f9fa 100%) !important; color:#263238 !important; }
.stButton>button {
  background:#344a80 !important; color:#fff !important; border:none !important;
  border-radius:8px !important; font-weight:700 !important; padding:.6rem 1.4rem !important;
  box-shadow:0 4px 12px rgba(52,74,128,.25) !important; transition:all .2s;
}
.stButton>button:hover { background:#ec6a88 !important; transform:translateY(-2px); }
.btn-gestor>button {
  background:transparent !important; color:#344a80 !important;
  border:1px solid #344a80 !important; border-radius:20px !important; font-weight:600 !important;
}
.btn-gestor>button:hover { background:#ec6a88 !important; color:#fff !important; border-color:#ec6a88 !important; }
.card { background:#fff; padding:28px; border-radius:16px; box-shadow:0 8px 28px rgba(35,50,86,.10); margin-bottom:16px; }
.avisodel { color:#344a80; font-weight:800; font-size:1.15rem; letter-spacing:1px; text-transform:uppercase; text-align:center; }
.posicao {
  text-align:center; background:#fff; border-radius:20px; padding:36px 20px; margin-bottom:20px;
  border-top:6px solid #ec6a88; border-bottom:6px solid #344a80;
  box-shadow:0 10px 30px rgba(35,50,86,.10);
}
.posicao .num {
  font-size:5.5rem; font-weight:900; line-height:1; margin:0;
  background:linear-gradient(145deg,#ab0846,#f55078);
  -webkit-background-clip:text; background-clip:text; color:transparent;
}
.legal {
  background:#fff; border-left:5px solid #ec6a88; padding:18px 24px;
  border-radius:10px; box-shadow:0 4px 12px rgba(35,50,86,.08); margin-bottom:24px; line-height:1.6;
}
footer { visibility:hidden; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ---------------- Segurança ----------------
def digitos(v): return "".join(c for c in str(v or "") if c.isdigit())
def sanitize(v): return html.escape(str(v if v is not None else "—"))
def confere_senha(senha, h):
    try: return bcrypt.checkpw(senha.encode(), h.strip().encode())
    except Exception: return False

def falha_login():
    st.session_state["tent"] = st.session_state.get("tent", 0) + 1
    if st.session_state["tent"] >= 5:
        st.session_state["bloq"] = time.time() + 300
        st.session_state["tent"] = 0

def sai_sessao():
    for k in ("paciente", "gestor"): st.session_state.pop(k, None)

# ---------------- Dados ----------------
@st.cache_data(ttl=30, show_spinner="Atualizando base...")
def carregar():
    u = f"https://docs.google.com/spreadsheets/d/{{}}/gviz/tq?tqx=out:csv&sheet={{}}"
    try: fila = pd.read_csv(u.format(SHEET_FILA, ABA_FILA), dtype=str)
    except Exception: fila = pd.DataFrame()
    try: cad = pd.read_csv(u.format(SHEET_CAD, ABA_CAD), dtype=str)
    except Exception: cad = pd.DataFrame()
    fila.columns = [c.strip() for c in fila.columns]
    if not fila.empty and {"Nome_Paciente", "CPF"}.issubset(fila.columns):
        fila = fila[fila["Nome_Paciente"].notna() & (fila["Nome_Paciente"].str.strip() != "")]
        fila = fila[fila["CPF"].notna() & (fila["CPF"].str.strip() != "")].copy()
        fila["CPF_DIG"] = fila["CPF"].apply(digitos)
        fila["Data"] = pd.to_datetime(fila["Data_Cadastro_AIH"], dayfirst=True, errors="coerce")
        fila = fila.sort_values(["Data"], ascending=True).reset_index(drop=True)
    return fila, cad

# ---------------- Telas ----------------
def cabecalho():
    st.markdown(
        '<h1 style="color:#344a80;">HOSPITAL ESTADUAL CENTRAL</h1>'
        '<p style="color:#263238;">Portal de Acompanhamento da Fila de Espera</p>'
        '<hr style="height:2px;border:none;border-radius:2px;'
        'background:linear-gradient(90deg,#344a80,#ec6a88);">',
        unsafe_allow_html=True)

def tela_consulta():
    cabecalho()
    st.markdown('<div class="legal">Informe seu <b>CPF</b> e sua <b>data de nascimento</b> para ver '
                'sua posição na fila. Nenhum dado pessoal é armazenado nesta consulta.</div>',
                unsafe_allow_html=True)
    with st.form("consulta"):
        cpf = st.text_input("CPF", placeholder="000.000.000-00")
        nasc = st.text_input("Data de Nascimento", placeholder="DD/MM/AAAA")
        ok = st.form_submit_button("Consultar Minha Posição")
    if not ok or st.session_state.get("paciente"):
        return
    cpf_d = digitos(cpf)
    if len(cpf_d) != 11:
        st.error("Informe um CPF válido com 11 dígitos.")
        return
    fila, _ = carregar()
    if fila.empty:
        st.error("Base indisponível. Tente novamente em instantes.")
        return
    alvo = pd.to_datetime(nasc, dayfirst=True, errors="coerce")
    if pd.isna(alvo):
        st.error("Informe a data de nascimento (DD/MM/AAAA).")
        return
    r = fila[fila["CPF_DIG"] == cpf_d]
    if r.empty:
        st.warning("Paciente não localizado na fila. Verifique os dados.")
        return
    st.session_state["paciente"] = {
        "nome": sanitize(r.iloc[0]["Nome_Paciente"]),
        "pos": int(r.index[0]) + 1,
        "esp": sanitize(r.iloc[0].get("Especialidade")),
        "aih": sanitize(r.iloc[0].get("Numero_AIH")),
        "cid": sanitize(r.iloc[0].get("CID")) or "—",
    }

def tela_resultado():
    d = st.session_state["paciente"]
    primeiro = d["nome"].split()[0]
    st.markdown(  # valor já sanitizado na origem
        animate := None, ) if False else None
    st.markdown(
        '<div class="posicao"><div class="avisodel">Olá, ' + primeiro +
        '! Sua posição na fila é</div>'
        '<p class="num">' + str(d["pos"]) + u"º</p>"
        '<h2 style="color:#344a80;">' + d["esp"] + "</h2></div>",
        unsafe_allow_html=True)
    with st.container(border=True):
        c1, c2 = st.columns(2)
        c1.markdown(f"**AIH:** {d['aih']}")
        c2.markdown(f"**CID:** {d['cid']}")
    st.markdown('<div class="legal"><b>Acompanhe:</b> a posição pode mudar conforme chamadas e '
                'desistências. Em caso de piora, procure o serviço de saúde mais próximo.</div>',
                unsafe_allow_html=True)
    if st.button("Nova Consulta"):
        sai_sessao()
        st.rerun()

def tela_gestor_login():
    cabecalho()
    if time.time() < st.session_state.get("bloq", 0):
        st.error(f"Muitas tentativas. Aguarde {int(st.session_state['bloq'] - time.time())}s.")
        return
    _, cad = carregar()
    st.markdown("### 🔐 Área do Gestor")
    with st.form("login"):
        g_cpf = st.text_input("CPF do Gestor")
        g_senha = st.text_input("Senha", type="password")
        ok = st.form_submit_button("Entrar")
    if not ok:
        return
    cols = [c for c in (cad.columns if not cad.empty else []) if "cpf" in c.lower()]
    if not cols:
        st.error("Cadastro indisponível.")
        return
    g = cad[cad[cols[0]].apply(digitos) == digitos(g_cpf)]
    col_hash = next((c for c in g.columns if "senha_hash" in c.lower()), None)
    h = str(g.iloc[0].get(col_hash)) if (not g.empty and col_hash) else st.secrets.get("SENHA_INICIAL_HASH", "")
    if not g.empty and h and confere_senha(g_senha, h):
        st.session_state["gestor"] = True
        st.session_state["tent"] = 0
        st.rerun()
    else:
        falha_login()
        st.error("CPF ou senha incorretos.")

def tela_gestor_painel():
    cabecalho()
    st.markdown("### 📊 Painel do Gestor")
    fila, _ = carregar()
    if fila.empty:
        st.info("Nenhum paciente com registro completo na fila.")
    else:
        c1, c2 = st.columns(2)
        c1.metric("Total na fila", len(fila))
        c2.metric("Especialidades", fila["Especialidade"].nunique() if "Especialidade" in fila else 0)
        vis = fila[["Nome_Paciente", "CPF", "Especialidade", "Numero_AIH",
                    "Status_Exames_Lab", "Status_Exames_Imagem", "Escore_Prioridade"]].copy()
        vis["CPF"] = vis["CPF"].apply(lambda c: f"***.{digitos(c)[-6:-3]}.***-{digitos(c)[-2:]}" if digitos(c) else "—")
        st.dataframe(vis, use_container_width=True, hide_index=True)
    if st.button("Sair", key="btn_sair"):
        sai_sessao()
        st.rerun()

# ---------------- Roteamento ----------------
if st.session_state.get("gestor"):
    tela_gestor_painel()
elif st.session_state.get("paciente"):
    cabecalho()
    tela_resultado()
else:
    tela_consulta()
    if not st.session_state.get("paciente"):
        with st.container():
            st.markdown("<div style='margin-top:30px;text-align:center;'>", unsafe_allow_html=True)
            st.markdown('<span class="btn-gestor"></span>', unsafe_allow_html=True)
            if st.button("Sou Gestor", key="btn_gestor"):
                st.session_state["tela_gestor"] = True
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
