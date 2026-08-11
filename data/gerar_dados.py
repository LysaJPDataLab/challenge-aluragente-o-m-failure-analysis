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
    "Sensors": [
        "801 - Anemometer mismatch",
        "802 - Wind vane error",
        "803 - Ice detection on blades",
        "804 - Ambient temperature out of range"
    ]
}

dados = []

# =================================================================
# 1. PLANEJAMENTO DE PREVENTIVAS (Regra: Max 2 WTG/dia, Exceto aos Domingos)
# =================================================================
def gerar_slots_manutencao(data_inicio, data_fim):
    """Gera uma lista de datas disponíveis, excluindo domingos, com 2 vagas por dia."""
    slots = []
    atual = data_inicio
    while atual <= data_fim:
        if atual.weekday() != 6:  # 0=Segunda ... 6=Domingo
            slots.extend([atual, atual])  # Duas equipes disponíveis por dia
        atual += timedelta(days=1)
    return slots

# Definindo as janelas do 1º e 2º semestre
slots_s1 = gerar_slots_manutencao(datetime(2025, 1, 1), datetime(2025, 5, 31))
slots_s2 = gerar_slots_manutencao(datetime(2025, 7, 1), datetime(2025, 11, 30))

# Embaralhar os slots para distribuir aleatoriamente entre as WTGs
random.shuffle(slots_s1)
random.shuffle(slots_s2)

# Selecionar as exatas 30 datas necessárias para cada semestre
datas_prev_s1 = slots_s1[:NUM_WTGS]
datas_prev_s2 = slots_s2[:NUM_WTGS]

for idx, wtg in enumerate(wtgs):
    # --- 1ª Preventiva ---
    data_base_1 = datas_prev_s1[idx]
    hora_inicio_1 = random.randint(7, 9)  # Início do expediente da manhã
    inicio_1 = data_base_1 + timedelta(hours=hora_inicio_1)
    fim_1 = inicio_1 + timedelta(hours=72)  # Duração de 3 dias
    
    dados.append({
        "data_hora_inicio": inicio_1.strftime("%Y-%m-%d %H:%M:%S"),
        "data_hora_fim": fim_1.strftime("%Y-%m-%d %H:%M:%S"),
        "aerogerador": wtg,
        "subsistema": "PCM-PROG",
        "codigo_alarme": "001",
        "descricao_alarme": "manual stop_maintenance",
        "tempo_parada_horas": 72.0,
        "tipo_parada": "Preventive"
    })
    
    # --- 2ª Preventiva ---
    data_base_2 = datas_prev_s2[idx]
    hora_inicio_2 = random.randint(7, 9)
    inicio_2 = data_base_2 + timedelta(hours=hora_inicio_2)
    fim_2 = inicio_2 + timedelta(hours=72)
    
    dados.append({
        "data_hora_inicio": inicio_2.strftime("%Y-%m-%d %H:%M:%S"),
        "data_hora_fim": fim_2.strftime("%Y-%m-%d %H:%M:%S"),
        "aerogerador": wtg,
        "subsistema": "PCM-PROG",
        "codigo_alarme": "001",
        "descricao_alarme": "manual stop_maintenance",
        "tempo_parada_horas": 72.0,
        "tipo_parada": "Preventive"
    })

# =================================================================
# 2. GERAÇÃO DE EVENTOS NÃO PROGRAMADOS (Forçadas e Corretivas)
# =================================================================
eventos_restantes = NUM_REGISTROS - len(dados)

for _ in range(eventos_restantes):
    dias_aleatorios = random.randint(0, 364)
    horas_aleatorias = random.randint(0, 23)
    minutos_aleatorios = random.randint(0, 59)
    
    data_hora_inicio = DATA_INICIO + timedelta(days=dias_aleatorios, hours=horas_aleatorias, minutes=minutos_aleatorios)
    wtg = random.choice(wtgs)
    
    is_manual_repair = np.random.choice([True, False], p=[0.2, 0.8])
    
    if is_manual_repair:
        subsistema = "PCM-CORR"
        codigo = "002"
        descricao = "manual stop_repair"
        tempo_parada = round(random.uniform(2.0, 36.0), 1)
        tipo = "Corrective"
    else:
        subsistema = random.choice(list(subsistemas_alarmes.keys()))
        alarme_completo = random.choice(subsistemas_alarmes[subsistema])
        codigo, descricao = alarme_completo.split(" - ")
        
        tempo_parada = round(np.random.exponential(scale=8.5) + 0.5, 1)
        if tempo_parada > 120:  
            tempo_parada = 120.0
        tipo = "TRIP"
            
    data_hora_fim = data_hora_inicio + timedelta(hours=tempo_parada)
    
    dados.append({
        "data_hora_inicio": data_hora_inicio.strftime("%Y-%m-%d %H:%M:%S"),
        "data_hora_fim": data_hora_fim.strftime("%Y-%m-%d %H:%M:%S"),
        "aerogerador": wtg,
        "subsistema": subsistema,
        "codigo_alarme": codigo,
        "descricao_alarme": descricao,
        "tempo_parada_horas": tempo_parada,
        "tipo_parada": tipo
    })

# =================================================================
# 3. ORGANIZAÇÃO E EXPORTAÇÃO
# =================================================================
df = pd.DataFrame(dados)

df = df.sort_values(by="data_hora_inicio").reset_index(drop=True)
df.insert(0, "id_parada", df.index + 1)

df.to_csv("historico_paradas_wtg.csv", index=False, encoding='utf-8')

print(f"Arquivo 'historico_paradas_wtg.csv' gerado com sucesso! Total de registros: {len(df)}")
