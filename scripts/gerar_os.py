import pandas as pd
import random
import numpy as np

print("Lendo histórico de paradas do SCADA...")
# Carregar a base de SCADA existente
df_paradas = pd.read_csv('historico_paradas_wtg.csv')

# Filtrar apenas as paradas que geraram intervenção da equipe de campo
df_manutencao = df_paradas[df_paradas['tipo_parada'].isin(['Preventive', 'Corrective'])].copy()

wo_data = []
wo_counter = 1001

equipes = [
    'Equipe Alpha (Mecânica)', 
    'Equipe Beta (Elétrica)', 
    'Equipe Gama (Geral)', 
    'Especialistas (Alta Tensão)', 
    'Especialistas (Pás)'
]

print(f"Gerando Ordens de Serviço para {len(df_manutencao)} intervenções...")

for _, row in df_manutencao.iterrows():
    id_parada = row['id_parada']
    wtg = row['aerogerador']
    tipo = row['tipo_parada']
    subsistema = row['subsistema']
    tempo_parada_total = row['tempo_parada_horas']

    # Gerar ID da Ordem de Serviço
    id_wo = f"WO-{wo_counter}"
    wo_counter += 1

    # Definir quantidade de técnicos na frente de trabalho
    num_tecnicos = random.choice([3, 4]) if tipo == 'Preventive' else random.choice([2, 3])
    
    # Atribuir equipe baseada na especialidade do subsistema
    if 'Pitch' in subsistema or 'Pás' in subsistema:
        equipe = 'Especialistas (Pás)' if random.random() > 0.5 else 'Equipe Alpha (Mecânica)'
    elif 'Electrical' in subsistema or 'Converter' in subsistema or 'Generator' in subsistema:
        equipe = 'Equipe Beta (Elétrica)' if random.random() > 0.3 else 'Especialistas (Alta Tensão)'
    else:
        equipe = random.choice(['Equipe Alpha (Mecânica)', 'Equipe Gama (Geral)'])

    # Calcular Homem-Hora (HH) efetivo de trabalho (menor que o tempo total de indisponibilidade)
    if tipo == 'Preventive':
        # Preventiva padrão leva aprox 3 dias x 10h de turno = 30h ativas por técnico
        hh = round(num_tecnicos * random.uniform(25, 32), 1) 
        custo = round(random.uniform(5000, 15000), 2)
        pecas = "Óleo lubrificante, filtros de óleo, graxa, consumíveis gerais"
    else:
        # Corretiva: tempo ativo de trabalho é uma fração do tempo parado (descontando logística, clima, etc)
        fator_trabalho = random.uniform(0.3, 0.8)
        hh = round(tempo_parada_total * num_tecnicos * fator_trabalho, 1)
        custo = round(random.uniform(1500, 60000), 2)
        
        # Sortear peças trocadas com base no subsistema realística
        if 'Pitch' in subsistema: pecas = random.choice(['Motor de Pitch', 'Bateria de Backup', 'Encoder', 'Nenhuma (Ajuste/Calibração)'])
        elif 'Yaw' in subsistema: pecas = random.choice(['Motor de Yaw', 'Pastilhas de Freio', 'Sensor de Posição', 'Nenhuma (Ajuste)'])
        elif 'Hydraulic' in subsistema: pecas = random.choice(['Válvula Proporcional', 'Bomba Hidráulica', 'Mangueira de Alta Pressão', 'Acumulador de Pressão'])
        elif 'Generator' in subsistema: pecas = random.choice(['Rolamento', 'Escovas do Anel Coletor', 'Cooler / Trocador de Calor'])
        elif 'Gearbox' in subsistema: pecas = random.choice(['Filtro de Óleo', 'Bomba de Lubrificação', 'Sensor de Vibração'])
        elif 'Converter' in subsistema: pecas = random.choice(['Módulo IGBT', 'Placa de Controle', 'Fusível de Potência'])
        else: pecas = 'Fiação / Componentes menores'

    status = random.choices(['Concluída', 'Encerrada com Ressalva', 'Aguardando Peça'], weights=[0.85, 0.10, 0.05])[0]

    wo_data.append({
        'id_ordem_servico': id_wo,
        'id_parada_scada': id_parada, # Chave Estrangeira
        'aerogerador': wtg,
        'tipo_manutencao': tipo,
        'equipe_responsavel': equipe,
        'qte_tecnicos': num_tecnicos,
        'homem_hora_trabalhada': hh,
        'status_ordem': status,
        'custo_materiais_brl': custo,
        'pecas_substituidas': pecas
    })
    
df_wo = pd.DataFrame(wo_data)

# Exportar para CSV
df_wo.to_csv('ordens_servico_wtg.csv', index=False, encoding='utf-8-sig')

print(f"Sucesso! Arquivo 'ordens_servico_wtg.csv' criado com {len(df_wo)} Ordens de Serviço.")
