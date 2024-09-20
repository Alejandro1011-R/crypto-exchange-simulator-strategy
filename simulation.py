
import numpy as np
from typing import List
import matplotlib.pyplot as plt
from agents import *
from gemini_ai import *  # Asegúrate de que este módulo exista y esté correctamente implementado
import random  # Asegúrate de importar random si no está ya importado

class Simulation:
    def __init__(self, num_steps: int, agents: List[Agente], market: Market, parser, sentiment_analyzer, reddit_instance):
        self.num_steps = num_steps
        self.agents = agents
        self.market = market
        self.price_history = {crypto: [market.cryptocurrencies[crypto].price] for crypto in market.cryptocurrencies}
        self.volume_history = {crypto: [] for crypto in market.cryptocurrencies}
        self.sentiment_history = {crypto: [] for crypto in market.cryptocurrencies}
        self.agent_performances = {agent.nombre: [] for agent in agents}
        self.parser = parser
        self.sentiment_analyzer = sentiment_analyzer
        self.reddit_instance = reddit_instance
        self.precomputed_sentiments = {crypto: [] for crypto in market.cryptocurrencies}

    def run(self):
        agent_gen = 1
        No_Agente = 0
        count = 1

        subreddits_list = {}

        # post_limit = 10

        # for crypto in self.market.cryptocurrencies:
        #     subreddits_list[crypto] = ['CryptoCurrency', 'CryptoTrading', 'CryptoInvesting', crypto]

        # *** Precomputar los sentimientos antes de iniciar la simulación ***
        for crypto in self.market.cryptocurrencies:
            # Obtener todos los sentimientos de una sola vez
            # sentiment = Process(
            #     self.sentiment_analyzer,
            #     self.reddit_instance,
            #     subreddits_list[crypto],
            #     post_limit,
            #     crypto
            # )
            # Almacenar el sentimiento precomputado para todos los pasos
            # self.precomputed_sentiments[crypto] = [sentiment] * self.num_steps
            self.precomputed_sentiments[crypto] = np.random.normal(-1,1)


        for step in range(self.num_steps):
            # Asignar los sentimientos precomputados en lugar de calcularlos
            for crypto in self.market.cryptocurrencies:
                self.sentiment_history[crypto].append(self.precomputed_sentiments[crypto])

            # *** Actualizar las creencias de los agentes con el estado actual del mercado ***
            for agent in self.agents:
                agent.update_beliefs(self.market, self.sentiment_history)

            # Los agentes toman decisiones y ejecutan operaciones
            for agent in self.agents:
                accion, resultado, crypto_decision = agent.tomar_decision(self.market)  # Usar el método tomar_decision de Agente
                agent.ejecutar_accion(accion, self.market, crypto_decision)  # Cambiar
                agent.actualizar_ganancia(self.market)
                agent.ciclo = agent.ciclo+1
                self.agent_performances[agent.nombre].append(agent.historia_ganancia[-1])

                # Ejecutar la acción basada en la decisión tomada por el agente
                if accion and resultado:
                    self.agent_performances[agent.nombre].append(resultado[0])  # Asumiendo que resultado es una tupla (valor, cripto)

            # Actualiza el estado del mercado
            self.market.update(self.sentiment_history)

            # Algoritmo Genético cada 10 pasos
            if count == 10:
                count = 1
                nuevos, peores = self.algoritmo_genetico(self.market, self.agents, count)
                # Registra datos para análisis posterior
                print("**** Nuevos agentes y reglas *****")
                for agente in nuevos:
                    print(agente.nombre)
                    print(agente.reglas)

                for agente in peores:
                    self.agents.remove(agente)

                for agente in nuevos:
                    nuevo_nombre = f'agente {No_Agente} generación {agent_gen}'
                    nuevo_agente = Agente(nuevo_nombre, agente.reglas, self.parser)
                    self.agents.append(nuevo_agente)
                    self.agent_performances[nuevo_nombre] = []  # Inicializa el desempeño del nuevo agente
                    No_Agente += 1

                agent_gen += 1
                No_Agente = 0

            else:
                count += 1

            self._record_data()
            # Imprime información del paso actual
            self._print_step_info(step)

    def mutar_regla(self, regla):
        # Separar la regla en 'SI', condiciones, 'ENTONCES', acción
        partes = regla.split(" ENTONCES ")
        if len(partes) != 2:
            # Regla mal formada, no puede mutar
            print(f"Regla mal formada, no se puede mutar: {regla}")
            return regla

        condiciones = partes[0].replace("SI ", "")
        accion = partes[1]

        # Split condiciones en palabras
        condiciones_partes = condiciones.split(" ")

        # Mutar condiciones
        valores_precio_volumen = ["alto", "bajo", "medio"]
        valores_sentimiento = ["negativo", "neutro", "positivo"]

        for i, palabra in enumerate(condiciones_partes):
            if palabra in valores_precio_volumen:
                nuevas_valores = [valor for valor in valores_precio_volumen if valor != palabra]
                condiciones_partes[i] = random.choice(nuevas_valores)
            elif palabra in valores_sentimiento:
                nuevas_valores = [valor for valor in valores_sentimiento if valor != palabra]
                condiciones_partes[i] = random.choice(nuevas_valores)

        condiciones_mutadas = " ".join(condiciones_partes)

        # Mutar la acción
        acciones = ["comprar", "vender", "mantener"]
        accion_mutada = accion
        if accion in acciones:
            accion_mutada = random.choice([a for a in acciones if a != accion])

        # Reconstruir la regla asegurando la estructura correcta
        regla_mutada = f"SI {condiciones_mutadas} ENTONCES {accion_mutada}"
        return regla_mutada

    def crossover(self, parent1, parent2, crossover_rate=0.5):
        # Asegúrate de que ambos padres tengan el mismo tamaño

        '''if len(parent1) != len(parent2):
            raise ValueError("Los padres deben tener el mismo tamaño")'''
        # Trunca las listas al tamaño del padre más corto si no tienen el mismo tamaño
        min_len = min(len(parent1), len(parent2))
        parent1, parent2 = parent1[:min_len], parent2[:min_len]

        child1 = []
        child2 = []

        # Iterar sobre cada gen/law en los padres
        for i in range(len(parent1)):
            if random.random() < crossover_rate:
                # Tomar el gen/law del primer padre para el primer hijo, y del segundo para el segundo hijo
                child1.append(parent1[i])
                child2.append(parent2[i])
            else:
                # Tomar el gen/law del segundo padre para el primer hijo, y del primero para el segundo hijo
                child1.append(parent2[i])
                child2.append(parent1[i])

        return child1, child2

    def validar_regla(self, regla):
        # Intenta analizar la regla para verificar su validez
        try:
            parsed_conditions, accion = self.parser.parse_rule(regla)
            return True
        except ValueError as e:
            # Imprime un mensaje de error si la regla no es válida
            print(f"Regla inválida: {regla}. Error: {e}")
            return False

  

    # Función de Supervivencia Sigmoide Basada en Edad
    def probabilidad_supervivencia(age, fitness, k=0.1, t=50):
        
        return fitness / (1 + np.exp(k * (age - t)))

    def algoritmo_genetico(self, contexto, agentes, tasa_mutacion=0.1):
        nuevos_agentes = []

        # Evaluar desempeño de cada agente
        desempeno_agentes = [(agente,probabilidad_supervivencia(agente.ciclo,agente.evaluar_desempeno(contexto)))for agente in agentes]

        # Ordenar los agentes por desempeño (mayor desempeño primero)
        desempeno_agentes.sort(key=lambda x: x[1], reverse=True)  # Asumiendo que evaluar_desempeno devuelve (nombre, desempeño)

        # Caso especial: Solo hay dos agentes
        if len(agentes) <= 3:
            mejor_agente = desempeno_agentes[0]  # Agente con mejor desempeño
            peor_agente = desempeno_agentes[1]   # Agente con peor desempeño

            # Realizar crossover y mutación entre los dos agentes
            nuevas_reglas_padre1, nuevas_reglas_padre2 = self.crossover(mejor_agente[0].reglas, peor_agente[0].reglas)

            # Aplicar mutación a las reglas con una probabilidad definida
            if random.random() < tasa_mutacion:
                nuevas_reglas_padre1 = [self.mutar_regla(regla) for regla in nuevas_reglas_padre1]
            if random.random() < tasa_mutacion:
                nuevas_reglas_padre2 = [self.mutar_regla(regla) for regla in nuevas_reglas_padre2]

            # Validar reglas y generar un nuevo agente para reemplazar al peor
            if self.validar_regla(" ".join(nuevas_reglas_padre2)):
                nuevo_agente = Agente(
                    f'agente {peor_agente[0].nombre}',
                    nuevas_reglas_padre2,
                    self.parser,
                    capital_inicial=peor_agente[0].capital_inicial  # Mantener el capital inicial
                )
                nuevos_agentes.append(nuevo_agente)

            # Retornar el nuevo agente creado y el agente reemplazado
            return nuevos_agentes, [peor_agente[0]]

        # Caso general: Más de dos agentes
        else:
            corte = len(desempeno_agentes) // 2
            mejores = desempeno_agentes[:corte]  # Mejores agentes
            peores = desempeno_agentes[corte:]   # Peores agentes (serán reemplazados)

            # Realiza crossover y mutación en las reglas seleccionadas
            while len(nuevos_agentes) < len(peores):
                # Selecciona dos padres al azar de los mejores
                padres = random.sample(mejores, 2)
                padre1, padre2 = padres[0][0], padres[1][0]

                # Realizar crossover (cruce) entre las reglas de los padres
                nuevas_reglas_padre1, nuevas_reglas_padre2 = self.crossover(padre1.reglas, padre2.reglas)

                # Mutar reglas con probabilidad de tasa_mutacion
                if random.random() < tasa_mutacion:
                    nuevas_reglas_padre1 = [self.mutar_regla(regla) for regla in nuevas_reglas_padre1]
                if random.random() < tasa_mutacion:
                    nuevas_reglas_padre2 = [self.mutar_regla(regla) for regla in nuevas_reglas_padre2]

                # Validar reglas y crear nuevos agentes
                if self.validar_regla(" ".join(nuevas_reglas_padre1)):
                    nuevo_agente1 = Agente(
                        f'agente {len(nuevos_agentes)}',
                        nuevas_reglas_padre1,
                        self.parser,
                        capital_inicial=padre1.capital_inicial  # Mantener el capital inicial
                    )
                    nuevos_agentes.append(nuevo_agente1)
                    self.agent_performances[nuevo_agente1.nombre] = []  # Inicializa el desempeño

                if self.validar_regla(" ".join(nuevas_reglas_padre2)):
                    nuevo_agente2 = Agente(
                        f'agente {len(nuevos_agentes)}',
                        nuevas_reglas_padre2,
                        self.parser,
                        capital_inicial=padre2.capital_inicial  # Mantener el capital inicial
                    )
                    nuevos_agentes.append(nuevo_agente2)
                    self.agent_performances[nuevo_agente2.nombre] = []  # Inicializa el desempeño

            # Retornar los nuevos agentes creados y los agentes que fueron reemplazados
            return nuevos_agentes, [agente[0] for agente in peores]


    def _print_step_info(self, step):
        print(f"Step {step}: Timestamp = {self.market.timestamp}")
        for crypto_name, crypto in self.market.cryptocurrencies.items():
            # print(f"  {crypto_name}: Price = ${crypto.price:.2f}, Volume = {crypto.volume:.2f}")
            print(f"  {crypto_name}: Price = ${crypto.price:.2f}")

    def _record_data(self):
        for crypto_name, crypto in self.market.cryptocurrencies.items():
            self.price_history[crypto_name].append(crypto.price)
            print(f'VOLUMEN: {crypto.volume}')
            self.volume_history[crypto_name].append(crypto.volume)

    def plot_results(self):
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 18))

        # Graficar precios
        for crypto, prices in self.price_history.items():
            ax1.plot(prices, label=crypto)
        ax1.set_title('Precio de las criptomonedas')
        ax1.set_xlabel('Pasos de tiempo')
        ax1.set_ylabel('Precio')
        ax1.legend()

        # Graficar sentimiento del mercado
        for crypto, sentiment in self.sentiment_history.items():
            ax2.plot(sentiment, label=crypto)  # Graficar cada criptomoneda
        ax2.set_title('Sentimiento del mercado')
        ax2.set_xlabel('Pasos de tiempo')
        ax2.set_ylabel('Sentimiento')
        ax2.legend()  # Añadir leyenda para identificar cada criptomoneda

        # Graficar rendimiento de los agentes
        for agent in self.agents:
            ax3.plot(self.agent_performances[agent.nombre], label=agent.nombre)
        ax3.set_title('Rendimiento de los agentes')
        ax3.set_xlabel('Pasos de tiempo')
        ax3.set_ylabel('Rendimiento (%)')
        ax3.legend()

        plt.tight_layout()
        plt.show()

    def get_summary(self):
        summary = {}
        for crypto_name, prices in self.price_history.items():
            summary[crypto_name] = {
                'initial_price': prices[0],
                'final_price': prices[-1],
                'price_change': (prices[-1] - prices[0]) / prices[0] * 100,
                'max_price': max(prices),
                'min_price': min(prices),
                'total_volume': sum(self.volume_history[crypto_name])
            }

        # Añadir resumen del rendimiento de los agentes
        summary['agent_performance'] = {}
        for agent in self.agents:
            if len(agent.historia_ganancia) > 0:
                final_value = agent.historia_ganancia[-1]
                initial_value = agent.capital_inicial
                performance = (final_value - initial_value) / initial_value * 100
                summary['agent_performance'][agent.nombre] = {
                    'initial_value': initial_value,
                    'final_value': final_value,
                    'performance': performance,
                    'max_performance': (max(agent.historia_ganancia) - initial_value) / initial_value * 100,
                    'min_performance': (min(agent.historia_ganancia) - initial_value) / initial_value * 100,
                    'avg_performance': (sum(agent.historia_ganancia) / len(agent.historia_ganancia) - initial_value) / initial_value * 100,
                    'rules': agent.reglas
                }

        return summary

    def get_performance(self):

        summary = self.get_summary()

        print("Resumen de la simulación:")
        for crypto, data in summary.items():
            if crypto != 'agent_performance':
                print(f"{crypto}:")
                for key, value in data.items():
                    print(f"  {key}: {value}")

        print("\nRendimiento de los agentes:")
        for agent_name, performance in summary['agent_performance'].items():
            print(f"{agent_name}:")
            for key, value in performance.items():
                # Línea 328 modificada para manejar correctamente el formateo
                if key in ['performance', 'max_performance', 'min_performance', 'avg_performance']:
                    print(f"  {key}: {value:.2%}")
                else:
                    print(f"  {key}: {value}")

        # Determinar la estrategia más efectiva
        best_agent = max(summary['agent_performance'], key=lambda x: summary['agent_performance'][x]['performance'])
        print(f"\nLa estrategia más efectiva fue: {best_agent}\n\n")

        return best_agent
