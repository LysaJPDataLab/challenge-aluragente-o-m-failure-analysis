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
    "Electrical": [
        "601 - Grid voltage out of limits",
        "602 - IGBT overtemperature",
        "603 - Converter communication failure",
        "604 - DC link overvoltage",
        "605 - Grid frequency instability"
    ],
    "Gearbox": [
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
    # Data e hora aleatória no período de 12 meses
    dias_aleatorios = random.randint(0, 364)
    horas_aleatorias = random.randint(0, 23)
    minutos_aleatorios = random.randint(0, 59)
    data_hora = DATA_INICIO + timedelta(days=dias_aleatorios, hours=horas_aleatorias, minutes=minutos_aleatorios)
    
    wtg = random.choice(wtgs)
    subsistema = random.choice(list(subsistemas_alarmes.keys()))
    alarme = random.choice(subsistemas_alarmes[subsistema])
    
    # Simular tempo de parada (skewed: muitas paradas curtas, algumas longas)
    tempo_parada = round(np.random.exponential(scale=8.5) + 0.5, 1)
    if tempo_parada > 120:  
        tempo_parada = 120.0
        
    # Definir tipo de manutenção (80% corretiva, 20% preventiva)
    # Refletindo a realidade onde a equipe de campo insere os dados de corretiva com mais frequência
    tipo_manutencao = np.random.choice(["Corretiva", "Preventiva"], p=[0.8, 0.2])
    
    if tipo_manutencao == "Preventiva":
        tempo_parada = round(random.uniform(4.0, 12.0), 1)

    dados.append([i+1, data_hora.strftime("%Y-%m-%d %H:%M:%S"), wtg, subsistema, alarme, tempo_parada, tipo_manutencao])

# Criar DataFrame e ordenar cronologicamente
df = pd.DataFrame(dados, columns=["id_parada", "data_hora", "aerogerador", "subsistema", "codigo_alarme", "tempo_parada_horas", "tipo_manutencao"])
df = df.sort_values(by="data_hora").reset_index(drop=True)
df["id_parada"] = df.index + 1 

# Exportar para CSV
df.to_csv("historico_paradas.csv", index=False, encoding='utf-8')

print(f"Arquivo 'historico_paradas.csv' atualizado com sucesso! Total de registros: {len(df)}")