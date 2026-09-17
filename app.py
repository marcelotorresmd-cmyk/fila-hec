import streamlit as st
import pandas as pd
from datetime import datetime

# Configuração da Página
st.set_page_config(
    page_title="Fila Cirúrgica - Hospital Estadual Central",
    page_icon="🏥",
    layout="wide"
)

# URL ou carregamento do Google Sheets (Modo público/CSV exportado ou via pandas)
# Nota: Para produção, utiliza-se a API do Google Sheets ou o link CSV público da planilha.
@st.cache_data(ttl=60)
def carregar_dados():
    # Substitua abaixo pelo link de exportação CSV da sua planilha do Google Sheets publicada na web,
    # ou utilize um arquivo local 'dados_fila.csv' para testes iniciais.
    url = "SUA_URL_DE_EXPORTACAO_CSV_DO_GOOGLE_SHEETS_AQUI"
    try:
        df = pd.read_csv(url)
        return df
    except:
        # DataFrame de exemplo caso o link ainda não esteja configurado
        data = {
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
        return pd.DataFrame(data)

df = carregar_dados()

# Ordenar o DataFrame pelo Escore de Prioridade de forma decrescente (maior escore = topo da fila)
if "Escore_Prioridade" in df.columns:
    df = df.sort_values(by="Escore_Prioridade", ascending=False).reset_index(drop=True)
    df["Posicao_Fila"] = df.index + 1
else:
    df["Posicao_Fila"] = 1

# Barra Lateral - Escolha do Perfil
st.sidebar.title("Navegação do Sistema")
perfil = st.sidebar.selectbox("Selecione o Perfil de Acesso:", ["Área do Paciente (Consulta)", "Área Administrativa (Gestor)"])

# ---------------------------------------------------------
# MÓDULO 1: ÁREA DO PACIENTE
# ---------------------------------------------------------
if perfil == "Área do Paciente (Consulta)":
    st.title("🏥 Hospital Estadual Central - Consulta de Posição na Fila")
    st.markdown("### Sistema de Transparência de Cirurgias Eletivas")
    
    # Aviso legal obrigatório sobre a equidade no SUS
    st.info(
        "**Aviso Importante sobre a Fila do SUS:**\n\n"
        "A fila de espera do Sistema Único de Saúde (SUS) não obedece estritamente à ordem cronológica de inscrição. "
        "Em conformidade com os princípios constitucionais e as diretrizes do SUS, a priorização é regida por critérios "
        "técnicos, clínicos e de equidade. O escore considera a gravidade do quadro clínico, riscos associados, faixas "
        "etárias prioritárias e a conclusão integral do itinerário de exames laboratoriais, de imagem e avaliações "
        "pré-anestésicas, garantindo a justiça distributiva e a máxima eficiência cirúrgica."
    )
    
    st.markdown("---")
    st.subheader("Informe seus dados para consultar a sua situação:")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        input_nome = st.text_input("Nome Completo:")
    with col2:
        input_cpf = st.text_input("CPF (ex: 111.222.333-44):")
    with col3:
        input_cns = st.text_input("Número do Cartão do SUS (CNS):")
        
    if st.button("Consultar Situação na Fila"):
        if input_nome and input_cpf and input_cns:
            # Filtro cruzado para segurança e validação
            paciente_encontrado = df[
                (df["Nome_Paciente"].str.strip().str.lower() == input_nome.strip().lower()) &
                (df["CPF"].str.strip() == input_cpf.strip()) &
                (df["Cartao_SUS"].str.strip() == input_cns.strip())
            ]
            
            if not paciente_encontrado.empty:
                p = paciente_encontrado.iloc[0]
                st.success("Cadastro localizado com sucesso!")
                
                # Exibição dos dados em cartões visuais
                col_a, col_b, col_c = st.columns(3)
                col_a.metric("Posição Atual na Fila", f"{int(p['Posicao_Fila'])}º lugar")
                col_b.metric("Especialidade", p["Especialidade"])
                col_c.metric("Número da AIH", p["Numero_AIH"])
                
                st.markdown("#### Status do Preparo Pré-Operatório:")
                col_ex1, col_ex2, col_ex3, col_ex4 = st.columns(4)
                col_ex1.text(f"Exames Lab: {p['Status_Exames_Lab']}")
                col_ex2.text(f"Exames Imagem: {p['Status_Exames_Imagem']}")
                col_ex3.text(f"Avaliação Cardio: {p['Status_Avaliacao_Cardio']}")
                col_ex4.text(f"Avaliação Pré-Anest.: {p['Status_Avaliacao_PreAnestesica']}")
                
            else:
                st.error("Nenhum registro encontrado com a combinação exata de Nome, CPF e Cartão do SUS informados. Verifique os dados digitados.")
        else:
                st.warning("Por favor, preencha todos os campos de identificação para realizar a consulta.")

# ---------------------------------------------------------
# MÓDULO 2: ÁREA DO GESTOR
# ---------------------------------------------------------
elif perfil == "Área Administrativa (Gestor)":
    st.title("🔒 Painel Gerencial - Hospital Estadual Central")
    st.markdown("### Acesso Restrito a Gestores e Operadores Autorizados")
    
    senha_digitada = st.text_input("Digite a senha administrativa:", type="password")
    
    # Senha padrão de exemplo (em produção, usar variáveis de ambiente seguras)
    SENHA_MESTRE = "hec2026admin"
    
    if senha_digitada == SENHA_MESTRE:
        st.success("Acesso autorizado com sucesso.")
        st.subheader("Visão Geral Consolidada da Fila Cirúrgica")
        
        # Filtros administrativos
        especialidade_filtro = st.selectbox("Filtrar por Especialidade:", ["Todas"] + list(df["Especialidade"].unique()))
        if especialidade_filtro != "Todas":
            df_exibicao = df[df["Especialidade"] == especialidade_filtro]
        else:
            df_exibicao = df
            
        st.dataframe(df_exibicao, use_container_width=True)
        st.metric("Total de Pacientes na Fila", len(df_exibicao))
        
    elif senha_digitada != "":
        st.error("Senha incorreta. Acesso negado.")
