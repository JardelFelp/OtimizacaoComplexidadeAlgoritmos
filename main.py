import pandas as pd
import numpy as np
import json

# Função para calcular a matriz de custo
def prepare_cost_matrix(participants, schools, distances):
    # Lista para mapear informações das salas disponíveis
    school_room_map = []
    # Matriz de custos para cada participante e sala
    cost_matrix = []

    # Criar o mapeamento de salas com informações de capacidade, tipo de prova e distrito
    for school in schools:
        for room in school["rooms"]:
            school_room_map.append({
                "school_id": school["id"],       # ID da escola
                "room_id": room["id"],           # ID da sala
                "capacity": room["capacity"],    # Capacidade da sala
                "type_of_test": room["type_of_test"],  # Tipo de prova compatível com a sala
                "district_id": school["district_id"]  # Distrito onde a escola está localizada
            })

    # Preencher matriz de custos para cada participante
    for participant in participants:
        participant_cost = []  # Custos para este participante
        for room in school_room_map:
            if participant["type_of_test"] == room["type_of_test"]:  # Verificar compatibilidade do tipo de prova
                try:
                    # Obter a distância do distrito do participante para o distrito da sala
                    dist = distances.loc[participant["district_id"], room["district_id"]]
                    participant_cost.append(float(dist))  # Adicionar custo baseado na distância
                except KeyError:
                    # Caso o distrito não exista na matriz, custo infinito
                    participant_cost.append(np.inf)
            else:
                # Custo infinito se o tipo de prova não for compatível
                participant_cost.append(np.inf)
        cost_matrix.append(participant_cost)  # Adicionar custos do participante à matriz
    return np.array(cost_matrix), school_room_map  # Retornar matriz de custos e mapeamento de salas

# Função para alocar participantes às salas com fallback
def allocate_participants_with_fallback(participants, schools, distances):
    # Obter matriz de custos e mapeamento de salas
    cost_matrix, school_room_map = prepare_cost_matrix(participants, schools, distances)
    room_usage = [0] * len(school_room_map)  # Lista para rastrear o uso atual de cada sala
    assignments = []  # Lista final de alocações

    # Iterar sobre cada participante para encontrar a melhor sala
    for participant_idx, participant in enumerate(participants):
        best_room_idx = None  # Índice da melhor sala
        best_cost = np.inf    # Melhor custo (menor distância)

        # Iterar sobre as salas para encontrar a melhor alocação
        for room_idx, cost in enumerate(cost_matrix[participant_idx]):
            if cost < best_cost and room_usage[room_idx] < school_room_map[room_idx]["capacity"]:
                # Atualizar melhor sala se o custo for menor e a sala tiver capacidade disponível
                best_cost = cost
                best_room_idx = room_idx

        if best_room_idx is not None and best_cost < 9999:
            # Se foi encontrada uma sala válida
            room_details = school_room_map[best_room_idx]  # Detalhes da sala selecionada
            assignments.append({
                "participant_id": participant["id"],      # ID do participante
                "district_id": participant["district_id"],  # Distrito do participante
                "school_id": room_details["school_id"],    # ID da escola
                "room_id": room_details["room_id"],        # ID da sala
                "type_of_test": participant["type_of_test"],  # Tipo de prova
                "distance": best_cost  # Distância para a sala
            })
            room_usage[best_room_idx] += 1  # Atualizar uso da sala
        else:
            # Se nenhuma sala foi encontrada, adicionar fallback
            assignments.append({
                "participant_id": participant["id"],      # ID do participante
                "district_id": participant["district_id"],  # Distrito do participante
                "school_id": -2,                           # ID especial para fallback
                "room_id": -2,                             # Sala especial para fallback
                "type_of_test": participant["type_of_test"],  # Tipo de prova
                "distance": 9999  # Distância indicando fallback
            })
    return assignments  # Retornar lista de alocações

# Carregar dados
distance_matrix = pd.read_csv("distance_matrix.csv", index_col=0)  # Carregar matriz de distâncias
with open("participants.json", "r") as f:
    participants = json.load(f)  # Carregar lista de participantes
with open("schools.json", "r") as f:
    schools = json.load(f)  # Carregar lista de escolas

# Ajustar índices da matriz de distâncias para números
district_mapping = {name: idx for idx, name in enumerate(distance_matrix.index)}  # Mapear distritos para índices numéricos
distance_matrix = distance_matrix.rename(index=district_mapping, columns=district_mapping)  # Renomear índices e colunas

# Remover duplicatas nos índices da matriz de distâncias
distance_matrix = distance_matrix.loc[~distance_matrix.index.duplicated(keep='first')]
distance_matrix = distance_matrix.loc[:, ~distance_matrix.columns.duplicated(keep='first')]

# Adicionar distritos ausentes na matriz de distâncias, se necessário
missing_districts = set(participant["district_id"] for participant in participants) - set(distance_matrix.index)
for missing in missing_districts:
    # Adicionar valores padrão para distritos ausentes
    distance_matrix.loc[missing] = 9999999
    distance_matrix[missing] = 9999999
    distance_matrix.loc[missing, missing] = 0

# Alocar participantes às salas
assignments = allocate_participants_with_fallback(participants, schools, distance_matrix)

# Verificar se todos os participantes foram alocados
total_participants = len(participants)  # Número total de participantes

# Salvar somente os participantes alocados em salas reais
with open("allocation_result.json", "w") as f:
    json.dump([a for a in assignments if a["school_id"] != -2], f, indent=4)  # Salvar alocações reais no arquivo

print("Alocações salvas em 'allocation_result.json'.")