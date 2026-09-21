# -*- coding: utf-8 -*-
"""Portal Fila de Espera — Hospital Estadual Central (padrão Inova Capixaba)."""
import html
import json
import random
import re
import smtplib
import string
import time
from datetime import datetime
from email.mime.text import MIMEText

import bcrypt
import gspread
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Fila de Espera — HEC", page_icon="🏥", layout="wide")
SHEET_FILA = st.secrets.get("SHEET_FILA_ID", "1d1X3vGQGdRA5Wpg3cnfKIYSXRiE6VC1XoCTn1XBcTj0")
SHEET_CAD = st.secrets.get("SHEET_CADASTRO_ID", "1Ql2dIHQBPuqoLOpWrQlq26V8Y30c5xhmEzLaCMB9UnI")
ABA_FILA, ABA_CAD = "Página1", "Página1"

# ================================================================
# VISUAL — identidade Inova profissional
# ================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@500;700;800;900&family=Poppins:wght@300;400;500;600;700&display=swap');
:root {
  --azul:#344a80; --azul-escuro:#233256; --rosa:#ec6a88; --magenta:#ab0846;
  --tinta:#263238; --neutro:#f5f6fa;
}
html, body, .stApp { font-family:'Poppins',sans-serif !important; }
h1,h2,h3,h4 { font-family:'Montserrat',sans-serif !important; }
.stApp { background:var(--neutro) !important; color:var(--tinta) !important; }

/* Faixa lateral institucional (azul-marinho em cima, vinho embaixo) */
.main .block-container { max-width:1100px; padding:2rem 2.5rem 4rem; }
div[data-testid="stAppViewContainer"] { background:var(--neutro) !important; }

.bloco {
  background:#ffffff; border-radius:18px; padding:2.2rem 2.4rem;
  box-shadow:0 10px 34px rgba(35,50,86,.10); margin-bottom:1.6rem;
}
.hero {
  background:linear-gradient(120deg, var(--azul) 0%, var(--azul-escuro) 100%);
  border-radius:18px; padding:2.4rem 2.4rem 2rem; color:#fff; margin-bottom:1.6rem;
  position:relative; overflow:hidden;
}
.hero::after {
  content:""; position:absolute; right:-60px; top:-60px; width:220px; height:220px;
  border-radius:50%;
  background:radial-gradient(circle, rgba(236,106,136,.45) 0%, transparent 70%);
}
.hero h1 { color:#fff; font-weight:900; letter-spacing:.5px; margin:0; font-size:1.7rem; }
.hero p  { margin:.3rem 0 0; opacity:.85; }
.oi { color:var(--rosa); font-weight:700; }

.posicao-card {
  text-align:center; background:#fff; border-radius:24px; padding:2.6rem 2rem;
  border-top:8px solid var(--rosa); box-shadow:0 14px 40px rgba(35,50,86,.12);
  margin-bottom:1.6rem;
}
.posicao-card .rotulo {
  color:var(--azul); font-weight:700; text-transform:uppercase;
  letter-spacing:2px; font-size:1rem;
}
.posicao-card .num {
  font-size:6rem; font-weight:900; line-height:1; margin:.2rem 0;
  background:linear-gradient(145deg,var(--magenta),#f55078);
  -webkit-background-clip:text; background-clip:text; color:transparent;
}
.aviso {
  background:#fff; border-left:5px solid var(--rosa); padding:1.1rem 1.4rem;
  border-radius:12px; box-shadow:0 6px 18px rgba(35,50,86,.08);
  line-height:1.65; margin-bottom:1.4rem; font-size:.95rem;
}

.stButton > button, .stForm button {
  background:var(--azul) !important; color:#fff !important; border:none !important;
  border-radius:10px !important; font-weight:600 !important; padding:.55rem 1.4rem !important;
  box-shadow:0 4px 14px rgba(52,74,128,.25) !important; transition:all .2s ease !important;
}
.stButton > button:hover, .stForm button:hover {
  background:var(--rosa) !important; transform:translateY(-2px);
  box-shadow:0 8px 20px rgba(236,106,136,.35) !important;
}
input, .stTextInput input { border-radius:10px !important; }
footer { visibility:hidden; }
[data-testid="stMetricValue"] { color: var(--azul); font-family:'Montserrat',sans-serif; }
</style>
""", unsafe_allow_html=True)

# ================================================================
# UTILITÁRIOS
# ================================================================
DIG = lambda v: "".join(c for c in str(v or "") if c.isdigit())
SAN = lambda v: html.escape(str(v if v not in (None, "") else "—"))


def validar_cpf(cpf_d: str) -> bool:
    if len(cpf_d) != 11 or cpf_d == cpf_d[0] * 11:
        return False
    for n in (9, 10):
        s = sum(int(cpf_d[i]) * (n - i) for i in range(n))
        dv = (s * 10) % 11 % 10
        if int(cpf_d[n]) != dv:
            return False
    return True


def confere_senha(senha: str, hash_alvo: str) -> bool:
    try:
        return bcrypt.checkpw(senha.encode(), str(hash_alvo).strip().encode())
    except (ValueError, TypeError):
        return False


def hash_senha(senha: str) -> str:
    return bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()


def falha_login():
    st.session_state["tent"] = st.session_state.get("tent", 0) + 1
    if st.session_state["tent"] >= 5:
        st.session_state["bloq"] = time.time() + 300
        st.session_state["tent"] = 0


def sai():
    for k in ("paciente", "gestor", "tela_gestor"):
        st.session_state.pop(k, None)

# ================================================================
# ESCRITA NA PLANILHA (conta de serviço, via secrets)
# ================================================================
GC = None

def cliente_gdrive():
    global GC
    if GC is None:
        info = st.secrets.get("gcp_service_account")
        if not info:
            return None
        try:
            dados = dict(info) if not isinstance(info, str) else json.loads(info)
            GC = gspread.service_account_from_dict(dados)
        except Exception:
            return None
    return GC


def gravar_senha_hash(cpf_d: str, hash_val: str) -> bool:
    """Salva Senha_Hash na planilha de gestores. Usa coluna existente ou cria."""
    gc = cliente_gdrive()
    if gc is None:
        return False
    try:
        ws = gc.open_by_key(SHEET_CAD).worksheet(ABA_CAD)
        valores = ws.get_all_values()  # sem header (linha 1 é dado)
        valores = valores or []
        n_lin = len(valores) + 1
        #localizar coluna com header◥ Senha_Hash em algum lugar vazio...
        vals = valores or []
        linhas = vals
        # O cabeçalho foi adicionado por engane
        linhas = [row for row in linhas]
        # locate CPF column among columns that hold cpf-digit-like cells
        idx_cpf = col_hash = None
        # Procura coluna "Senha_Hash"/"CPF" se a planilha tiver header:
        primeira = linhas[0] if linhas else []
        if any("senha_hash" in (c or "").lower() for c in primeira) or \
           any("cpf" in str(c or "").lower() for c in primeira):
            hdr = [c.strip().lower() if c else "" for c in primeira]
            if "cpf" in hdr: idx_cpf = hdr.index("cpf")
            if "senha_hash" in hdr: col_hash = hdr.index("senha_hash") + 1
            start = 2
        else:
            # sem header: CPF na coluna 2 (B), Senha_Hash na coluna 4 (D)
            idx_cpf, col_hash, start = 1, 4, 1
        if col_hash is None:
            col_hash = len(primeira) + 1 if primeira else 4
            # adiciona rótulo se houver header
            if start > 1 and primeira:
                ws.update_cell(1, col_hash, "Senha_Hash")
        for i in range(start, n_lin + 1):
            if idx_cpf is not None and DIG(ws.cell(i, idx_cpf).value) == cpf_d:
                ws.update_cell(i, col_hash, hash_val)
                return True
        return False
    except Exception:
        return False


def enviar_email(destino: str, assunto: str, corpo: str) -> bool:
    smtp_user = st.secrets.get("SMTP_EMAIL")
    smtp_pass = st.secrets.get("SMTP_APP_PASSWORD")
    if not (smtp_user and smtp_pass):
        return False
    try:
        msg = MIMEText(corpo, "plain", "utf-8")
        msg["Subject"], msg["From"], msg["To"] = assunto, smtp_user, destino
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as s:
            s.login(smtp_user, smtp_pass)
            s.send_message(msg)
        return True
    except Exception:
        return False

# ================================================================
# DADOS
# ================================================================
@st.cache_data(ttl=30, show_spinner="Atualizando base...")
def carregar():
    u = "https://docs.google.com/spreadsheets/d/{}/gviz/tq?tqx=out:csv&sheet={}"
    try:
        fila = pd.read_csv(u.format(SHEET_FILA, ABA_FILA), dtype=str)
        fila.columns = [c.strip() for c in fila.columns]
    except Exception:
        fila = pd.DataFrame()
    try:
        cad = pd.read_csv(u.format(SHEET_CAD, ABA_CAD), dtype=str)
    except Exception:
        cad = pd.DataFrame()
    cad.columns = [c.strip() if isinstance(c, str) else c for c in cad.columns] if not cad.empty else []
    if not fila.empty and {"Nome_Paciente", "CPF", "Cartao_SUS"}.issubset(fila.columns):
        fila = fila[fila["Nome_Paciente"].notna() & (fila["Nome_Paciente"].str.strip() != "")]
        fila = fila[fila["CPF"].notna() & (fila["CPF"].str.strip() != "")].copy()
        fila["CPF_DIG"] = fila["CPF"].apply(DIG)
        fila["SUS_DIG"] = fila["Cartao_SUS"].apply(DIG)
        fila["Data"] = pd.to_datetime(fila.get("Data_Cadastro_AIH"), dayfirst=True, errors="coerce")
        fila = fila.sort_values("Data").reset_index(drop=True)
    if not cad.empty:
        col_cpf = next((c for c in cad.columns if "cpf" in c.lower()), None)
        col_mail = next((c for c in cad.columns if "email" in c.lower() or "mail" in c.lower()), None)
        col_nome = cad.columns[0]
        if col_cpf:
            cad["CPF_DIG"] = cad[col_cpf].apply(DIG)
    return fila, cad

# ================================================================
# COMPONENTES
# ================================================================
def hero():
    try:
        st.image("logo-inova-cor.png", width=120)
    except Exception:
        pass
    st.markdown(
        '<div class="hero"><p style="font-size:.8rem;letter-spacing:3px;'
        'text-transform:uppercase;opacity:.7;">Hospital Estadual Central</p>'
        '<h1>Portal de Posição da Fila de Espera</h1>'
        '<p style="font-size:.95rem;">Consulte sua posição de forma segura — '
        '<span class="oi">acolher e cuidar</span>.</p></div>',
        unsafe_allow_html=True,
    )


def bloco(conteudo):
    st.markdown(f'<div class="bloco">{"conteudo"}</div>', unsafe_allow_html=True)

# ================================================================
# PACIENTE
# ================================================================
def tela_consulta():
    hero()
    st.markdown(
        '<div class="aviso"><b>Status da fila atualizado automaticamente a cada 30 segundos.</b>'
        "<br>Informe seu CPF e o número do Cartão Nacional de Saúde para localizar seu registro. "
        "Nenhum dado pessoal é armazenado nesta consulta.</div>",
        unsafe_allow_html=True,
    )
    c_esq, c_dir = st.columns([1.1, 1])
    with c_esq:
        with st.container():
            with st.form("consulta"):
                cpf = st.text_input("CPF", placeholder="000.000.000-00")
                sus = st.text_input("Cartão Nacional de Saúde (CNS)", placeholder="000 0000 0000 0000")
                ok = st.form_submit_button("Consultar Minha Posição")
    with c_dir:
        st.markdown(
            '<div class="bloco" style="padding:1.6rem;"><b>🔎 Dica</b><br>'
            "Os dois números estão no cartão do SUS e no comprovante de cadastro na regulação. "
            "A posição pode mudar ao longo do dia.</div>",
            unsafe_allow_html=True,
        )
    if not ok:
        return
    cpf_d, sus_d = DIG(cpf), DIG(sus)
    if not validar_cpf(cpf_d):
        st.error("CPF inválido — verifique os 11 dígitos.")
        return
    if len(sus_d) != 15:
        st.error("Informe o CNS completo com 15 dígitos.")
        return
    fila, _ = carregar()
    if fila.empty:
        st.error("Base indisponível. Tente novamente em instantes.")
        return
    r = fila[(fila["CPF_DIG"] == cpf_d) & (fila["SUS_DIG"] == sus_d)]
    if r.empty:
        st.warning("Não encontramos seu registro. Confira os dados ou procure a regulação.")
        return
    p = r.iloc[0]
    st.session_state["paciente"] = {
        "nome": SAN(p["Nome_Paciente"].split()[0]),
        "pos": int(r.index[0]) + 1,
        "esp": SAN(p.get("Especialidade")),
        "aih": SAN(p.get("Numero_AIH")),
        "cid": SAN(p.get("CID")),
        "lab": SAN(p.get("Status_Exames_Lab")),
        "img": SAN(p.get("Status_Exames_Imagem")),
        "car": SAN(p.get("Status_Avaliacao_Cardio")),
        "pre": SAN(p.get("Status_Avaliacao_PreAnestesica")),
    }


def tela_resultado():
    d = st.session_state["paciente"]
    hero()
    st.markdown(
        f'<div class="posicao-card"><div class="rotulo">Olá, {d["nome"]} — sua posição na fila é</div>'
        f'<div class="num">{d["pos"]}º</div>'
        f'<h2 style="color:#344a80;">{d["esp"]}</h2></div>',
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="bloco"><b>🧾 Dados do procedimento</b>'
                    f"<br><b>AIH:</b> {d['aih']}<br><b>CID:</b> {d['cid']}<br>"
                    f"<b>Especialidade:</b> {d['esp']}</div>", unsafe_allow_html=True)
    with c2:
        cor = lambda s: "✅" if str(s).lower() == "concluído" else "⏳"
        st.markdown('<div class="bloco"><b>🩺 Exames e avaliações</b>'
                    f"<br>{cor(d['lab'])} Exames laboratoriais: <b>{d['lab']}</b>"
                    f"<br>{cor(d['img'])} Exames de imagem: <b>{d['img']}</b>"
                    f"<br>{cor(d['car'])} Avaliação cardiológica: <b>{d['car']}</b>"
                    f"<br>{cor(d['pre'])} Pré anestésica: <b>{d['pre']}</b></div>",
                    unsafe_allow_html=True)
    st.markdown(
        '<div class="aviso"><b>Acompanhe:</b> a posição pode mudar conforme chamadas, '
        "prioridades e desistências. Em caso de piora do quadro, procure o serviço de saúde "
        "ou a UPA mais próxima.</div>",
        unsafe_allow_html=True,
    )
    if st.button("⬅ Nova Consulta"):
        sai()
        st.rerun()

# ================================================================
# GESTOR
# ================================================================
def login_aceito_estado(nome, cpf_d, forcar_troca=False, hash_atual=""):
    st.session_state["gestor"] = {"nome": nome, "cpf": cpf_d,
                                  "forcar_troca": forcar_troca, "hash_atual": hash_atual}
    st.session_state["tent"] = 0


def autenticar_gestor(cpf_d: str, senha: str):
    _, cad = carregar()
    if cad.empty:
        return None, "Cadastro indisponível."
    LINHA = cad[cad["CPF_DIG"] == cpf_d]
    if LINHA.empty:
        return None, None  # usuário inexistente → mensagem genérica
    linha = LINHA.iloc[0]
    col_hash = next((c for c in cad.columns if "senha_hash" in c.lower()), None)
    hash_alvo = str(linha.get(col_hash) or "").strip() if col_hash else ""
    padrao = st.secrets.get("SENHA_INICIAL_HASH", "")
    if hash_alvo and confere_senha(senha, hash_alvo):
        if hash_alvo.startswith("TMP$"):
            return linha, ("temp", hash_alvo)
        return linha, ("ok", hash_alvo)
    if padrao and confere_senha(senha, padrao):
        return linha, ("padrao", padrao)
    return ("erro", None)


def tela_login_gestor():
    hero()
    c_esq, _ = st.columns([1.1, 1])
    with c_esq:
        st.markdown('<div class="bloco"><h3 style="color:#344a80;">🔐 Acesso do Gestor</h3>'
                    "Informe seu CPF e senha para visualizar a fila completa.</div>",
                    unsafe_allow_html=True)
        if time.time() < st.session_state.get("bloq", 0):
            st.error(f"Muitas tentativas. Aguarde {int(st.session_state['bloq'] - time.time())}s.")
        else:
            with st.form("login"):
                g_cpf = st.text_input("CPF", placeholder="000.000.000-00")
                g_senha = st.text_input("Senha", type="password")
                ok = st.form_submit_button("Entrar", use_container_width=True)
            st.markdown("<p style='text-align:center;margin-top:8px;'>", unsafe_allow_html=True)
            esqueci = st.button("Esqueci minha senha")
            st.markdown("</p>", unsafe_allow_html=True)
        if st.button("← Voltar ao portal"):
            st.session_state.pop("tela_gestor", None)
            st.rerun()
    if not (ok or esqueci):
        return
    cpf_d = DIG(g_cpf)
    if not validar_cpf(cpf_d):
        st.error("CPF inválido.")
        return
    _, cad = carregar()
    linha_cad = cad[cad.get("CPF_DIG", pd.Series(dtype=str)) == cpf_d]
    email = str(linha_cad.iloc[0].get("Email", "")).strip() if not linha_cad.empty else ""

    if esqueci:
        gc = cliente_gdrive()
        if gc is None:
            st.error("Serviço de redefinição indisponível — peça à TI que gere uma nova senha.")
            return
        if linha_cad.empty or not email:
            st.warning("Se este CPF estiver cadastrado, você receberá um e-mail em instantes.")
            return
        nova = "".join(random.choices(string.ascii_letters + string.digits, k=10)) + "!C@"
        if gravar_senha_hash(cpf_d, "TMP$" + hash_senha(nova)) and \
           enviar_email(email, "Portal HEC — senha temporária",
                        f"Olá!\n\nSua senha temporária de acesso ao Portal HEC é:\n\n{nova}\n\n"
                        "Use-a em seguida e troque por uma senha sua no primeiro acesso.\n\n"
                        "Se não pediu isso, considere o pedido de futuro compromisso suscetível e ignore esta mensagem."):
            st.success(f"Foi enviado um e-mail com a senha temporária para o cadastro do gestor.")
        else:
            st.error("Não foi possível enviar o e-mail agora. Tente novamente em instantes.")
        return

    if not ok:
        return
    estado, valor = autenticar_gestor(cpf_d, g_senha)
    if estado in ("ok", "temp", "padrao"):
        nome = SAN(linha_cad.iloc[0][cad.columns[0]]) if not linha_cad.empty else "Gestor"
        login_aceito_estado(nome, cpf_d, forcar_troca=(estado != "ok"),
                            hash_atual=valor[1] if isinstance(valor, tuple) else "")
        st.rerun()
    elif estado == "erro":
        falha_login()
        st.error("CPF ou senha incorretos.")


def tela_troca_senha():
    g = st.session_state["gestor"]
    hero()
    st.markdown('<div class="bloco"><h3 style="color:#344a80;">🔑 Defina a sua senha</h3>'
                "Por segurança, no primeiro acesso (ou após uma redefinição) você deve "
                "cadastrar uma senha pessoal. Mínimo de 8 caracteres.</div>",
                unsafe_allow_html=True)
    with st.form("troca"):
        n1 = st.text_input("Nova senha", type="password")
        n2 = st.text_input("Confirmar nova senha", type="password")
        ok = st.form_submit_button("Salvar senha")
    if ok:
        if n1 != n2:
            st.error("As senhas não são iguais.")
        elif len(n1) < 8:
            st.error("A senha deve ter ao menos 8 caracteres.")
        else:
            if gravar_senha_hash(g["cpf"], hash_senha(n1)):
                st.success("Senha definida com sucesso!")
                g["forcar_troca"], g["hash_atual"] = False, hash_senha(n1)
                st.rerun()
            else:
                st.warning(" ⚠ Não foi possível gravar na base agora — você poderá usar a senha "
                           "atual nesta sessão. Avise a TI para verificar a integração.")
                g["forcar_troca"] = False
                st.rerun()


def tela_painel_gestor():
    g = st.session_state["gestor"]
    st.markdown(
        f'<div class="hero" style="padding:1.4rem 2rem;"><h1 style="font-size:1.25rem;">'
        f"📊 Painel do Gestor — {g['nome']}</h1><p>Fila completa · atualizada a cada 30s</p></div>",
        unsafe_allow_html=True,
    )
    fila, _ = carregar()
    if fila.empty:
        st.info("Nenhum paciente com registro completo na fila.")
    else:
        c1, c2, c3, c4 = st.columns(4)
        pend = lambda col: int(fila.get(col, pd.Series(dtype=str)).astype(str).str.strip().eq("Pendente").sum())
        c1.metric("Total na fila", len(fila))
        c2.metric("Especialidades", fila["Especialidade"].nunique() if "Especialidade" in fila else 0)
        c3.metric("Aguardando exames", pend("Status_Exames_Lab") + pend("Status_Exames_Imagem"))
        c4.metric("Sem avaliação card.", pend("Status_Avaliacao_Cardio"))
        vis = fila[["Nome_Paciente", "CPF", "Cartao_SUS", "Especialidade", "Numero_AIH", "CID",
                    "Status_Exames_Lab", "Status_Exames_Imagem", "Status_Avaliacao_Cardio",
                    "Status_Avaliacao_PreAnestesica", "Escore_Prioridade"]].copy()
        vis["CPF"] = vis["CPF"].apply(lambda c: f"***.{DIG(c)[-6:-3]}.***-{DIG(c)[-2:]}" if DIG(c) else "—")
        vis["Cartao_SUS"] = vis["Cartao_SUS"].apply(lambda c: "…" + DIG(c)[-4:] if DIG(c) else "—")
        st.dataframe(vis, use_container_width=True, hide_index=True, height=430)
        st.download_button("⬇️ Baixar fila completa (CSV)",
                           fila.drop(columns=["CPF_DIG", "SUS_DIG", "Data"], errors="ignore")
                           .to_csv(index=False).encode("utf-8"), "fila_hec.csv", "text/csv")
    cc1, _ = st.columns([1, 4])
    with cc1:
        if st.button("Sair", key="btn_sair"):
            sai()
            st.rerun()

# ================================================================
# ROTEAMENTO
# ================================================================
if st.session_state.get("gestor"):
    if st.session_state["gestor"].get("forcar_troca"):
        tela_troca_senha()
    else:
        tela_painel_gestor()
elif st.session_state.get("tela_gestor"):
    tela_login_gestor()
elif st.session_state.get("paciente"):
    tela_resultado()
else:
    tela_consulta()
    st.markdown("<div style='text-align:center;margin-top:10px;'>", unsafe_allow_html=True)
    if st.button("🔐 Sou Gestor", key="btn_gestor"):
        st.session_state["tela_gestor"] = True
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
