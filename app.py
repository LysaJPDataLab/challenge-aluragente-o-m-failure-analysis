import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent

# -- AJUSTE CRUCIAL PARA GRÁFICOS NO STREAMLIT --
import matplotlib
matplotlib.use('Agg') # Força o modo de servidor para não travar
import matplotlib.pyplot as plt

# 1. Carregar variáveis de ambiente (Chave do Gemini)
load_dotenv()
google_api_key = os.getenv("GOOGLE_API_KEY")

# 2. Configuração da Página do Streamlit
st.set_page_config(
    page_title="AlurAgente - O&M Failure Analysis",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ AlurAgente: Análise de Falhas (O&M)")
st.markdown("Assistente inteligente para análise de dados do Complexo Eólico AlurAgente.")

# 3. Função para carregar os dados
@st.cache_data
def carregar_dados():
    try:
        df_scada = pd.read_csv("data/historico_paradas_wtg.csv")
        df_os = pd.read_csv("data/ordens_servico_wtg.csv")
        return df_scada, df_os
    except FileNotFoundError:
        st.error("⚠️ Arquivos CSV não encontrados na pasta 'data/'. Verifique a estrutura do projeto.")
        return None, None

df_scada, df_os = carregar_dados()

# 4. Configuração do Agente Inteligente (LangChain + Gemini)
def inicializar_agente(df_scada, df_os):
    # Inicializa o modelo Gemini
    llm = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash-lite", 
        temperature=0.2, 
        google_api_key=google_api_key
    )
    
    # Instruções de base do agente (Resumo do PDF de Diretrizes)
    instrucoes_engenharia = """
    Você é um Engenheiro de Confiabilidade Sênior analisando dados de um parque eólico.
    Você tem acesso a dois dataframes:
    1. df_scada: Histórico de paradas (TRIP, Corrective, Preventive). O tempo_parada_horas daqui define a indisponibilidade.
    2. df_os: Ordens de Serviço com custos e homem-hora (HH). Liga-se ao SCADA por id_parada_scada = id_parada.
    
    Regras estritas de O&M:
    - MTBF: Considere APENAS falhas (TRIP). Ignore Preventive e Corrective no contador de eventos.
    - MTTR: Considere APENAS eventos 'Corrective'.
    - Custos e HH de TRIPs automáticos sem OS atrelada são sempre ZERO.
    - Sempre filtre pelo 'subsistema' quando solicitado.
    
    REGRAS PARA GRÁFICOS:
    - Primeiro calcule os dados corretamente.
    - Para criar gráficos, escreva e execute o código em Python usando pandas e matplotlib.
    - Você DEVE incluir `import matplotlib.pyplot as plt` no seu código.
    - OBRIGATÓRIO: Salve o gráfico rodando EXATAMENTE o comando: plt.savefig('grafico_temp.png', bbox_inches='tight')
    - Limpe a memória em seguida usando plt.close()
    - NUNCA use plt.show().
    
    Sempre explique seu raciocínio brevemente antes de dar a resposta final.
    """

    # Cria o agente que sabe programar em Pandas
    agente = create_pandas_dataframe_agent(
        llm,
        [df_scada, df_os],
        verbose=True,
        allow_dangerous_code=True, 
        prefix=instrucoes_engenharia,
        handle_parsing_errors=True,
        agent_type="tool-calling",
        max_iterations=20
    )
    return agente

# 5. Interface de Chat (Histórico da Sessão)
if "mensagens" not in st.session_state:
    st.session_state.mensagens = []

# Exibir mensagens antigas
for msg in st.session_state.mensagens:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 6. Caixa de Texto para o Usuário digitar
if prompt := st.chat_input("Faça uma pergunta sobre os indicadores do parque eólico..."):
    
    # Mostrar pergunta do usuário
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Salvar pergunta no histórico
    st.session_state.mensagens.append({"role": "user", "content": prompt})
    
    # Processar a resposta do Agente
    with st.chat_message("assistant"):
        if df_scada is not None and df_os is not None:
            with st.spinner("Analisando bases de dados do SCADA e CMMS... ⚙️"):
                try:
                    agente = inicializar_agente(df_scada, df_os)
                    resposta = agente.invoke(prompt)
                    
                    # O LangChain retorna um dicionário, pegamos o output final
                    texto_resposta = resposta["output"]
                    
                    # Limpeza do pacote estruturado (desempacotando o tool-calling)
                    if isinstance(texto_resposta, list) and len(texto_resposta) > 0 and isinstance(texto_resposta[0], dict):
                        texto_resposta = texto_resposta[0].get("text", str(texto_resposta))
                        
                    st.markdown(texto_resposta)
                    
                    # Salvar resposta de texto no histórico
                    st.session_state.mensagens.append({"role": "assistant", "content": texto_resposta})
                    
                    # --- LÓGICA DE EXIBIÇÃO DE GRÁFICO ---
                    caminho_grafico = "grafico_temp.png"
                    if os.path.exists(caminho_grafico):
                        st.image(caminho_grafico)
                        # Remove a imagem do diretório para não ser exibida por engano na próxima pergunta
                        os.remove(caminho_grafico)
                        
                except Exception as e:
                    st.error(f"Ocorreu um erro ao processar a análise: {e}")