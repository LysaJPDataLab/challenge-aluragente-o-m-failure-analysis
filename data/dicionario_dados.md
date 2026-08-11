# 📖 Dicionário de Dados - Challenge AlurAgente (O&M Failure Analysis)

Este diretório contém os conjuntos de dados simulados que representam a operação e manutenção de um complexo eólico fictício composto por 30 aerogeradores (WTG-01 a WTG-30) durante o período de 12 meses (Ano 2025).

Os dados foram modelados para refletir a realidade de dois sistemas distintos que se relacionam na rotina de confiabilidade: o sistema SCADA (automação e alarmes) e o sistema CMMS/ERP (gestão de manutenção e ordens de serviço).

---

## 1. Tabela: `historico_paradas_wtg.csv`
Representa os logs gerados automaticamente pelo sistema de supervisão (SCADA). Registra todas as indisponibilidades das máquinas, sejam elas desarmes do sistema ou paradas manuais para intervenção.

* **`id_parada`** (Int): Chave primária. Identificador único de cada evento de parada.
* **`data_hora_inicio`** (Datetime): Data e horário exatos em que a turbina parou de gerar energia.
* **`data_hora_fim`** (Datetime): Data e horário exatos em que a turbina retornou à operação.
* **`aerogerador`** (String): Identificação do ativo (WTG-01 a WTG-30).
* **`subsistema`** (String): Componente ou área afetada (ex: Pitch System, Yaw System, Gearbox, etc.).
* **`codigo_alarme`** (String): Código numérico de falha gerado pelo SCADA.
* **`descricao_alarme`** (String): Descrição técnica do alarme ou motivo da parada.
* **`tempo_parada_horas`** (Float): Tempo total de indisponibilidade (Downtime) calculado em horas.
* **`tipo_parada`** (String): Classificação do evento. Pode ser `TRIP` (desarme forçado automático), `Corrective` (parada manual para correção) ou `Preventive` (parada manual programada).

---

## 2. Tabela: `ordens_servico_wtg.csv`
Representa os apontamentos do sistema de gestão de manutenção. Contém as informações das Ordens de Serviço (OS) que são inseridas diariamente na plataforma pela equipe de campo após a execução das atividades nas turbinas.

* **`id_ordem_servico`** (String): Chave primária. Código identificador da OS (ex: WO-1001).
* **`id_parada_scada`** (Int): **Chave Estrangeira**. Relaciona esta Ordem de Serviço ao evento exato de parada na tabela `historico_paradas_wtg.csv`.
* **`aerogerador`** (String): Identificação do ativo onde o serviço foi executado.
* **`tipo_manutencao`** (String): Classificação da manutenção (`Corrective` ou `Preventive`).
* **`equipe_responsavel`** (String): Frente de trabalho que executou a atividade (ex: Equipe Alpha Mecânica, Especialistas Pás).
* **`qte_tecnicos`** (Int): Número de técnicos de campo alocados na atividade.
* **`homem_hora_trabalhada`** (Float): Total de horas ativas de trabalho investidas pela equipe (HH).
* **`status_ordem`** (String): Situação atual da OS (ex: Concluída, Aguardando Peça).
* **`custo_materiais_brl`** (Float): Custo estimado (em Reais) das peças ou insumos utilizados.
* **`pecas_substituidas`** (String): Descrição dos principais componentes trocados durante a intervenção.

---

## 🔗 Relacionamento (Modelo de Dados)
O modelo segue uma estrutura relacional simples (1:1 ou 1:0), onde os dados de supervisão conversam com os dados de manutenção:

A coluna `id_parada` da tabela SCADA (`historico_paradas_wtg.csv`) liga-se à coluna `id_parada_scada` da tabela de manutenção (`ordens_servico_wtg.csv`). 

* **Nota Técnica:** Nem todo registro no SCADA possui uma Ordem de Serviço correspondente, pois os eventos do tipo `TRIP` (desarmes rápidos ou resets remotos que não exigem deslocamento) não geram apontamento da equipe de campo.
