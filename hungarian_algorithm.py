import pandas as pd
import numpy as np
import json
from scipy.optimize import linear_sum_assignment

def allocate_participants(participants, rooms, distance_matrix):
    allocation = []
    remaining_participants = participants.copy()

    while remaining_participants:
        cost_matrix = np.full((len(remaining_participants), len(rooms)), 99999)  # Grande valor como custo inicial

        # Criar matriz de custos com base nas distâncias e compatibilidades
        for i, participant in enumerate(remaining_participants):
            for j, room in enumerate(rooms):
                if room["current_capacity"] < room["capacity"]:
                    if room["type_of_test"] == participant["type_of_test"]:
                        cost_matrix[i][j] = distance_matrix.at[participant["district_id"], room["district_id"]]
                    else:
                        # Penalidade para salas não compatíveis
                        cost_matrix[i][j] = distance_matrix.at[participant["district_id"], room["district_id"]] + 10000

        # Verificar se há linhas ou colunas completamente inviáveis
        if np.all(cost_matrix == 99999):
            print("Erro: Todos os custos são inviáveis. Revisar matriz de distâncias e compatibilidade.")
            break

        # Aplicar o Algoritmo Húngaro
        row_ind, col_ind = linear_sum_assignment(cost_matrix)

        # Alocar participantes
        allocated_indices = set()
        for participant_idx, room_idx in zip(row_ind, col_ind):
            if cost_matrix[participant_idx][room_idx] < 99999:  # Apenas processar alocações válidas
                participant = remaining_participants[participant_idx]
                room = rooms[room_idx]
                distance = cost_matrix[participant_idx][room_idx]

                # Atualizar capacidade da sala
                room["current_capacity"] += 1

                # Salvar alocação no formato solicitado
                allocation.append({
                    "participant_id": participant["id"],
                    "district_id": participant["district_id"],
                    "school_id": room["school_id"],
                    "room_id": room["id"],
                    "type_of_test": participant["type_of_test"],
                    "distance": int(distance)
                })

                allocated_indices.add(participant_idx)

        # Remover participantes alocados
        remaining_participants = [p for idx, p in enumerate(remaining_participants) if idx not in allocated_indices]

    return allocation

# Função principal para carregar os dados e executar a alocação
def main(participants_file, districts_file, distances_file):
    # Carregar arquivos
    with open(participants_file, 'r') as f:
        participants = json.load(f)

    with open(districts_file, 'r') as f:
        districts = json.load(f)

    distance_matrix = pd.read_csv(distances_file, index_col=0)
    distance_matrix.index = range(len(distance_matrix))
    distance_matrix.columns = range(len(distance_matrix.columns))

    # Criar lista de salas
    rooms = []
    for district in districts:
        for school in district["schools"]:
            for room in school["rooms"]:
                rooms.append({
                    "id": room["id"],
                    "school_id": school["id"],
                    "district_id": district["id"],
                    "type_of_test": room["type_of_test"],
                    "capacity": room["capacity"],
                    "current_capacity": 0
                })

    # Executar alocação
    allocation = allocate_participants(participants, rooms, distance_matrix)

    # Resumo da alocação
    total_allocated = len(allocation)
    print(f"Total de participantes alocados: {total_allocated}")
    return allocation

# Arquivos de entrada
participants_file = "participants.json"
districts_file = "districts_schools.json"
distances_file = "distance_matrix.csv"

# Executar o algoritmo
allocation = main(participants_file, districts_file, distances_file)

with open("allocation_result_hungarian.json", "w") as output_file:
    json.dump(allocation, output_file, indent=4)