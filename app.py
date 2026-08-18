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

# 3.5 Configuração do RAG (Leitura do Manual em PDF)
@st.cache_resource
def configurar_rag():
    try:
        # 1. Carrega o PDF do diretório
        loader = PyPDFLoader("docs/MANUAL DE DIRETRIZES DE CONFIABILIDADE E INDICADORES DE MANUTENÇÃO.pdf")
        documentos = loader.load()
        
        # 2. Divide o documento em chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, 
            chunk_overlap=200
        )
        textos_divididos = text_splitter.split_documents(documentos)
        
        # 3. Cria os embeddings com o modelo do Gemini
        embeddings = GoogleGenerativeAIEmbeddings(
            model="gemini-embedding-001",
            google_api_key=google_api_key
        )

        # 4. Cria o banco vetorial FAISS
        vector_store = FAISS.from_documents(
            textos_divididos, 
            embeddings
        )
        
        # 5. Cria o retriever
        retriever = vector_store.as_retriever(
            search_kwargs={"k": 3}
        )

        # 6. Cria a ferramenta que será usada pelo agente
        ferramenta_rag = create_retriever_tool(
            retriever,
            "buscar_diretrizes_manutencao",
            "Busca e retorna informações teóricas, regras e conceitos do Manual de Diretrizes de Confiabilidade."
        )

        return ferramenta_rag
    
    except Exception as e:
        st.warning(f"⚠️ Não foi possível carregar o PDF para o RAG: {e}")
        return None

ferramenta_rag = configurar_rag()

# 4. Configuração do Agente Inteligente (LangChain + Gemini)
def inicializar_agente(df_scada, df_os):
    # Inicializa o modelo Gemini
    llm = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash-lite", 
        temperature=0.2, 
        google_api_key=google_api_key
    )
    
    # Instruções de base do agente (Prompt)
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
    # Prepara a lista de ferramentas extras (insere o RAG se ele tiver sido carregado com sucesso)
    tools = [ferramenta_rag] if ferramenta_rag else []

    # Cria o agente que sabe programar em Pandas e Ler PDFs
    agente = create_pandas_dataframe_agent(
        llm,
        [df_scada, df_os],
        verbose=True,
        allow_dangerous_code=True, 
        prefix=instrucoes_engenharia,
        handle_parsing_errors=True,
        agent_type="tool-calling",
        max_iterations=20,
        extra_tools=tools
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
