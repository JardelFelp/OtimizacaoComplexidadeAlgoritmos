import json
import matplotlib.pyplot as plt

# Carregar os dados do arquivo JSON
with open('allocation_result_hungarian.json', 'r') as file:
    json_data = json.load(file)

# Ordenar as distâncias
sorted_data = sorted(json_data, key=lambda x: x["distance"])
distances = [entry["distance"] for entry in sorted_data]

# Criar o gráfico de linhas com os índices como eixo X
plt.figure(figsize=(10, 6))
plt.plot(range(len(distances)), distances, marker='o', linestyle='-', label='Distância')

# Adicionar título e rótulos
plt.title('Distâncias Ordenadas dos Participantes às Escolas')
plt.xlabel('Índice (Participantes ordenados por distância)')
plt.ylabel('Distância (metros)')
plt.grid(True)
plt.legend()

# Exibir o gráfico
plt.show()