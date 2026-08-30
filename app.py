import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent

# -- PARA GRÁFICOS NO STREAMLIT --
import matplotlib
matplotlib.use('Agg') # Força o modo de servidor para não travar
import matplotlib.pyplot as plt

# -- PARA o RAG NO STREAMLIT --
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.tools import create_retriever_tool

# 1. Carregar variáveis de ambiente (Chave do Gemini)
load_dotenv()
google_api_key = os.getenv("GOOGLE_API_KEY")

if not google_api_key:
    try:
        google_api_key = st.secrets["GOOGLE_API_KEY"]
    except KeyError:
        st.error("A GOOGLE_API_KEY não foi configurada.")
        st.stop()

# 2. Configuração da Página do Streamlit
st.set_page_config(
    page_title="AlurAgente - Wind Farm Failure Analysis",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Caminhos das imagens do avatar
AVATAR_ROSTO = "https://github.com/LysaJPDataLab/challenge-aluragente-o-m-failure-analysis/blob/main/assets/avatar_rosto.png?raw=true"
AVATAR_CORPO = "https://github.com/LysaJPDataLab/challenge-aluragente-o-m-failure-analysis/blob/main/assets/avatar_corpo.png?raw=true"

# ==========================================
# START - ÁREA PRINCIPAL
# ==========================================
st.title("Histórico Operacional e Indicadores do Complexo Eólico AlurAgente")

# 3. Funções de Carregamento
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

# ==========================================
# BARRA LATERAL (SIDEBAR)
# ==========================================
# Posicionamento necessário para que seja possível usar os dados das bases
with st.sidebar:
    st.markdown("## AlurAgente")
    st.markdown("**Complexo Eólico AlurAgente**") 
    st.divider()
    
    # Verifica se os dados foram carregados corretamente no app
    if df_scada is not None and not df_scada.empty:
        
        # 1. CONTAGEM DISTINTA DE AEROGERADORES
        coluna_aerogerador = 'aerogerador' 
        
        if coluna_aerogerador in df_scada.columns:
            total_turbinas = df_scada[coluna_aerogerador].nunique()
        else:
            total_turbinas = "Erro"
        
        # 2. CONTAGEM DE EVENTOS (TRIP)
        coluna_evento = 'tipo_parada'
        
        if coluna_evento in df_scada.columns:
            total_trips = len(df_scada[df_scada[coluna_evento] == 'TRIP'])
        else:
            total_trips = "Erro"

        # 3. PERÍODO DE DADOS DISPONÍVEL
        coluna_data = 'data_hora_inicio'
        
        if coluna_data in df_scada.columns:
            # Converte a coluna para o formato de data (datetime) do Pandas para garantir o min/max correto
            datas_formatadas = pd.to_datetime(df_scada[coluna_data], errors='coerce')
            
            data_minima = datas_formatadas.min().strftime('%d/%m/%Y')
            data_maxima = datas_formatadas.max().strftime('%d/%m/%Y')
            periodo = f"{data_minima} a {data_maxima}"
        else:
            periodo = "Erro de Coluna"

        # --- EXIBIÇÃO NA TELA ---
        st.metric(label="Aerogeradores", value=total_turbinas)
        st.metric(label="Eventos de TRIP", value=total_trips)
        st.markdown(f"**📆 Período:** {periodo}")
        
    else:
        st.info("Aguardando carregamento da base de dados...")
        
    st.divider()
    
    # Adiciona a imagem de corpo inteiro no final da barra lateral
    st.image(AVATAR_CORPO, use_container_width=True)

# ==========================================
# 4. RAG, Agente, Abas do Chat
# ==========================================

@st.cache_resource
def configurar_rag():
    try:
        loader = PyPDFLoader("docs/MANUAL DE DIRETRIZES DE CONFIABILIDADE E INDICADORES DE MANUTENÇÃO.pdf")
        documentos = loader.load()
        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        textos_divididos = text_splitter.split_documents(documentos)
        
        embeddings = GoogleGenerativeAIEmbeddings(model="gemini-embedding-001", google_api_key=google_api_key)
        vector_store = FAISS.from_documents(textos_divididos, embeddings)
        retriever = vector_store.as_retriever(search_kwargs={"k": 3})
        
        ferramenta_rag = create_retriever_tool(
            retriever,
            "buscar_diretrizes_manutencao",
            "Busca e retorna informações teóricas, regras e conceitos do Manual de Diretrizes de Confiabilidade."
        )
        return ferramenta_rag
    except Exception as e:
        st.error(f"Erro ao configurar o RAG: {e}")
        return None

ferramenta_rag = configurar_rag()

def inicializar_agente(df_scada, df_os):
    llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite", temperature=0.2, google_api_key=google_api_key)
    instrucoes_engenharia = """
    Você é uma Engenheira de Confiabilidade Sênior analisando dados de um parque eólico.
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
    tools = [ferramenta_rag] if ferramenta_rag else []
    agente = create_pandas_dataframe_agent(
        llm, [df_scada, df_os], verbose=True, allow_dangerous_code=True, 
        prefix=instrucoes_engenharia, handle_parsing_errors=True,
        agent_type="tool-calling", max_iterations=20, extra_tools=tools
    )
    return agente

# ==========================================
# INTERFACE EM ABAS (TAB)
# ==========================================
# Define duas abas: Chat e Mapa
tab_chat, tab_mapa = st.tabs(["Chat", "Mapa"])

with tab_chat:
    # Histórico da Sessão
    if "mensagens" not in st.session_state:
        st.session_state.mensagens = [
            {"role": "assistant", "content": "Olá! Eu sou a AlurAgente. Estive analisando os dados do Complexo Eólico AlurAgente. Como posso te ajudar com as análises hoje?"}
        ]

    # Exibir mensagens antigas
    for msg in st.session_state.mensagens:
        # Define qual ícone usar com base em quem está falando
        icone = AVATAR_ROSTO if msg["role"] == "assistant" else "🧑" if msg["role"] == "user" else None
        
        with st.chat_message(msg["role"], avatar=icone):
            st.markdown(msg["content"])

with tab_mapa:
    st.subheader("Visão Geral: Complexo Eólico AlurAgente")
    
    # Exibe a imagem do mapa usando o link diretamente
    caminho_mapa = "https://github.com/LysaJPDataLab/challenge-aluragente-o-m-failure-analysis/blob/main/assets/mapa_parque.jpg?raw=true"
    st.image(caminho_mapa, caption="Mapa Conceitual do Parque.", use_container_width=True)

    st.divider()

    # Layout em colunas para os dados técnicos
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Dados da Usina")
        st.markdown("""
        * **Capacidade Instalada:** 63.0 MW
        * **Total de Aerogeradores:** 30
        * **Tensão de Geração:** 690 V
        * **Tensão de Exportação (Subestação):** 34,5/69 kV
        * **Conexão:** Sistema Interligado Nacional (SIN)
        """)

    with col2:
        st.markdown("### Especificações do Aerogerador")
        st.markdown("""
        * **Potência Nominal:** 2.100 kW (2.1 MW)
        * **Altura da Torre:** 90 metros
        * **Diâmetro do Rotor:** 114 metros
        * **Velocidade Nominal do Vento:** 12 m/s
        * **Cut-out:** 25 m/s
        * **Cut-in:** 3 m/s
        * **Tipo de Rotor:** Horizontal
        * **Tipo de Gerador:** DFIG (Double Fed Induction Generator)
        * **Tipo de Torre:** Tubular de aço
        * **Sistema de Pitch:** Acionamento Eletromecânico Independente
        * **Controle:** SCADA / PLC dedicado por máquina
        """)

# ==========================================
# CAIXA DE TEXTO FIXA NO RODAPÉ
# ==========================================
# chat_input FORA das abas para o Streamlit fixar automaticamente na base da tela
if prompt := st.chat_input("Faça uma pergunta sobre os indicadores do parque eólico..."):
    
    # Redirecionamos a exibição da pergunta e da resposta DE VOLTA para a aba de Chat
    with tab_chat:
        # Mostrar pergunta do usuário
        with st.chat_message("user", avatar="🧑"):
            st.markdown(prompt)
        
        # Salvar pergunta no histórico
        st.session_state.mensagens.append({"role": "user", "content": prompt})
        
        # Processar a resposta do Agente
        with st.chat_message("assistant", avatar=AVATAR_ROSTO):
            if df_scada is not None and df_os is not None:
                with st.spinner("Analisando bases de dados do SCADA e CMMS... ⚙️"):
                    try:
                        agente = inicializar_agente(df_scada, df_os)
                        resposta = agente.invoke(prompt)
                        
                        texto_resposta = resposta["output"]
                        if isinstance(texto_resposta, list) and len(texto_resposta) > 0 and isinstance(texto_resposta[0], dict):
                            texto_resposta = texto_resposta[0].get("text", str(texto_resposta))
                            
                        st.markdown(texto_resposta)
                        st.session_state.mensagens.append({"role": "assistant", "content": texto_resposta})
                        
                        # --- LÓGICA DE EXIBIÇÃO DE GRÁFICO ---
                        caminho_grafico = "grafico_temp.png"
                        if os.path.exists(caminho_grafico):
                            st.image(caminho_grafico)
                            os.remove(caminho_grafico)
                            
                    except Exception as e:
                        st.error(f"Ocorreu um erro ao processar a análise: {e}")
