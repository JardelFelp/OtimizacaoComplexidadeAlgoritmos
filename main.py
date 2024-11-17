import json
import pandas as pd


# Extrai os tipos de teste e as informações das salas disponíveis em cada distrito.
def get_tests_and_rooms(districts):
    types = []
    rooms = []

    for district in districts:
        for school in district["schools"]:
            for room in school["rooms"]:
                # Adiciona os dados da sala à lista de salas
                rooms.append({
                    "district_id": district["id"],
                    "school_id": school["id"],
                    "room_id": room["id"],
                    "type_of_test": room["type_of_test"],
                    "capacity": room["capacity"]
                })

                # Garante que o tipo de teste seja único na lista
                if room["type_of_test"] not in types:
                    types.append(room["type_of_test"])

    return types, rooms


# Retorna o número de escolas em um distrito.
def district_with_schools(district):
    return len(district["schools"])


# Identifica os distritos que possuem escolas oferecendo um determinado tipo de teste.
def get_districts_with_test(rooms, type_of_test):
    return list({room["district_id"] for room in rooms if room["type_of_test"] == type_of_test})


# Calcula a menor distância entre distritos e distritos com escolas que oferecem um determinado tipo de teste.
def calculate_minimum_distance_by_index(distance_matrix, school_district_indices):
    minimum_distances = {}
    for i, district in enumerate(distance_matrix.index):
        # Seleciona as distâncias do distrito atual para os distritos-alvo
        distances_to_schools = distance_matrix.iloc[i, school_district_indices]
        # Calcula a distância mínima
        minimum_distances[i] = int(distances_to_schools.min())
    return minimum_distances


# Ordena os distritos com base na distância mínima para os distritos com escolas.
def order_by_distance(distance_matrix, districts_with_schools):
    # Calcula as distâncias mínimas
    minimum_distances = calculate_minimum_distance_by_index(distance_matrix, districts_with_schools)

    # Ordena os distritos pela distância mínima (decrescente)
    sorted_districts = sorted(minimum_distances.items(), key=lambda x: x[1], reverse=True)

    return [i for i, item in sorted_districts]


# Função principal para realizar a alocação de participantes.
def main():
    # Carrega a matriz de distâncias e os dados de entrada
    distance_matrix = pd.read_csv("distance_matrix.csv", index_col=0)
    districts = json.load(open("districts_schools.json", "r", encoding="utf-8"))
    participants = json.load(open("participants.json", "r", encoding="utf-8"))

    # Processa os tipos de teste e as salas disponíveis
    types_tests, rooms = get_tests_and_rooms(districts)

    # Converte a matriz de distâncias para uma lista
    distance_matrix_items = distance_matrix.to_numpy().tolist()

    result = []  # Lista para armazenar os resultados da alocação

    # Itera sobre cada tipo de teste
    for type_of_test in types_tests:
        # Identifica os distritos com salas disponíveis para o tipo de teste
        districts_with_test = get_districts_with_test(rooms, type_of_test)
        # Ordena os distritos pela distância mínima para as escolas
        district_distance_order = order_by_distance(distance_matrix, districts_with_test)
        # Filtra as salas para o tipo de teste atual
        rooms_with_test = [room for room in rooms if room["type_of_test"] == type_of_test]

        # Itera sobre os distritos ordenados
        for district in district_distance_order:
            # Filtra os participantes do distrito atual
            district_participants = [
                item for item in participants
                if item["district_id"] == district and item["type_of_test"] == type_of_test
            ]

            # Ordena os distritos-alvo com base na distância
            distance_matrix_to_test = sorted([
                (index, item)
                for index, item in enumerate(distance_matrix_items[district])
                if index in districts_with_test
            ], key=lambda x: x[1])

            # Aloca os participantes em salas disponíveis
            for participant in district_participants:
                for test_district_index, distance in distance_matrix_to_test:
                    # Busca uma sala disponível no distrito mais próximo
                    available_room = next(
                        (room for room in rooms_with_test if
                         room["district_id"] == test_district_index and room["capacity"] > 0),
                        None
                    )

                    if available_room:
                        # Realiza a alocação do participante
                        result.append({
                            "participant_id": participant["id"],
                            "district_id": test_district_index,
                            "school_id": available_room["school_id"],
                            "room_id": available_room["room_id"],
                            "type_of_test": type_of_test,
                            "distance": distance
                        })
                        # Reduz a capacidade da sala
                        available_room["capacity"] -= 1
                        break

        # Exibe e salva o resultado final da alocação
        print(json.dumps(result, indent=4))
        with open("allocation_result.json", "w") as output_file:
            json.dump(result, output_file, indent=4)


# Executa a função principal
main()