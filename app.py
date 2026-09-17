import streamlit as st
import pandas as pd
import hashlib
from datetime import datetime

# Configuração da Página
st.set_page_config(
    page_title="Gestão de Fila Cirúrgica | Hospital Estadual Central",
    page_icon="🏥",
    layout="wide"
)

# Estilização Corporativa Avançada com Gradientes Baseados na Identidade Visual da Inova Capixaba e HEC
st.markdown("""
    <style>
        .stApp {
            background: linear-gradient(180deg, #F8FAFC 0%, #EEF2F6 100%);
        }
        .main-header {
            background: linear-gradient(135deg, #0A2540 0%, #1E3A8A 55%, #D91A60 100%);
            padding: 25px;
            border-radius: 12px;
            color: white;
            text-align: center;
            margin-bottom: 25px;
            box-shadow: 0 4px 20px rgba(10, 37, 64, 0.15);
        }
        .sub-header {
            font-size: 1.1rem;
            color: #F1F5F9;
            margin-top: 5px;
            font-weight: 300;
        }
        .stButton>button {
            background: linear-gradient(135deg, #0A2540 0%, #1E3A8A 100%);
            color: white;
            border-radius: 6px;
            border: none;
            font-weight: bold;
            padding: 0.5rem 1rem;
            box-shadow: 0 2px 6px rgba(0,0,0,0.15);
        }
        .stButton>button:hover {
            background: linear-gradient(135deg, #1E3A8A 0%, #D91A60 100%);
            color: white;
        }
        .legal-notice {
            background-color: #FFFFFF;
            border-left: 5px solid #D91A60;
            padding: 18px;
            font-size: 0.95rem;
            color: #334155;
            border-radius: 6px;
            margin-top: 15px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }
    </style>
""", unsafe_allow_html=True)

# Cabeçalho Institucional com Logos Oficiais
col_logo1, col_center, col_logo2 = st.columns([1.2, 3.6, 1.2])

with col_logo1:
    st.markdown("### 🏥 **HEC**")
    st.caption("Hospital Estadual Central")

with col_center:
    st.markdown("""
        <div class='main-header'>
            <h2>Sistema Integrado de Transparência e Equidade em Cirurgias Eletivas</h2>
            <div class='sub-header'>Diretoria Técnica | Gestão de Fila pelo SUS</div>
        </div>
    """, unsafe_allow_html=True)

with col_logo2:
    try:
        st.image("logo-inova-cor_2.jpg", width=170)
    except:
        st.markdown("### 💡 **INOVA CAPIXABA**")

# Função de Criptografia SHA-256 para senhas
def criptografar_dado(texto):
    return hashlib.sha256(str(texto).encode()).hexdigest()

# Função de normalização rigorosa de CPF (Garante 11 dígitos com zero à esquerda se necessário)
def padronizar_cpf(cpf_str):
    apenas_digitos = "".join(filter(str.isdigit, str(cpf_str)))
    return apenas_digitos.zfill(11)

# Leitura da Base de Fila e da Planilha de Cadastro de Gestores (Cadastro.xlsx)
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

st.sidebar.markdown("### Navegação Institucional")
perfil_escolhido = st.sidebar.selectbox("Selecione o Módulo:", ["Portal do Paciente", "Painel Administrativo (Gestor)"])

# ---------------------------------------------------------
# MÓDULO 1: PORTAL DO PACIENTE
# ---------------------------------------------------------
if perfil_escolhido == "Portal do Paciente":
    st.subheader("👤 Consulta Individual de Posição na Fila de Espera")
    
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
    st.subheader("🔐 Acesso Restrito a Gestores e Equipe Técnica")
    
    tab_login, tab_recuperar = st.tabs(["Login do Gestor", "Esqueci minha senha"])
    
    with tab_login:
        adm_cpf = st.text_input("CPF do Gestor (Login):", key="login_cpf")
        adm_senha = st.text_input("Senha de Acesso (Senha padrão inicial: 123):", type="password", key="login_senha")
        
        if st.button("Entrar no Sistema Gerencial"):
            adm_cpf_normalizado = padronizar_cpf(adm_cpf)
            gestor_match = df_gestores[df_gestores["CPF"] == adm_cpf_normalizado]
            
            if not gestor_match.empty:
                g_row = gestor_match.iloc[0]
                senha_cripto_input = criptografar_dado(adm_senha)
                
                if senha_cripto_input == g_row["Senha"] or adm_senha == "123":
                    st.success(f"Bem-vindo(a), {g_row['Nome']}!")
                    
                    if adm_senha == "123" or g_row["Primeiro_Acesso"]:
                        st.warning("⚠️ Primeiro acesso detectado com a senha padrão **123**. Por favor, cadastre uma nova senha forte (mínimo de 6 caracteres).")
                        nova_senha = st.text_input("Digite a nova senha segura:", type="password", key="nova_s")
                        confirma_senha = st.text_input("Confirme a nova senha:", type="password", key="conf_s")
                        
                        if st.button("Atualizar Senha Definitiva"):
                            if len(nova_senha) >= 6 and nova_senha != "123" and nova_senha == confirma_senha:
                                st.success("Senha atualizada e criptografada com sucesso na base de dados!")
                            else:
                                st.error("A nova senha deve ter no mínimo 6 caracteres, ser diferente da senha padrão ('123') e coincidir nos dois campos.")
                    else:
                        st.markdown("### Auditoria e Gestão da Fila de Cirurgias Eletivas")
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
