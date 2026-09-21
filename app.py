# -*- coding: utf-8 -*-
"""Portal Fila de Espera — Hospital Estadual Central (padrão Inova Capixaba)."""
import html
import time

import bcrypt
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Fila de Espera — HEC", page_icon="🏥", layout="centered")
SHEET_FILA = st.secrets.get("SHEET_FILA_ID", "1d1X3vGQGdRA5Wpg3cnfKIYSXRiE6VC1XoCTn1XBcTj0")
SHEET_CAD = st.secrets.get("SHEET_CADASTRO_ID", "1Ql2dIHQBPuqoLOpWrQlq26V8Y30c5xhmEzLaCMB9UnI")
ABA_FILA, ABA_CAD = "Página1", "Página1"

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


# ---------------- Utilidades ----------------
def digitos(v):
    return "".join(c for c in str(v or "") if c.isdigit())


def sanitize(v):
    return html.escape(str(v if v not in (None, "") else "—"))


def confere_senha(senha, h):
    try:
        return bcrypt.checkpw(senha.encode(), str(h).strip().encode())
    except Exception:
        return False


def falha_login():
    st.session_state["tent"] = st.session_state.get("tent", 0) + 1
    if st.session_state["tent"] >= 5:
        st.session_state["bloq"] = time.time() + 300
        st.session_state["tent"] = 0


def sai_sessao():
    for k in ("paciente", "gestor", "tela_gestor"):
        st.session_state.pop(k, None)


# ---------------- Dados ----------------
@st.cache_data(ttl=30, show_spinner="Atualizando base...")
def carregar():
    u = "https://docs.google.com/spreadsheets/d/{}/gviz/tq?tqx=out:csv&sheet={}"
    # Fila HEC — com cabeçalho
    try:
        fila = pd.read_csv(u.format(SHEET_FILA, ABA_FILA), dtype=str)
        fila.columns = [c.strip() for c in fila.columns]
    except Exception:
        fila = pd.DataFrame()
    # Cadastro de gestores — SEM cabeçalho (linha 1 já é dado)
    try:
        cad = pd.read_csv(u.format(SHEET_CAD, ABA_CAD), dtype=str, header=None)
        cad.columns = ["Nome", "CPF", "Email"][: len(cad.columns)] + list(
            cad.columns[len(cad.columns[:3])]
        ) if len(cad.columns) > 3 else ["Nome", "CPF", "Email"]
    except Exception:
        cad = pd.DataFrame(columns=["Nome", "CPF", "Email"])
    if not fila.empty and {"Nome_Paciente", "CPF", "Cartao_SUS"}.issubset(fila.columns):
        fila = fila[fila["Nome_Paciente"].notna() & (fila["Nome_Paciente"].str.strip() != "")]
        fila = fila[fila["CPF"].notna() & (fila["CPF"].str.strip() != "")].copy()
        fila["CPF_DIG"] = fila["CPF"].apply(digitos)
        fila["SUS_DIG"] = fila["Cartao_SUS"].apply(digitos)
        fila["Data"] = pd.to_datetime(fila.get("Data_Cadastro_AIH"), dayfirst=True, errors="coerce")
        fila = fila.sort_values(["Data"]).reset_index(drop=True)
    return fila, cad


def cabecalho():
    st.markdown(
        '<h1 style="color:#344a80;">HOSPITAL ESTADUAL CENTRAL</h1>'
        '<p style="color:#263238;">Portal de Acompanhamento da Fila de Espera</p>'
        '<hr style="height:2px;border:none;border-radius:2px;'
        'background:linear-gradient(90deg,#344a80,#ec6a88);">',
        unsafe_allow_html=True,
    )


# ---------------- Paciente ----------------
def tela_consulta():
    cabecalho()
    st.markdown(
        '<div class="legal">Informe seu <b>CPF</b> e o <b>número do Cartão SUS</b> '
        'cadastrados para ver sua posição na fila. Nenhum dado pessoal é armazenado.</div>',
        unsafe_allow_html=True,
    )
    with st.form("consulta"):
        cpf = st.text_input("CPF", placeholder="000.000.000-00")
        sus = st.text_input("Cartão Nacional de Saúde (CNS)", placeholder="000 0000 0000 0000")
        ok = st.form_submit_button("Consultar Minha Posição")
    if not ok:
        return
    cpf_d, sus_d = digitos(cpf), digitos(sus)
    if len(cpf_d) != 11:
        st.error("Informe um CPF válido com 11 dígitos.")
        return
    if len(sus_d) != 15:
        st.error("Informe o CNS com 15 dígitos (impresso no cartão).")
        return
    fila, _ = carregar()
    if fila.empty:
        st.error("Base indisponível. Tente novamente em instantes.")
        return
    r = fila[(fila["CPF_DIG"] == cpf_d) & (fila["SUS_DIG"] == sus_d)]
    if r.empty:
        st.warning("Paciente não localizado. Confira CPF e CNS ou procure a regulação do hospital.")
        return
    p = r.iloc[0]
    st.session_state["paciente"] = {
        "nome": sanitize(p["Nome_Paciente"]),
        "pos": int(r.index[0]) + 1,
        "esp": sanitize(p.get("Especialidade")),
        "aih": sanitize(p.get("Numero_AIH")),
        "cid": sanitize(p.get("CID")),
    }


def tela_resultado():
    d = st.session_state["paciente"]
    primeiro = d["nome"].split()[0]
    st.markdown(
        '<div class="posicao"><p style="color:#344a80;font-weight:800;'
        'font-size:1.15rem;letter-spacing:1px;text-transform:uppercase;text-align:center;">'
        "Olá, " + primeiro + '! Sua posição na fila é</p>'
        '<p class="num">' + str(d["pos"]) + "º</p>"
        '<h2 style="color:#344a80;">' + d["esp"] + "</h2></div>",
        unsafe_allow_html=True,
    )
    with st.container(border=True):
        c1, c2 = st.columns(2)
        c1.markdown(f"**AIH:** {d['aih']}")
        c2.markdown(f"**CID:** {d['cid']}")
    st.markdown(
        '<div class="legal"><b>Acompanhe:</b> a posição pode mudar conforme chamadas e '
        "desistências. Em caso de piora do quadro, procure o serviço de saúde mais próximo.</div>",
        unsafe_allow_html=True,
    )
    if st.button("Nova Consulta"):
        sai_sessao()
        st.rerun()


# ---------------- Gestor ----------------
def tela_gestor_login():
    cabecalho()
    if time.time() < st.session_state.get("bloq", 0):
        restante = int(st.session_state["bloq"] - time.time())
        st.error(f"Muitas tentativas. Aguarde {restante} segundos.")
        return
    _, cad = carregar()
    st.markdown("### 🔐 Área do Gestor")
    with st.form("login"):
        g_cpf = st.text_input("CPF do Gestor", placeholder="000.000.000-00")
        g_senha = st.text_input("Senha", type="password")
        ok = st.form_submit_button("Entrar")
    if not ok:
        if st.button("← Voltar"):
            st.session_state.pop("tela_gestor", None)
            st.rerun()
        return
    cpf_d = digitos(g_cpf)
    if cad.empty or cpf_d not in cad["CPF"].apply(digitos).values:
        falha_login()
        st.error("CPF ou senha incorretos.")
        return
    # Senha: usa coluna Senha_Hash se existir; senão, a senha inicial dos secrets
    col_hash = next((c for c in cad.columns if "senha_hash" in str(c).lower()), None)
    hash_alvo = ""
    if col_hash:
        linha = cad[cad["CPF"].apply(digitos) == cpf_d].iloc[0]
        hash_alvo = str(linha.get(col_hash) or "").strip()
    if not hash_alvo:
        hash_alvo = st.secrets.get("SENHA_INICIAL_HASH", "")
    if hash_alvo and confere_senha(g_senha, hash_alvo):
        linha = cad[cad["CPF"].apply(digitos) == cpf_d].iloc[0]
        st.session_state["gestor"] = {"nome": sanitize(linha["Nome"])}
        st.session_state["tent"] = 0
        st.rerun()
    else:
        falha_login()
        st.error("CPF ou senha incorretos.")


def tela_gestor_painel():
    cabecalho()
    st.markdown(f"### 📊 Painel do Gestor — {st.session_state['gestor']['nome']}")
    fila, _ = carregar()
    if fila.empty:
        st.info("Nenhum paciente com registro completo na fila.")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("Total na fila", len(fila))
        c2.metric("Especialidades", fila["Especialidade"].nunique() if "Especialidade" in fila else 0)
        c3.metric(
            "Aguardando exames",
            int(fila.get("Status_Exames_Lab", pd.Series(dtype=str)).astype(str).str.strip().eq("Pendente").sum()),
        )
        vis = fila[
            ["Nome_Paciente", "CPF", "Cartao_SUS", "Especialidade", "Numero_AIH", "CID",
             "Status_Exames_Lab", "Status_Exames_Imagem", "Status_Avaliacao_Cardio",
             "Status_Avaliacao_PreAnestesica", "Escore_Prioridade"]
        ].copy()
        vis["CPF"] = vis["CPF"].apply(
            lambda c: f"***.{digitos(c)[-6:-3]}.***-{digitos(c)[-2:]}" if digitos(c) else "—"
        )
        vis["Cartao_SUS"] = vis["Cartao_SUS"].apply(lambda c: "…" + digitos(c)[-4:] if digitos(c) else "—")
        st.dataframe(vis, use_container_width=True, hide_index=True)
        st.download_button(
            "⬇️ Baixar fila completa (CSV)",
            fila.drop(columns=["CPF_DIG", "SUS_DIG", "Data"], errors="ignore").to_csv(index=False).encode("utf-8"),
            "fila_hec.csv",
            "text/csv",
        )
    if st.button("Sair", key="btn_sair"):
        sai_sessao()
        st.rerun()


# ---------------- Roteamento ----------------
if st.session_state.get("gestor"):
    tela_gestor_painel()
elif st.session_state.get("tela_gestor"):
    tela_gestor_login()
elif st.session_state.get("paciente"):
    cabecalho()
    tela_resultado()
else:
    tela_consulta()
    if not st.session_state.get("paciente"):
        st.markdown("<div style='margin-top:30px;text-align:center;'>", unsafe_allow_html=True)
        if st.button("Sou Gestor", key="btn_gestor"):
            st.session_state["tela_gestor"] = True
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
