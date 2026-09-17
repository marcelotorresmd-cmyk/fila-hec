import streamlit as st
import pandas as pd
import hashlib

# Configuração da Página
st.set_page_config(
    page_title="Gestão de Fila Cirúrgica | HEC & Inova Capixaba",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicialização Persistente de Estados de Sessão (Correção do Fluxo de Login)
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "usuario_logado" not in st.session_state:
    st.session_state.usuario_logado = None
if "banco_senhas_customizadas" not in st.session_state:
    st.session_state.banco_senhas_customizadas = {}
if "banco_primeiro_acesso" not in st.session_state:
    st.session_state.banco_primeiro_acesso = {}

# Estilização Avançada (UI/UX - Light Corporate / Clinical Theme)
st.markdown("""
    <style>
        /* Fundo Geral Claro para Alto Contraste e Legibilidade */
        .stApp {
            background-color: #F8FAFC;
            color: #1E293B;
        }
        /* Textos padrão forçados para cor escura para garantir leitura */
        h1, h2, h3, h4, h5, h6, p, span, div {
            color: #0F172A;
        }
        /* Cabeçalho Branco com Sombra Suave e Borda Superior com as cores da Inova */
        .main-header {
            background: #FFFFFF;
            padding: 30px;
            border-radius: 12px;
            text-align: center;
            margin-bottom: 30px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
            border-top: 5px solid #D91A60;
        }
        .main-title {
            font-size: 2.2rem;
            font-weight: 800;
            color: #0A2540 !important;
            letter-spacing: -0.5px;
            margin-bottom: 5px;
        }
        .sub-header {
            font-size: 1.15rem;
            color: #64748B !important;
            font-weight: 500;
        }
        /* Botões Executivos (Azul e Magenta) */
        .stButton>button {
            background: #0A2540;
            color: #FFFFFF !important;
            border-radius: 8px;
            border: none;
            font-weight: 600;
            padding: 0.6rem 1.2rem;
            box-shadow: 0 4px 10px rgba(10, 37, 64, 0.2);
            transition: all 0.3s ease;
            width: 100%;
        }
        .stButton>button:hover {
            background: #D91A60;
            color: #FFFFFF !important;
            box-shadow: 0 4px 15px rgba(217, 26, 96, 0.3);
            transform: translateY(-2px);
        }
        /* Aviso Institucional Estilizado */
        .legal-notice {
            background: #EFF6FF;
            border-left: 6px solid #1E3A8A;
            padding: 20px;
            font-size: 0.95rem;
            color: #1E293B !important;
            border-radius: 8px;
            margin-top: 10px;
            margin-bottom: 25px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.03);
        }
        /* Cartão de Fundo Branco para Formulários */
        .form-card {
            background-color: #FFFFFF;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05);
            border: 1px solid #E2E8F0;
        }
        /* Rodapé de Versão */
        .version-badge {
            position: fixed;
            bottom: 10px;
            right: 15px;
            background: #FFFFFF;
            color: #64748B !important;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.75rem;
            border: 1px solid #CBD5E1;
            z-index: 9999;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }
    </style>
""", unsafe_allow_html=True)

# Exibição da Versão do Sistema no Rodapé
st.markdown("<div class='version-badge'>Versão 3.0-PRO | HEC & Inova</div>", unsafe_allow_html=True)

# Cabeçalho Institucional Topo
col_logo1, col_center, col_logo2 = st.columns([1.5, 5, 1.5], gap="large")

with col_logo1:
    st.markdown("### 🏥 **HEC**")
    st.caption("Hospital Estadual Central")

with col_center:
    st.markdown("""
        <div class='main-header'>
            <div class='main-title'>Sistema Integrado de Equidade Cirúrgica</div>
            <div class='sub-header'>Diretoria Técnica | Gestão de Fila Ambulatorial (SUS)</div>
        </div>
    """, unsafe_allow_html=True)

with col_logo2:
    try:
        st.image("logo-inova-cor_2.jpg", width=160)
    except:
        st.markdown("### 💡 **INOVA**")

# Funções Utilitárias de Segurança e Normalização
def criptografar_dado(texto):
    return hashlib.sha256(str(texto).encode()).hexdigest()

def padronizar_cpf(cpf_str):
    apenas_digitos = "".join(filter(str.isdigit, str(cpf_str)))
    return apenas_digitos.zfill(11)

# Leitura Simulada de Dados (Fila e Cadastro.xlsx)
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
    except Exception as e:
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

# Menu Lateral (Bloqueado caso o gestor esteja logado para evitar perda de foco)
if st.session_state.autenticado:
    st.sidebar.success(f"Logado como: {st.session_state.usuario_logado['Nome']}")
    if st.sidebar.button("Sair (Logout)"):
        st.session_state.autenticado = False
        st.session_state.usuario_logado = None
        st.rerun()
    perfil_escolhido = "Painel Administrativo (Gestor)"
else:
    st.sidebar.markdown("### 🧭 Menu do Sistema")
    perfil_escolhido = st.sidebar.radio("Navegação:", ["Portal do Paciente", "Painel Administrativo (Gestor)"])

st.markdown("---")

# ---------------------------------------------------------
# MÓDULO 1: PORTAL DO PACIENTE
# ---------------------------------------------------------
if perfil_escolhido == "Portal do Paciente":
    st.markdown("### 👤 Área do Cidadão - Consulta de Posição")
    
    st.markdown("""
        <div class='legal-notice'>
            <strong>Aviso de Transparência Pública:</strong><br><br>
            A fila de espera do Sistema Único de Saúde (SUS) não obedece estritamente à ordem cronológica. 
            Em cumprimento aos princípios constitucionais e às diretrizes do SUS, a priorização é regida por <strong>critérios técnicos e de equidade clínica</strong>. 
            A classificação considera a gravidade do quadro, riscos associados, prioridades etárias e a <strong>conclusão integral do preparo pré-operatório</strong> 
            (exames e avaliações pré-anestésicas), garantindo justiça distributiva e segurança ao paciente.
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<div class='form-card'>", unsafe_allow_html=True)
    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        pac_nome = st.text_input("Nome Completo:")
    with col_p2:
        pac_cpf = st.text_input("CPF (Ex: 111.222.333-44):")
    with col_p3:
        pac_cns = st.text_input("Nº Cartão Nacional de Saúde (CNS):")
        
    st.write("") # Espaçamento
    if st.button("Consultar Situação na Fila"):
        if pac_nome and pac_cpf and pac_cns:
            match_paciente = df_fila[
                (df_fila["Nome_Paciente"].str.strip().str.lower() == pac_nome.strip().lower()) &
                (df_fila["CPF"].str.strip() == pac_cpf.strip()) &
                (df_fila["Cartao_SUS"].str.strip() == pac_cns.strip())
            ]
            
            if not match_paciente.empty:
                p = match_paciente.iloc[0]
                st.success("Autenticação validada com sucesso!")
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Posição na Fila", f"{int(p['Posicao_Fila'])}º Lugar")
                c2.metric("Especialidade", p["Especialidade"])
                c3.metric("Protocolo AIH", p["Numero_AIH"])
                
                st.markdown("#### Progresso do Preparo Clínico:")
                ex1, ex2, ex3, ex4 = st.columns(4)
                ex1.info(f"**Laboratório:** {p['Status_Exames_Lab']}")
                ex2.info(f"**Imagem:** {p['Status_Exames_Imagem']}")
                ex3.info(f"**Cardiologia:** {p['Status_Avaliacao_Cardio']}")
                ex4.info(f"**Pré-Anestésica:** {p['Status_Avaliacao_PreAnestesica']}")
            else:
                st.error("Dados não encontrados. Verifique a digitação exata do Nome, CPF e CNS.")
        else:
            st.warning("Preencha todas as credenciais de identificação.")
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------
# MÓDULO 2: PAINEL ADMINISTRATIVO (GESTOR)
# ---------------------------------------------------------
elif perfil_escolhido == "Painel Administrativo (Gestor)":
    
    # SE NÃO ESTIVER AUTENTICADO: MOSTRA TELA DE LOGIN
    if not st.session_state.autenticado:
        st.markdown("### 🔐 Acesso Administrativo Restrito")
        
        tab_login, tab_recuperar = st.tabs(["Credenciais de Acesso", "Recuperar Senha"])
        
        with tab_login:
            st.markdown("<div class='form-card'>", unsafe_allow_html=True)
            adm_cpf = st.text_input("CPF do Gestor:", placeholder="Apenas números")
            adm_senha = st.text_input("Senha:", type="password")
            
            st.write("")
            if st.button("Autenticar Usuário"):
                if adm_cpf and adm_senha:
                    adm_cpf_normalizado = padronizar_cpf(adm_cpf)
                    gestor_match = df_gestores[df_gestores["CPF"] == adm_cpf_normalizado]
                    
                    if not gestor_match.empty:
                        g_row = gestor_match.iloc[0]
                        cpf_key = g_row["CPF"]
                        
                        # Verifica em memória (sessão) se já atualizou a senha; senão usa a original ('123')
                        senha_valida_atual = st.session_state.banco_senhas_customizadas.get(cpf_key, g_row["Senha_Original"])
                        senha_input_hash = criptografar_dado(adm_senha)
                        
                        if senha_input_hash == senha_valida_atual:
                            # Login Efetuado com Sucesso! Atualiza o estado da sessão.
                            st.session_state.autenticado = True
                            st.session_state.usuario_logado = g_row.to_dict()
                            st.rerun() # Recarrega a página para entrar na área logada
                        else:
                            st.error("Senha administrativa incorreta.")
                    else:
                        st.error("Credencial de CPF não localizada na base de autoridades.")
                else:
                    st.warning("Informe o CPF e a Senha para prosseguir.")
            st.markdown("</div>", unsafe_allow_html=True)
            
        with tab_recuperar:
            st.markdown("<div class='form-card'>", unsafe_allow_html=True)
            email_rec = st.text_input("E-mail Institucional Vinculado:")
            if st.button("Solicitar Redefinição"):
                if email_rec:
                    st.success("Se o e-mail existir na base, um link seguro de redefinição será enviado pelo servidor.")
                else:
                    st.warning("Preencha o campo de e-mail.")
            st.markdown("</div>", unsafe_allow_html=True)

    # SE ESTIVER AUTENTICADO: AVALIA SE PRECISA TROCAR SENHA OU MOSTRA O PAINEL
    else:
        usuario = st.session_state.usuario_logado
        cpf_key = usuario["CPF"]
        
        # Verifica se o primeiro acesso ainda está pendente no estado da sessão
        primeiro_acesso_pendente = st.session_state.banco_primeiro_acesso.get(cpf_key, usuario["Primeiro_Acesso_Original"])
        
        if primeiro_acesso_pendente:
            st.markdown("### ⚠️ Requisito de Segurança Obrigatório")
            st.warning("Este é o seu primeiro acesso. Conforme as normas de segurança da informação da Diretoria Técnica, é obrigatório substituir a senha padrão por uma credencial forte.")
            
            st.markdown("<div class='form-card'>", unsafe_allow_html=True)
            nova_senha = st.text_input("Definir Nova Senha Segura (Mínimo 6 caracteres):", type="password")
            confirma_senha = st.text_input("Confirmar Nova Senha:", type="password")
            
            if st.button("Salvar Nova Credencial"):
                if len(nova_senha) >= 6 and nova_senha != "123":
                    if nova_senha == confirma_senha:
                        # Grava as alterações permanentemente na sessão
                        st.session_state.banco_senhas_customizadas[cpf_key] = criptografar_dado(nova_senha)
                        st.session_state.banco_primeiro_acesso[cpf_key] = False
                        st.success("✅ Senha validada e atualizada com sucesso! Inicializando painel de gestão...")
                        st.rerun() # Recarrega para sair da tela de troca de senha
                    else:
                        st.error("As senhas informadas não coincidem. Tente novamente.")
                else:
                    st.error("A senha deve ter no mínimo 6 caracteres e não pode ser a senha padrão.")
            st.markdown("</div>", unsafe_allow_html=True)
            
        else:
            # Painel Administrativo Definitivo
            st.markdown(f"### 📊 Painel de Governança Cirúrgica - Bem-vindo, {usuario['Nome']}")
            st.markdown("<div class='form-card'>", unsafe_allow_html=True)
            
            filtro_esp = st.selectbox("Filtragem Específica por Especialidade:", ["Visualizar Todas"] + list(df_fila["Especialidade"].unique()))
            
            df_filtrado = df_fila if filtro_esp == "Visualizar Todas" else df_fila[df_fila["Especialidade"] == filtro_esp]
            
            st.dataframe(df_filtrado, use_container_width=True, hide_index=True)
            
            col_met1, col_met2 = st.columns(2)
            col_met1.metric("Pacientes na Fila (Abertos)", len(df_filtrado))
            col_met2.metric("Atualização da Base", "Tempo Real (Drive)")
            st.markdown("</div>", unsafe_allow_html=True)
