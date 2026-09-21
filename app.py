# -*- coding: utf-8 -*-
"""Portal Fila de Espera — Hospital Estadual Central (padrão Inova Capixaba)."""
import html
import json
import random
import smtplib
import string
import time
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
# VISUAL
# ================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@500;700;800;900&family=Poppins:wght@300;400;500;600;700&display=swap');
:root { --azul:#344a80; --azul-escuro:#233256; --rosa:#ec6a88; --magenta:#ab0846; --tinta:#263238; --neutro:#f5f6fa; }
html, body, .stApp { font-family:'Poppins',sans-serif !important; }
h1,h2,h3,h4 { font-family:'Montserrat',sans-serif !important; }
.stApp { background:var(--neutro) !important; color:var(--tinta) !important; }
.main .block-container { max-width:1100px; padding:2rem 2.5rem 4rem; }
.bloco { background:#fff; border-radius:18px; padding:2rem 2.2rem;
  box-shadow:0 10px 34px rgba(35,50,86,.10); margin-bottom:1.4rem; }
.hero { background:linear-gradient(120deg,var(--azul) 0%,var(--azul-escuro) 100%);
  border-radius:18px; padding:2.2rem; color:#fff; margin-bottom:1.4rem; position:relative; overflow:hidden; }
.hero::after { content:""; position:absolute; right:-60px; top:-60px; width:220px; height:220px;
  border-radius:50%; background:radial-gradient(circle, rgba(236,106,136,.45) 0%, transparent 70%); }
.hero h1 { color:#fff; font-weight:900; margin:0; font-size:1.6rem; }
.hero p { margin:.3rem 0 0; opacity:.85; }
.posicao-card { text-align:center; background:#fff; border-radius:24px; padding:2.4rem 2rem;
  border-top:8px solid var(--rosa); box-shadow:0 14px 40px rgba(35,50,86,.12); margin-bottom:1.4rem; }
.posicao-card .rotulo { color:var(--azul); font-weight:700; text-transform:uppercase; letter-spacing:2px; }
.posicao-card .num { font-size:5.8rem; font-weight:900; line-height:1; margin:.2rem 0;
  background:linear-gradient(145deg,var(--magenta),#f55078);
  -webkit-background-clip:text; background-clip:text; color:transparent; }
.aviso { background:#fff; border-left:5px solid var(--rosa); padding:1.1rem 1.4rem;
  border-radius:12px; box-shadow:0 6px 18px rgba(35,50,86,.08); line-height:1.65; margin-bottom:1.2rem; font-size:.95rem; }
.stButton>button, .stForm button { background:var(--azul) !important; color:#fff !important;
  border:none !important; border-radius:10px !important; font-weight:600 !important;
  padding:.55rem 1.4rem !important; box-shadow:0 4px 14px rgba(52,74,128,.25) !important; transition:all .2s ease !important; }
.stButton>button:hover, .stForm button:hover { background:var(--rosa) !important; transform:translateY(-2px); }
input, .stTextInput input { border-radius:10px !important; }
footer { visibility:hidden; }
[data-testid="stMetricValue"] { color:var(--azul); font-family:'Montserrat',sans-serif; }
</style>
""", unsafe_allow_html=True)

# ================================================================
# UTILITÁRIOS
# ================================================================
def DIG(v):
    return "".join(c for c in str(v or "") if c.isdigit())


def SAN(v):
    return html.escape(str(v if v not in (None, "") else "—"))


def validar_cpf(cpf_d):
    """Aceita qualquer CPF com 11 dígitos — a autenticação de fato
    acontece na comparação com a planilha de cadastro."""
    return len(cpf_d) == 11 and cpf_d != cpf_d[0] * 11


def confere_senha(senha, hash_alvo):
    try:
        return bcrypt.checkpw(senha.encode(), str(hash_alvo).strip().encode())
    except (ValueError, TypeError):
        return False


def hash_senha(senha):
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
# ESCRITA NA PLANILHA (conta de serviço)
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
            if "\\n" in str(dados.get("private_key", "")):
                dados["private_key"] = dados["private_key"].replace("\\n", "\n")
            GC = gspread.service_account_from_dict(dados)
        except Exception:
            GC = None
    return GC


def gravar_senha_hash(cpf_d, hash_val):
    """Grava o hash na planilha de gestores (A=Nome, B=CPF, C=Email, D=Senha_Hash)."""
    gc = cliente_gdrive()
    if gc is None:
        return False
    try:
        ws = gc.open_by_key(SHEET_CAD).worksheet(ABA_CAD)
        valores = ws.get_all_values()
        if not valores:
            return False
        primeira = [str(c).lower() if c else "" for c in valores[0]]
        tem_header = any(("cpf" in c) or ("nome" in c) for c in primeira)
        if tem_header:
            idx_cpf = primeira.index("cpf") if "cpf" in primeira else 1
            col_hash = (primeira.index("senha_hash") + 1) if "senha_hash" in primeira else None
            if col_hash is None:
                col_hash = len(primeira) + 1
                ws.update_cell(1, col_hash, "Senha_Hash")
            start = 2
        else:
            idx_cpf, col_hash, start = 1, 4, 1  # coluna B = CPF, coluna D = Senha_Hash
        for i in range(start, len(valores) + 1):
            linha = valores[i - 1]
            if len(linha) > idx_cpf and DIG(linha[idx_cpf]) == cpf_d:
                ws.update_cell(i, col_hash, hash_val)
                return True
        return False
    except Exception:
        return False


def enviar_email(destino, assunto, corpo):
    smtp_user = st.secrets.get("SMTP_EMAIL")
    smtp_pass = st.secrets.get("SMTP_APP_PASSWORD")
    if not (smtp_user and smtp_pass):
        return False
    try:
        msg = MIMEText(corpo, "plain", "utf-8")
        msg["Subject"], msg["From"], msg["To"] = assunto, smtp_user, destino
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as s:
            s.login(str(smtp_user), str(smtp_pass))
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
    # --- Fila HEC (tem cabeçalho) ---
    try:
        fila = pd.read_csv(u.format(SHEET_FILA, ABA_FILA), dtype=str)
        fila.columns = [c.strip() for c in fila.columns]
    except Exception:
        fila = pd.DataFrame()
    if not fila.empty and {"Nome_Paciente", "CPF", "Cartao_SUS"}.issubset(fila.columns):
        fila = fila[fila["Nome_Paciente"].notna() & (fila["Nome_Paciente"].str.strip() != "")]
        fila = fila[fila["CPF"].notna() & (fila["CPF"].str.strip() != "")].copy()
        fila["CPF_DIG"] = fila["CPF"].apply(DIG)
        fila["SUS_DIG"] = fila["Cartao_SUS"].apply(DIG)
        fila["Data"] = pd.to_datetime(fila.get("Data_Cadastro_AIH"), dayfirst=True, errors="coerce")
        fila = fila.sort_values("Data").reset_index(drop=True)

    # --- Gestores (SEM cabeçalho: linha 1 já é dado) ---
    try:
        cad_raw = pd.read_csv(u.format(SHEET_CAD, ABA_CAD), dtype=str, header=None)
    except Exception:
        cad_raw = pd.DataFrame()
    if cad_raw.empty:
        cad = pd.DataFrame(columns=["Nome", "CPF", "Email", "Senha_Hash"])
    else:
        primeira = [str(c).lower() if isinstance(c, str) else "" for c in cad_raw.iloc[0]]
        tem_header = any(("cpf" in c) or ("email" in c) for c in primeira)
        if tem_header:
            cad = cad_raw.iloc[1:].reset_index(drop=True)
            cad.columns = [str(c).strip() for c in cad_raw.iloc[0]]
        else:
            cad = cad_raw.copy()
            nomes = ["Nome", "CPF", "Email", "Senha_Hash"]
            if len(cad.columns) <= len(nomes):
                cad.columns = nomes[: len(cad.columns)]
            else:
                cad.columns = nomes + [f"Extra{i}" for i in range(len(cad.columns) - len(nomes))]
        cad = cad.dropna(how="all").reset_index(drop=True)
        cad["CPF_DIG"] = cad.get("CPF", pd.Series(dtype=str)).apply(DIG)
    return fila, cad

# ================================================================
# COMPONENTES
# ================================================================
def hero():
    st.markdown(
        '<div class="hero"><p style="font-size:.8rem;letter-spacing:3px;text-transform:uppercase;'
        'opacity:.7;">Hospital Estadual Central</p>'
        '<h1>Portal de Posição da Fila de Espera</h1>'
        '<p style="font-size:.95rem;">Consulte sua posição de forma segura — '
        '<b style="color:#ec6a88;">acolher e cuidar</b>.</p></div>',
        unsafe_allow_html=True,
    )

# ================================================================
# PACIENTE
# ================================================================
def tela_consulta():
    hero()
    st.markdown(
        '<div class="aviso"><b>Fila atualizada automaticamente a cada 30 segundos.</b><br>'
        "Informe seu CPF e o número do Cartão Nacional de Saúde para localizar seu registro. "
        "Nenhum dado pessoal é armazenado nesta consulta.</div>",
        unsafe_allow_html=True,
    )
    c_esq, c_dir = st.columns([1.1, 1])
    ok = False
    with c_esq:
        with st.form("consulta"):
            cpf = st.text_input("CPF", placeholder="000.000.000-00")
            sus = st.text_input("Cartão Nacional de Saúde (CNS)", placeholder="000 0000 0000 0000")
            ok = st.form_submit_button("Consultar Minha Posição", use_container_width=True)
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
    if len(cpf_d) != 11:
        st.error("Informe o CPF com 11 dígitos.")
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
        cor = lambda s: "✅" if str(s).strip().lower() == "concluído" else "⏳"
        st.markdown('<div class="bloco"><b>🩺 Exames e avaliações</b>'
                    f"<br>{cor(d['lab'])} Laboratoriais: <b>{d['lab']}</b>"
                    f"<br>{cor(d['img'])} Imagem: <b>{d['img']}</b>"
                    f"<br>{cor(d['car'])} Cardiológica: <b>{d['car']}</b>"
                    f"<br>{cor(d['pre'])} Pré-anestésica: <b>{d['pre']}</b></div>",
                    unsafe_allow_html=True)
    st.markdown(
        '<div class="aviso"><b>Acompanhe:</b> a posição pode mudar conforme chamadas, prioridades '
        "e desistências. Em caso de piora do quadro, procure o serviço de saúde mais próximo.</div>",
        unsafe_allow_html=True,
    )
    if st.button("⬅ Nova Consulta"):
        sai()
        st.rerun()

# ================================================================
# GESTOR
# ================================================================
def autenticar_gestor(cpf_d, senha):
    """Retorna (estado, linha). Estados: ok | temp | padrao | erro | erro_base."""
    _, cad = carregar()
    if cad.empty or "CPF_DIG" not in cad.columns:
        return "erro_base", None
    matches = cad[cad["CPF_DIG"] == cpf_d]
    if matches.empty:
        return "erro", None
    l = matches.iloc[0]
    col_hash = next((c for c in cad.columns if "senha_hash" in str(c).lower()), None)
    hash_alvo = str(l.get(col_hash) or "").strip() if col_hash else ""
    padrao = str(st.secrets.get("SENHA_INICIAL_HASH", "")).strip()

    if hash_alvo:
        if hash_alvo.startswith("TMP$"):
            if confere_senha(senha, hash_alvo[4:]):
                return "temp", l
            return "erro", None
        if confere_senha(senha, hash_alvo):
            return "ok", l
        return "erro", None
    if padrao and confere_senha(senha, padrao):
        return "padrao", l
    return "erro", None


def tela_login_gestor():
    hero()
    ok, esqueci = False, False
    bloqueado = time.time() < st.session_state.get("bloq", 0)
    c_esq, _ = st.columns([1.1, 1])
    with c_esq:
        st.markdown('<div class="bloco"><h3 style="color:#344a80;margin:0 0 .5rem;">🔐 Acesso do Gestor</h3>'
                    "Informe seu CPF e senha para visualizar a fila completa.</div>",
                    unsafe_allow_html=True)
        if bloqueado:
            st.error(f"Muitas tentativas. Aguarde {int(st.session_state['bloq'] - time.time())} segundos.")
        with st.form("login"):
            g_cpf = st.text_input("CPF", placeholder="000.000.000-00")
            g_senha = st.text_input("Senha", type="password")
            ok = st.form_submit_button("Entrar", use_container_width=True)
        esqueci = st.button("Esqueci minha senha")
        if st.button("← Voltar ao portal"):
            st.session_state.pop("tela_gestor", None)
            st.rerun()
    if not (ok or esqueci):
        return
    if bloqueado:
        return
    cpf_d = DIG(g_cpf)
    if len(cpf_d) != 11:
        st.error("Informe o CPF com 11 dígitos.")
        return
    _, cad = carregar()
    linha_cad = cad[cad.get("CPF_DIG", pd.Series(dtype=str)) == cpf_d] if "CPF_DIG" in cad.columns else pd.DataFrame()
    email = str(linha_cad.iloc[0].get("Email", "")).strip() if not linha_cad.empty else ""

    if esqueci:
        if cliente_gdrive() is None:
            st.error("Redefinição indisponível — peça à TI uma nova senha temporária.")
            return
        if linha_cad.empty or not email:
            st.warning("Se este CPF estiver cadastrado, você receberá um e-mail em instantes.")
            return
        nova = "".join(random.choices(string.ascii_letters + string.digits, k=10)) + "!Hc"
        if gravar_senha_hash(cpf_d, "TMP$" + hash_senha(nova)) and \
           enviar_email(email, "Portal HEC — senha temporária",
                        f"Olá!\n\nSua senha temporária de acesso ao Portal HEC é:\n\n{nova}\n\n"
                        "Ao entrar com ela, você deverá criar uma nova senha pessoal.\n\n"
                        "Se você não solicitou isso, ignore esta mensagem."):
            st.success("E-mail com senha temporária enviado para o endereço cadastrado.")
        else:
            st.error("Não foi possível enviar agora. Tente novamente em instantes.")
        return

    estado, l = autenticar_gestor(cpf_d, g_senha)
    if estado == "erro_base":
        st.error("Base de gestores indisponível. Verifique os Secrets e o compartilhamento da planilha.")
        return
    if estado == "erro":
        falha_login()
        st.error("CPF ou senha incorretos.")
        return
    st.session_state["gestor"] = {
        "nome": SAN(l.get("Nome")),
        "cpf": cpf_d,
        "forcar_troca": estado != "ok",
    }
    st.session_state["tent"] = 0
    st.rerun()


def tela_troca_senha():
    g = st.session_state["gestor"]
    hero()
    st.markdown('<div class="bloco"><h3 style="color:#344a80;margin:0 0 .5rem;">🔑 Defina a sua senha</h3>'
                "Por segurança, no primeiro acesso (ou após uma redefinição) você deve cadastrar "
                "uma senha pessoal com no mínimo 8 caracteres.</div>",
                unsafe_allow_html=True)
    with st.form("troca"):
        n1 = st.text_input("Nova senha", type="password")
        n2 = st.text_input("Confirmar nova senha", type="password")
        ok = st.form_submit_button("Salvar senha", use_container_width=True)
    if not ok:
        return
    if n1 != n2:
        st.error("As senhas não são iguais.")
        return
    if len(n1) < 8:
        st.error("A senha deve ter ao menos 8 caracteres.")
        return
    if gravar_senha_hash(g["cpf"], hash_senha(n1)):
        g["forcar_troca"] = False
        st.success("Senha definida com sucesso!")
        st.rerun()
    else:
        st.warning("Não foi possível gravar na base agora — a senha vale apenas nesta sessão. "
                   "Avise a TI para verificar o compartilhamento da planilha com a conta de serviço.")
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
        pend = lambda col: int(fila.get(col, pd.Series(dtype=str)).astype(str).str.strip().eq("Pendente").sum())
        c1, c2, c3, c4 = st.columns(4)
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
    c1, _ = st.columns([1, 4])
    with c1:
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
