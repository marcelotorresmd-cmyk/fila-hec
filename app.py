import streamlit as st
import pandas as pd
import hashlib

# Configuração da Página
st.set_page_config(
    page_title="Fila Cirúrgica | HEC & Inova Capixaba",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Gerenciamento de Estado (Persistência)
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "usuario_logado" not in st.session_state:
    st.session_state.usuario_logado = None
if "banco_senhas_customizadas" not in st.session_state:
    st.session_state.banco_senhas_customizadas = {}
if "banco_primeiro_acesso" not in st.session_state:
    st.session_state.banco_primeiro_acesso = {}

# Estilização Avançada (UI/UX - Padrão Inova / Referências de Mercado)
st.markdown("""
    <style>
        /* Fundo limpo e textos escuros de alto contraste */
        .stApp { background-color: #F4F7F9; color: #1E293B; }
        
        /* Cabeçalho Inova Capixaba (Azul Marinho) */
        .top-navbar {
            background-color: #17274D;
            padding: 15px 30px;
            border-radius: 0 0 12px 12px;
            margin-top: -60px;
            margin-bottom: 40px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        .top-navbar h2 { color: #FFFFFF; margin: 0; font-size: 1.4rem; font-weight: 600; }
        .top-navbar span { color: #D91A60; font-weight: 800; }
        
        /* Botões padronizados e com contraste corrigido */
        .stButton>button {
            background-color: #D91A60 !important;
            color: #FFFFFF !important;
            border-radius: 8px !important;
            border: none !important;
            font-weight: 700 !important;
            font-size: 1.1rem !important;
            padding: 0.6rem 1.2rem !important;
            box-shadow: 0 4px 10px rgba(217, 26, 96, 0.3) !important;
            transition: all 0.2s ease-in-out !important;
            width: 100%;
        }
        .stButton>button:hover {
            background-color: #B81550 !important;
            box-shadow: 0 6px 15px rgba(217, 26, 96, 0.4) !important;
            transform: translateY(-2px) !important;
        }

        /* Cartões de Layout (Formulários e Resultados) */
        .glass-card {
            background: #FFFFFF;
            padding: 35px;
            border-radius: 16px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.06);
            border: 1px solid #E2E8F0;
        }

        /* Destaque Gigante para a Posição do Paciente */
        .highlight-queue {
            text-align: center;
            background: linear-gradient(145deg, #ffffff, #f0f4f8);
            border-radius: 20px;
            padding: 40px 20px;
            border: 2px solid #E2E8F0;
            box-shadow: inset 0 2px 10px rgba(0,0,0,0.02), 0 10px 25px rgba(0,0,0,0.08);
            margin-bottom: 30px;
        }
        .highlight-queue h3 { color: #64748B; margin-bottom: 5px; font-size: 1.2rem; text-transform: uppercase; letter-spacing: 1px; }
        .highlight-queue h1 { font-size: 6rem; color: #D91A60; margin: 0; font-weight: 900; line-height: 1; }
        .highlight-queue h2 { color: #17274D; font-size: 1.8rem; margin-top: 15px; }

        /* Aviso Legal Minimalista */
        .legal-notice {
            background-color: #EFF6FF;
            border-left: 4px solid #17274D;
            padding: 15px 20px;
            font-size: 0.9rem;
            color: #334155 !important;
            border-radius: 6px;
            margin-bottom: 25px;
        }
    </style>
""", unsafe_allow_html=True)

# Navbar Customizada Superior
st.markdown("""
    <div class='top-navbar'>
        <h2>HEC <span>|</span> GESTÃO DE FILAS</h2>
        <h2 style='font-size: 1.1rem; color: #A0AABF;'>Transparência SUS</h2>
    </div>
""", unsafe_allow_html=True)

# Imagem da Inova centralizada caso não consiga embutir no HTML
col_logo_space, col_logo_img, col_logo_space2 = st.columns([4, 2, 4])
with col_logo_img:
    try:
        st.image("logo-inova-cor_2.jpg", use_column_width=True)
    except:
        pass

# Funções Utilitárias
def criptografar_dado(texto):
    return hashlib.sha256(str(texto).encode()).hexdigest()

def padronizar_cpf(cpf_str):
    return "".join(filter(str.isdigit, str(cpf_str))).zfill(11)

# Leitura Simulada de Dados
@st.cache_data(ttl=30)
def carregar_bases():
    data_fila = {
        "ID_Registro": ["REG-001", "REG-002"],
        "Data_Cadastro_AIH": ["2026-01-15", "2026-02-10"],
        "Nome_Paciente": ["Maria Oliveira Santos", "João Pereira da Silva"],
        "Cartao_SUS": ["123456789012345", "987654321098765"],
        "CPF": ["111.222.333-44", "222.333.444-55"],
        "Data_Nascimento": ["1965-04-12", "1980-09-25"],
        "Especialidade": ["Neurocirurgia", "Ortopedia"],
        "Numero_AIH": ["AIH-987654", "AIH-123456"],
        "Status_Exames_Lab": ["Concluído", "Concluído"],
        "Status_Exames_Imagem": ["Concluído", "Pendente"],
        "Status_Avaliacao_Cardio": ["Concluído", "Concluído"],
        "Status_Avaliacao_PreAnestesica": ["Concluído", "Pendente"],
        "Escore_Prioridade": [85.0, 45.0]
    }
    df_f = pd.DataFrame(data_fila)
    
    try:
        df_cad = pd.read_excel("Cadastro.xlsx", header=None)
        df_gestores = pd.DataFrame({
            "Nome": df_cad[0].astype(str).str.strip(),
            "CPF": df_cad[1].apply(padronizar_cpf),
            "Email": df_cad[2].astype(str).str.strip(),
            "Senha_Original": [criptografar_dado("123")] * len(df_cad),
            "Primeiro_Acesso_Original": [True] * len(df_cad)
        })
    except:
        df_gestores = pd.DataFrame({
            "Nome": ["Dr. Marcelo Torres"],
            "CPF": [padronizar_cpf("09021165767")],
            "Email": ["marcelotorres.md@gmail.com"],
            "Senha_Original": [criptografar_dado("123")],
            "Primeiro_Acesso_Original": [True]
        })
    return df_f, df_gestores

df_fila, df_gestores = carregar_bases()
if "Escore_Prioridade" in df_fila.columns:
    df_fila = df_fila.sort_values(by="Escore_Prioridade", ascending=False).reset_index(drop=True)
    df_fila["Posicao_Fila"] = df_fila.index + 1

# Navegação Lateral
if st.session_state.autenticado:
    st.sidebar.success(f"Gestor: {st.session_state.usuario_logado['Nome']}")
    if st.sidebar.button("Encerrar Sessão (Logout)"):
        st.session_state.autenticado = False
        st.session_state.usuario_logado = None
        st.rerun()
    perfil_escolhido = "Painel Administrativo"
else:
    st.sidebar.markdown("### Acesso ao Sistema")
    perfil_escolhido = st.sidebar.radio("", ["Portal do Paciente", "Painel Administrativo"])

st.markdown("---")

# ---------------------------------------------------------
# MÓDULO 1: PORTAL DO PACIENTE (Hero Layout)
# ---------------------------------------------------------
if perfil_escolhido == "Portal do Paciente":
    # Divisão em duas colunas inspirada em sites modernos (ex: Filazero)
    col_texto, col_form = st.columns([1.2, 1], gap="large")
    
    with col_texto:
        st.markdown("<h1 style='color: #17274D; font-size: 2.8rem; font-weight: 800; line-height: 1.1;'>Sua transparência<br>na fila de espera.</h1>", unsafe_allow_html=True)
        st.markdown("<p style='font-size: 1.1rem; color: #475569; margin-top: 15px;'>Acompanhe em tempo real a sua posição para cirurgias eletivas no Hospital Estadual Central.</p>", unsafe_allow_html=True)
        
        st.markdown("""
            <div class='legal-notice'>
                <strong>Critérios de Priorização (SUS):</strong><br>
                A fila não é exclusivamente cronológica. Nossa regulação avalia a gravidade, vulnerabilidade e a <strong>conclusão completa dos seus exames pré-operatórios</strong> para garantir equidade.
            </div>
        """, unsafe_allow_html=True)

    with col_form:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color: #17274D; margin-bottom: 20px;'>Acesse seus dados</h3>", unsafe_allow_html=True)
        pac_nome = st.text_input("Nome Completo:")
        pac_cpf = st.text_input("CPF (com pontuação):")
        pac_cns = st.text_input("Nº Cartão SUS (CNS):")
        
        st.write("")
        if st.button("Ver Minha Posição ➔"):
            if pac_nome and pac_cpf and pac_cns:
                match_paciente = df_fila[
                    (df_fila["Nome_Paciente"].str.strip().str.lower() == pac_nome.strip().lower()) &
                    (df_fila["CPF"].str.strip() == pac_cpf.strip()) &
                    (df_fila["Cartao_SUS"].str.strip() == pac_cns.strip())
                ]
                
                if not match_paciente.empty:
                    p = match_paciente.iloc[0]
                    # Exibição de Destaque Absoluto (Número Gigante)
                    st.markdown(f"""
                        <div class='highlight-queue'>
                            <h3>Sua Posição Atual</h3>
                            <h1>{int(p['Posicao_Fila'])}º</h1>
                            <h2>{p['Especialidade']}</h2>
                            <p style='color: #64748B; margin-top: 10px;'>AIH: {p['Numero_AIH']}</p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("#### Status do Preparo Cirúrgico:")
                    e1, e2, e3, e4 = st.columns(4)
                    e1.success(f"Exames Lab: {p['Status_Exames_Lab']}") if p['Status_Exames_Lab'] == 'Concluído' else e1.error(f"Exames Lab: Pendente")
                    e2.success(f"Imagem: {p['Status_Exames_Imagem']}") if p['Status_Exames_Imagem'] == 'Concluído' else e2.error(f"Imagem: Pendente")
                    e3.success(f"Cardiologia: {p['Status_Avaliacao_Cardio']}") if p['Status_Avaliacao_Cardio'] == 'Concluído' else e3.error(f"Cardiologia: Pendente")
                    e4.success(f"Pré-Anestésica: {p['Status_Avaliacao_PreAnestesica']}") if p['Status_Avaliacao_PreAnestesica'] == 'Concluído' else e4.error(f"Pré-Anestésica: Pendente")
                else:
                    st.error("Dados incorretos. Utilize as credenciais de teste para visualizar.")
            else:
                st.warning("Preencha todos os campos obrigatórios.")
        st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------
# MÓDULO 2: PAINEL ADMINISTRATIVO (Gestão)
# ---------------------------------------------------------
elif perfil_escolhido == "Painel Administrativo":
    
    if not st.session_state.autenticado:
        col_esp, col_login, col_esp2 = st.columns([1, 1.5, 1])
        with col_login:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.markdown("<h3 style='color: #17274D; text-align: center; margin-bottom: 25px;'>Acesso Restrito</h3>", unsafe_allow_html=True)
            adm_cpf = st.text_input("CPF do Gestor:")
            adm_senha = st.text_input("Senha:", type="password")
            
            st.write("")
            if st.button("Entrar no Sistema"):
                if adm_cpf and adm_senha:
                    cpf_norm = padronizar_cpf(adm_cpf)
                    match_gest = df_gestores[df_gestores["CPF"] == cpf_norm]
                    
                    if not match_gest.empty:
                        g_row = match_gest.iloc[0]
                        cpf_k = g_row["CPF"]
                        senha_ativa = st.session_state.banco_senhas_customizadas.get(cpf_k, g_row["Senha_Original"])
                        
                        if criptografar_dado(adm_senha) == senha_ativa:
                            st.session_state.autenticado = True
                            st.session_state.usuario_logado = g_row.to_dict()
                            st.rerun()
                        else:
                            st.error("Credenciais inválidas.")
                    else:
                        st.error("CPF não autorizado.")
                else:
                    st.warning("Preencha CPF e Senha.")
            st.markdown("</div>", unsafe_allow_html=True)

    else:
        # Área Logada
        usuario = st.session_state.usuario_logado
        cpf_k = usuario["CPF"]
        pendente = st.session_state.banco_primeiro_acesso.get(cpf_k, usuario["Primeiro_Acesso_Original"])
        
        if pendente:
            st.warning("Troca de senha obrigatória no primeiro acesso.")
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            n_senha = st.text_input("Nova Senha:", type="password")
            c_senha = st.text_input("Confirmar Senha:", type="password")
            if st.button("Atualizar"):
                if len(n_senha) >= 6 and n_senha == c_senha and n_senha != "123":
                    st.session_state.banco_senhas_customizadas[cpf_k] = criptografar_dado(n_senha)
                    st.session_state.banco_primeiro_acesso[cpf_k] = False
                    st.success("Senha atualizada!")
                    st.rerun()
                else:
                    st.error("Senha inválida ou incompatível.")
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<h3 style='color: #17274D;'>Painel de Regulação - {usuario['Nome']}</h3>", unsafe_allow_html=True)
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            f_esp = st.selectbox("Especialidade:", ["Todas"] + list(df_fila["Especialidade"].unique()))
            df_view = df_fila if f_esp == "Todas" else df_fila[df_fila["Especialidade"] == f_esp]
            st.dataframe(df_view, use_container_width=True, hide_index=True)
            st.markdown("</div>", unsafe_allow_html=True)
