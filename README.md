# challenge-aluragente-o-m-failure-analysis

## Estrutura do repositório

challenge-aluragente-o-m-failure-analysis/
│
├── .streamlit/               # (Opcional) Configurações visuais do Streamlit
│   └── config.toml
│
├── data/
│   └── historico_paradas.csv # Arquivo CSV com os dados de alarmes e falhas dos aerogeradores
│
├── src/                      # (Opcional) Pasta para organizar os módulos lógicos do código
│   └── agent.py              # Lógica de conexão com o LangChain e Gemini
│
├── .env                      # Arquivo local com suas chaves (NÃO vai para o GitHub!)
├── .gitignore                # Arquivo para proteger dados sensíveis e cache
├── app.py                    # Arquivo principal da interface e execução (Streamlit)
├── requirements.txt          # Lista de dependências e bibliotecas do Python
└── README.md                 # Documentação completa do projeto
