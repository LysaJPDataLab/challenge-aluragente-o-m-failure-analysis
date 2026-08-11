import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

# Configurações do Parque Eólico
NUM_WTGS = 30
NUM_REGISTROS = 1500
DATA_INICIO = datetime(2025, 1, 1)

# Gerar lista de WTGs (WTG-01 até WTG-30)
wtgs = [f"WTG-{str(i).zfill(2)}" for i in range(1, NUM_WTGS + 1)]

# Subsistemas e Modos de Falha
subsistemas_alarmes = {
    "Pitch System": [
        "201 - Difference between Pitch angles",
        "202 - Pitch battery fault",
        "203 - Pitch motor overtemperature",
        "204 - Pitch position sensor error",
        "205 - Blade angle asymmetry limit reached"
    ],
    "Yaw System": [
        "301 - Yaw error",
        "302 - Yaw motor overload",
        "303 - Cable twist limit exceeded",
        "304 - Yaw brake failure",
        "305 - Yaw inverter fault"
    ],
    "Hydraulic System": [
        "401 - Low hydraulic pressure",
        "402 - High hydraulic pressure",
        "403 - Hydraulic pump motor overload",
        "404 - Hydraulic oil low level",
        "405 - Valve switching failure"
    ],
    "Generator": [
        "501 - High temperature winding",
        "502 - Generator cooling failure",
        "503 - Bearing temperature high",
        "504 - Slip ring brush wear limit",
        "505 - Generator overspeed"
    ],
    "Converter / Electrical": [
        "601 - Grid voltage out of limits",
        "602 - IGBT overtemperature",
        "603 - Converter communication failure",
        "604 - DC link overvoltage",
        "605 - Grid frequency instability"
    ],
    "Gearbox (Multiplicador)": [
        "701 - Low oil pressure",
        "702 - High oil temperature",
        "703 - Bearing vibration high",
        "704 - Oil filter clogged",
        "705 - Gear mesh frequency vibration"
    ],
    "Sensors / Weather": [
        "801 - Anemometer mismatch",
        "802 - Wind vane error",
        "803 - Ice detection on blades",
        "804 - Ambient temperature out of range"
    ]
}

dados = []

for i in range(NUM_REGISTROS):
    # 1. Definição do cronograma do evento
    dias_aleatorios = random.randint(0, 364)
    horas_aleatorias = random.randint(0, 23)
    minutos_aleatorios = random.randint(0, 59)
    
    data_hora_inicio = DATA_INICIO + timedelta(days=dias_aleatorios, hours=horas_aleatorias, minutes=minutos_aleatorios)
    
    # 2. Definição do tipo de intervenção e cálculo do tempo de parada
    tipo_manutencao = np.random.choice(["Corretiva", "Preventiva"], p=[0.8, 0.2])
    
    if tipo_manutencao == "Preventiva":
        tempo_parada = round(random.uniform(4.0, 12.0), 1)
    else:
        tempo_parada = round(np.random.exponential(scale=8.5) + 0.5, 1)
        if tempo_parada > 120:  
            tempo_parada = 120.0
            
    data_hora_fim = data_hora_inicio + timedelta(hours=tempo_parada)
    
    # 3. Sorteio do ativo e separação do modo de falha
    wtg = random.choice(wtgs)
    subsistema = random.choice(list(subsistemas_alarmes.keys()))
    alarme_completo = random.choice(subsistemas_alarmes[subsistema])
    
    # Dividindo a string "Código - Descrição" em duas variáveis separadas
    codigo, descricao = alarme_completo.split(" - ")
    
    # 4. Consolidação do registro em um dicionário
    dados.append({
        "data_hora_inicio": data_hora_inicio.strftime("%Y-%m-%d %H:%M:%S"),
        "data_hora_fim": data_hora_fim.strftime("%Y-%m-%d %H:%M:%S"),
        "aerogerador": wtg,
        "subsistema": subsistema,
        "codigo_alarme": codigo,
        "descricao_alarme": descricao,
        "tempo_parada_horas": tempo_parada,
        "tipo_manutencao": tipo_manutencao
    })

# Criar DataFrame diretamente a partir da lista de dicionários
df = pd.DataFrame(dados)

# Ordenar cronologicamente e inserir a coluna de ID na primeira posição
df = df.sort_values(by="data_hora_inicio").reset_index(drop=True)
df.insert(0, "id_parada", df.index + 1)

# Exportar para CSV
df.to_csv("historico_paradas.csv", index=False, encoding='utf-8')

print(f"Arquivo 'historico_paradas.csv' gerado sucesso! Total de registros: {len(df)}")
