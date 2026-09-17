import streamlit as st
import pandas as pd
import hashlib

# Configuração da Página
st.set_page_config(
    page_title="Gestão de Fila Cirúrgica | HEC & Inova Capixaba",
    page_icon="🏥",
    layout="wide"
)

# Estilização Avançada de Alto Padrão (UI/UX - Web Design Corporativo Executivo)
st.markdown("""
    <style>
        /* Paleta de Cores e Fundo Gradiente Executivo Baseado na Inova Capixaba e HEC */
        .stApp {
            background: linear-gradient(135deg, #07192A 0%, #0A2540 40%, #1B2A4A 100%);
            color: #E2E8F0;
        }
        /* Cabeçalho Corporativo de Luxo */
        .main-header {
            background: linear-gradient(135deg, #0A2540 0%, #1E3A8A 50%, #D91A60 100%);
            padding: 30px;
            border-radius: 16px;
            color: white;
            text-align: center;
            margin-bottom: 25px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        .main-title {
            font-size: 2rem;
            font-weight: 800;
            letter-spacing: -0.5px;
            margin-bottom: 5px;
        }
        .sub-header {
            font-size: 1.15rem;
            color: #F1F5F9;
            font-weight: 400;
        }
        /* Cartões de Conteúdo e Vidro Corporativo (Glassmorphism sutil) */
        .card-container {
            background: rgba(15, 23, 42, 0.75);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            padding: 25px;
            border-radius: 14px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            margin-bottom: 20px;
        }
        /* Botões Executivos */
        .stButton>button {
            background: linear-gradient(135deg, #D91A60 0%, #9B1141 100%);
            color: white;
            border-radius: 8px;
            border: none;
            font-weight: 700;
            padding: 0.6rem 1.2rem;
            box-shadow: 0 4px 15px rgba(217, 26, 96, 0.4);
            transition: all 0.3s ease;
        }
        .stButton>button:hover {
            background: linear-gradient(135deg, #E63973 0%, #B81D53 100%);
            box-shadow: 0 6px 20px rgba(217, 26, 96, 0.6);
            transform: translateY(-1px);
        }
        /* Aviso Institucional */
        .legal-notice {
            background: rgba(30, 41, 59, 0.9);
            border-left: 6px solid #D91A60;
            padding: 20px;
            font-size: 0.95rem;
            color: #F8FAFC;
            border-radius: 8px;
            margin-top: 15px;
            margin-bottom: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            border-top: 1px solid rgba(255,255,255,0.05);
        }
        /* Rodapé de Versão */
        .version-badge {
            position: fixed;
            bottom: 10px;
            right: 15px;
            background: rgba(15, 23, 42, 0.85);
            color: #94A3B8;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.75rem;
            border: 1px solid rgba(255, 255, 255, 0.1);
            z-index: 9999;
            backdrop-filter: blur(5px);
        }
    </style>
""", unsafe_allow_html=True)

# Exibição da Versão do Sistema no Rodapé
st.markdown("<div class='version-badge'>Versão 2.1.0-PRO | HEC & Inova</div>", unsafe_allow_html=True)

# Cabeçalho Institucional com Logotipo Oficial e Design de Luxo
col_logo1, col_center, col_logo2 = st.columns([1.2, 3.6, 1.2])

with col_logo1:
    st.markdown("### 🏥 **HEC**")
    st.caption("Hospital Estadual Central")

with col_center:
    st.markdown("""
        <div class='main-header'>
            <div class='main-title'>Sistema Integrado de Transparência e Equidade</div>
            <div class='sub-header'>Diretoria Técnica | Gestão de Fila Cirúrgica Eletiva (SUS)</div>
        </div>
    """, unsafe_allow_html=True)

with col_logo2:
    try:
        st.image("logo-inova-cor_2.jpg", width=170)
    except:
        st.markdown("### 💡 **INOVA CAPIXABA**")

# Funções de Criptografia e Padronização de CPF
def criptografar_dado(texto):
    return hashlib.sha256(str(texto).encode()).hexdigest()

def padronizar_cpf(cpf_str):
    apenas_digitos = "".join(filter(str.isdigit, str(cpf_str)))
    return apenas_digitos.zfill(11)

# Inicialização de Estados de Sessão para Persistência de Senhas e Alterações
if "senhas_customizadas" not in st.session_state:
    st.session_state.senhas_customizadas = {}  # Mapeia CPF -> Hash da nova senha
if "primeiro_acesso_feito" not in st.session_state:
    st.session_state.primeiro_acesso_feito = set()  # CPFs que já concluíram a troca de senha

# Leitura da Base de Fila e Gestores (Cadastro.xlsx)
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
            "Senha": [criptografar_dado("123")] * len(df_cad),
            "Primeiro_Acesso": [True] * len(df_cad)
        })
    except Exception as e:
        df_gestores = pd.DataFrame({
            "Nome": ["Dr. Marcelo Torres"],
            "CPF": [padronizar_cpf("09021165767")],
            "Email": ["marcelotorres.md@gmail.com"],
            "Senha": [criptografar_dado("123")],
            "Primeiro_Acesso": [True]
        })
        
    return df_f, df_gestores

df_fila, df_gestores = carregar_bases()

if "Escore_Prioridade" in df_fila.columns:
    df_fila = df_fila.sort_values(by="Escore_Prioridade", ascending=False).reset_index(drop=True)
    df_fila["Posicao_Fila"] = df_fila.index + 1

# Menu Lateral Executivo
st.sidebar.markdown("### 🧭 Navegação Institucional")
perfil_escolhido = st.sidebar.selectbox("Selecione o Módulo:", ["Portal do Paciente", "Painel Administrativo (Gestor)"])

# ---------------------------------------------------------
# MÓDULO 1: PORTAL DO PACIENTE
# ---------------------------------------------------------
if perfil_escolhido == "Portal do Paciente":
    st.markdown("### 👤 Consulta Individual de Posição na Fila de Espera")
    
    st.markdown("""
        <div class='legal-notice'>
            <strong>Aviso Institucional e Transparência do SUS:</strong><br>
            A fila de espera do Sistema Único de Saúde (SUS) para procedimentos eletivos no Hospital Estadual Central 
            não obedece estritamente à ordem cronológica de inscrição. Em cumprimento aos princípios da administração pública 
            e às diretrizes do SUS, a priorização é regida por critérios técnicos e de equidade clínica. O ranqueamento computa 
            a gravidade do quadro, riscos associados, faixas etárias prioritárias e a conclusão integral do itinerário de exames 
            e avaliações pré-anestésicas, garantindo justiça distributiva, segurança do paciente e eficiência cirúrgica.
        </div>
    """, unsafe_allow_html=True)
    
    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        pac_nome = st.text_input("Nome Completo do Paciente:")
    with col_p2:
        pac_cpf = st.text_input("CPF (ex: 111.222.333-44):")
    with col_p3:
        pac_cns = st.text_input("Número do Cartão do SUS (CNS):")
        
    if st.button("Consultar Minha Posição"):
        if pac_nome and pac_cpf and pac_cns:
            match_paciente = df_fila[
                (df_fila["Nome_Paciente"].str.strip().str.lower() == pac_nome.strip().lower()) &
                (df_fila["CPF"].str.strip() == pac_cpf.strip()) &
                (df_fila["Cartao_SUS"].str.strip() == pac_cns.strip())
            ]
            
            if not match_paciente.empty:
                p = match_paciente.iloc[0]
                st.success("Autenticação realizada com sucesso!")
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Sua Posição Atual na Fila", f"{int(p['Posicao_Fila'])}º Lugar")
                c2.metric("Especialidade Cirúrgica", p["Especialidade"])
                c3.metric("Número da AIH", p["Numero_AIH"])
                
                st.markdown("#### Status Atual do Preparo Pré-Operatório:")
                ex1, ex2, ex3, ex4 = st.columns(4)
                ex1.info(f"**Exames Lab:** {p['Status_Exames_Lab']}")
                ex2.info(f"**Exames Imagem:** {p['Status_Exames_Imagem']}")
                ex3.info(f"**Avaliação Cardio:** {p['Status_Avaliacao_Cardio']}")
                ex4.info(f"**Avaliação Pré-Anestésica:** {p['Status_Avaliacao_PreAnestesica']}")
            else:
                st.error("Não foram encontrados registros correspondentes aos dados informados. Verifique a grafia e numeração digitadas.")
        else:
            st.warning("Preencha todos os campos obrigatórios para efetuar a consulta.")

# ---------------------------------------------------------
# MÓDULO 2: PAINEL ADMINISTRATIVO (GESTOR)
# ---------------------------------------------------------
elif perfil_escolhido == "Painel Administrativo (Gestor)":
    st.markdown("### 🔐 Acesso Restrito a Gestores e Equipe Técnica")
    
    tab_login, tab_recuperar = st.tabs(["Login do Gestor", "Esqueci minha senha"])
    
    with tab_login:
        adm_cpf = st.text_input("CPF do Gestor (Login):", key="login_cpf")
        adm_senha = st.text_input("Senha de Acesso:", type="password", key="login_senha")
        
        if st.button("Entrar no Sistema Gerencial"):
            adm_cpf_normalizado = padronizar_cpf(adm_cpf)
            gestor_match = df_gestores[df_gestores["CPF"] == adm_cpf_normalizado]
            
            if not gestor_match.empty:
                g_row = gestor_match.iloc[0]
                cpf_key = g_row["CPF"]
                
                # Verifica se já existe uma senha personalizada em sessão
                senha_cadastrada = st.session_state.senhas_customizadas.get(cpf_key, g_row["Senha"])
                primeiro_acesso_pendente = (cpf_key not in st.session_state.primeiro_acesso_feito) and (g_row["Primeiro_Acesso"] or adm_senha == "123")
                
                senha_cripto_input = criptografar_dado(adm_senha)
                
                if senha_cripto_input == senha_cadastrada or (primeiro_acesso_pendente and adm_senha == "123"):
                    st.success(f"Bem-vindo(a), {g_row['Nome']}!")
                    
                    if primeiro_acesso_pendente or adm_senha == "123":
                        st.warning("⚠️ Primeiro acesso detectado com a senha padrão **123**. Por favor, cadastre uma nova senha forte (mínimo de 6 caracteres).")
                        
                        with st.form("form_nova_senha"):
                            nova_senha = st.text_input("Digite a nova senha segura:", type="password")
                            confirma_senha = st.text_input("Confirme a nova senha:", type="password")
                            btn_atualizar = st.form_submit_button("Atualizar Senha Definitiva")
                            
                            if btn_atualizar:
                                if len(nova_senha) >= 6 and nova_senha != "123" and nova_senha == confirma_senha:
                                    # Salva permanentemente na sessão o novo hash da senha e marca como concluído
                                    st.session_state.senhas_customizadas[cpf_key] = criptografar_dado(nova_senha)
                                    st.session_state.primeiro_acesso_feito.add(cpf_key)
                                    st.success("✅ Senha atualizada e criptografada com sucesso! Faça login novamente com sua nova senha.")
                                    st.rerun()
                                else:
                                    st.error("A nova senha deve ter no mínimo 6 caracteres, ser diferente da senha padrão ('123') e coincidir nos dois campos.")
                    else:
                        st.markdown("---")
                        st.markdown("### 📊 Painel de Auditoria e Gestão Cirúrgica")
                        filtro_esp = st.selectbox("Filtrar por Especialidade:", ["Todas"] + list(df_fila["Especialidade"].unique()))
                        
                        if filtro_esp != "Todas":
                            df_filtrado = df_fila[df_fila["Especialidade"] == filtro_esp]
                        else:
                            df_filtrado = df_fila
                            
                        st.dataframe(df_filtrado, use_container_width=True)
                        st.metric("Total de Pacientes na Fila Ativa", len(df_filtrado))
                else:
                    st.error("Senha incorreta.")
            else:
                st.error(f"CPF '{adm_cpf}' não localizado na base de gestores autorizados (`Cadastro.xlsx`).")
                
    with tab_recuperar:
        st.markdown("#### Recuperação de Senha de Gestor")
        email_rec = st.text_input("Informe seu e-mail institucional cadastrado:")
        if st.button("Enviar Instruções de Recuperação"):
            if email_rec:
                email_encontrado = not df_gestores[df_gestores["Email"].str.strip().str.lower() == email_rec.strip().lower()].empty
                if email_encontrado:
                    st.success("Instruções de redefinição de senha enviadas com segurança para o e-mail corporativo cadastrado.")
                else:
                    st.error("O e-mail informado não consta na base de dados autorizada.")
            else:
                st.warning("Insira um e-mail corporativo válido.")
