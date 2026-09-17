import streamlit as st
import pandas as pd
import hashlib

# Configuração da Página
st.set_page_config(
    page_title="Fila Cirúrgica | HEC & Inova Capixaba",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
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
if "paciente_logado" not in st.session_state:
    st.session_state.paciente_logado = False
if "dados_paciente" not in st.session_state:
    st.session_state.dados_paciente = None
if "modo_gestor" not in st.session_state:
    st.session_state.modo_gestor = False

# Estilização Avançada (Fundo com Contraste e UI Limpa)
st.markdown("""
    <style>
        /* Fundo com contraste elegante (Cinza Ardósia Claro) para destacar os cartões brancos */
        .stApp { background-color: #E2E8F0; color: #1E293B; }
        
        /* Botão Superior Direito Discreto para Gestores */
        .btn-gestor>button {
            background-color: transparent !important;
            color: #64748B !important;
            border: 1px solid #CBD5E1 !important;
            border-radius: 20px !important;
            padding: 0.3rem 1rem !important;
            font-size: 0.85rem !important;
            font-weight: 600 !important;
            float: right;
            box-shadow: none !important;
        }
        .btn-gestor>button:hover {
            background-color: #CBD5E1 !important;
            color: #1E293B !important;
        }

        /* Botões de Ação Principais (Inova Magenta) */
        .stButton>button {
            background-color: #D91A60 !important;
            color: #FFFFFF !important;
            border-radius: 8px !important;
            border: none !important;
            font-weight: 700 !important;
            font-size: 1.1rem !important;
            padding: 0.6rem 1.2rem !important;
            box-shadow: 0 4px 10px rgba(217, 26, 96, 0.3) !important;
            transition: all 0.2s ease-in-out;
            width: 100%;
        }
        .stButton>button:hover {
            background-color: #B81550 !important;
            box-shadow: 0 6px 15px rgba(217, 26, 96, 0.4) !important;
            transform: translateY(-2px);
        }

        /* Cartões Flutuantes Brancos (Alto Contraste com o Fundo) */
        .glass-card {
            background: #FFFFFF;
            padding: 35px;
            border-radius: 16px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.08);
            border: 1px solid #FFFFFF;
            margin-bottom: 20px;
        }

        /* Destaque Gigante para Posição */
        .highlight-queue {
            text-align: center;
            background: linear-gradient(145deg, #ffffff, #F8FAFC);
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
            border-left: 5px solid #17274D;
            padding: 20px 25px;
            font-size: 1.05rem;
            color: #1E293B !important;
            border-radius: 8px;
            margin-bottom: 30px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.05);
            line-height: 1.6;
        }
        
        /* Oculta marca d'água do Streamlit */
        footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# CABEÇALHO SUPERIOR (Logos e Botão de Acesso)
# ---------------------------------------------------------
col_logo, col_vazio, col_btn_gestor = st.columns([2, 5, 2])
with col_logo:
    try:
        st.image("logo-inova-cor_2.jpg", width=160)
    except:
        st.markdown("### 🏥 **HEC | INOVA**")

with col_btn_gestor:
    st.markdown("<div class='btn-gestor'>", unsafe_allow_html=True)
    if st.session_state.autenticado:
        if st.button("Sair (Logout)"):
            st.session_state.autenticado = False
            st.session_state.usuario_logado = None
            st.session_state.modo_gestor = False
            st.rerun()
    else:
        rotulo_botao = "⬅ Voltar ao Portal" if st.session_state.modo_gestor else "🔒 Acesso Gestor"
        if st.button(rotulo_botao):
            st.session_state.modo_gestor = not st.session_state.modo_gestor
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Funções Utilitárias
def criptografar_dado(texto):
    return hashlib.sha256(str(texto).encode()).hexdigest()

def padronizar_cpf(cpf_str):
    return "".join(filter(str.isdigit, str(cpf_str))).zfill(11)

# Leitura Simulada de Dados (Com Inclusão do CID)
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
        "CID": ["C71.9", "M51.1"], # Adição da Coluna CID
        "Status_Exames_Lab": ["Concluído", "Concluído"],
        "Status_Exames_Imagem": ["Concluído", "Pendente"],
        "Status_Avaliacao_Cardio": ["Concluído", "Concluído"],
        "Status_Avaliacao_PreAnestesica": ["Concluído", "Pendente"],
        "Escore_Prioridade": [135.0, 45.0] # Escore elevado artificialmente para a paciente oncológica
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


# ---------------------------------------------------------
# MÓDULO 1: PORTAL DO PACIENTE (Modo Padrão)
# ---------------------------------------------------------
if not st.session_state.modo_gestor:
    
    # TELA 1: AUTENTICAÇÃO DO PACIENTE
    if not st.session_state.paciente_logado:
        col_texto, col_form = st.columns([1.2, 1], gap="large")
        
        with col_texto:
            st.markdown("<h1 style='color: #0A2540; font-size: 3rem; font-weight: 800; line-height: 1.1;'>Transparência total<br>na sua espera.</h1>", unsafe_allow_html=True)
            st.markdown("<p style='font-size: 1.15rem; color: #475569; margin-top: 15px;'>Consulte em tempo real a sua posição e pendências para cirurgias eletivas no Hospital Estadual Central.</p>", unsafe_allow_html=True)
            
            st.markdown("""
                <div class='legal-notice'>
                    <strong>Priorização Técnica no SUS:</strong><br><br>
                    O agendamento cirúrgico não segue apenas a ordem de chegada. Ele prioriza a gravidade da doença (ex: <strong>diagnósticos oncológicos</strong> possuem peso adicional), riscos clínicos e a <strong>conclusão de todos os exames pré-operatórios</strong>.
                </div>
            """, unsafe_allow_html=True)
    
        with col_form:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.markdown("<h3 style='color: #0A2540; margin-bottom: 20px;'>Autenticação do Paciente</h3>", unsafe_allow_html=True)
            pac_nome = st.text_input("Nome Completo:")
            pac_cpf = st.text_input("CPF (com pontuação, ex: 111.222.333-44):")
            pac_cns = st.text_input("Nº Cartão SUS (CNS):")
            
            st.write("")
            if st.button("Consultar Posição ➔"):
                if pac_nome and pac_cpf and pac_cns:
                    match_paciente = df_fila[
                        (df_fila["Nome_Paciente"].str.strip().str.lower() == pac_nome.strip().lower()) &
                        (df_fila["CPF"].str.strip() == pac_cpf.strip()) &
                        (df_fila["Cartao_SUS"].str.strip() == pac_cns.strip())
                    ]
                    
                    if not match_paciente.empty:
                        st.session_state.paciente_logado = True
                        st.session_state.dados_paciente = match_paciente.iloc[0].to_dict()
                        st.rerun()
                    else:
                        st.error("Dados não encontrados. Verifique a digitação.")
                else:
                    st.warning("Preencha todos os campos.")
            st.markdown("</div>", unsafe_allow_html=True)

    # TELA 2: RESULTADO E POSIÇÃO
    else:
        p = st.session_state.dados_paciente
        
        st.markdown(f"""
            <div class='highlight-queue'>
                <h3>Sua Posição Atual na Fila</h3>
                <h1>{int(p['Posicao_Fila'])}º</h1>
                <h2>{p['Especialidade']}</h2>
                <p style='color: #64748B; margin-top: 10px;'>Protocolo AIH: <strong>{p['Numero_AIH']}</strong> | CID Cadastrado: <strong>{p.get('CID', 'Não informado')}</strong></p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<h4 style='color: #0A2540; margin-bottom: 20px;'>Checklist do Preparo Cirúrgico</h4>", unsafe_allow_html=True)
        e1, e2, e3, e4 = st.columns(4)
        
        if p['Status_Exames_Lab'] == 'Concluído': e1.success("Exames Lab: Concluído")
        else: e1.error("Exames Lab: Pendente")
            
        if p['Status_Exames_Imagem'] == 'Concluído': e2.success("Imagem: Concluído")
        else: e2.error("Imagem: Pendente")
            
        if p['Status_Avaliacao_Cardio'] == 'Concluído': e3.success("Cardiologia: Concluído")
        else: e3.error("Cardiologia: Pendente")
            
        if p['Status_Avaliacao_PreAnestesica'] == 'Concluído': e4.success("Pré-Anestésica: Concluído")
        else: e4.error("Pré-Anestésica: Pendente")
        st.markdown("</div>", unsafe_allow_html=True)
            
        if st.button("⬅ Nova Consulta"):
            st.session_state.paciente_logado = False
            st.session_state.dados_paciente = None
            st.rerun()


# ---------------------------------------------------------
# MÓDULO 2: PAINEL ADMINISTRATIVO (Modo Gestor)
# ---------------------------------------------------------
else:
    if not st.session_state.autenticado:
        col_esp, col_login, col_esp2 = st.columns([1.5, 2, 1.5])
        with col_login:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.markdown("<h3 style='color: #0A2540; text-align: center; margin-bottom: 25px;'>Painel Institucional</h3>", unsafe_allow_html=True)
            adm_cpf = st.text_input("CPF do Gestor (Apenas números):")
            adm_senha = st.text_input("Senha:", type="password")
            
            st.write("")
            if st.button("Autenticar"):
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
                        st.error("CPF não autorizado na base administrativa.")
                else:
                    st.warning("Preencha CPF e Senha.")
            st.markdown("</div>", unsafe_allow_html=True)

    else:
        usuario = st.session_state.usuario_logado
        cpf_k = usuario["CPF"]
        pendente = st.session_state.banco_primeiro_acesso.get(cpf_k, usuario["Primeiro_Acesso_Original"])
        
        if pendente:
            col_esp, col_form, col_esp2 = st.columns([1, 2, 1])
            with col_form:
                st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
                st.warning("Troca de senha obrigatória no primeiro acesso.")
                n_senha = st.text_input("Nova Senha (Mín. 6 caracteres):", type="password")
                c_senha = st.text_input("Confirmar Senha:", type="password")
                
                st.write("")
                if st.button("Salvar e Acessar"):
                    if len(n_senha) >= 6 and n_senha == c_senha and n_senha != "123":
                        st.session_state.banco_senhas_customizadas[cpf_k] = criptografar_dado(n_senha)
                        st.session_state.banco_primeiro_acesso[cpf_k] = False
                        st.success("Credencial validada!")
                        st.rerun()
                    else:
                        st.error("As senhas são inválidas ou não conferem.")
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<h3 style='color: #0A2540; margin-bottom: 20px;'>Governança Cirúrgica | Olá, {usuario['Nome']}</h3>", unsafe_allow_html=True)
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            f_esp = st.selectbox("Filtrar Fila Eletiva por Especialidade:", ["Todas as Especialidades"] + list(df_fila["Especialidade"].unique()))
            df_view = df_fila if f_esp == "Todas as Especialidades" else df_fila[df_fila["Especialidade"] == f_esp]
            
            st.dataframe(df_view, use_container_width=True, hide_index=True)
            st.markdown("</div>", unsafe_allow_html=True)
