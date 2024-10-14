import numpy as np
from typing import List, Dict, Optional, Tuple
import pandas as pd
import matplotlib.pyplot as plt
from agents import *  # Importamos el agente BDI actualizado
from market import *
from llm import *
from Rules_Interpreter.rulelexer import RuleLexer
from Rules_Interpreter.ruleparser import RuleParser
from Induction_Motor.Motor import *
from Rules_Interpreter.ruleinterpreter import RuleInterpreter
import random

class Simulation:
    def __init__(self, num_steps: int, agents: List[Agente], market: Market, parser, motor,interpreter, reddit_instance,map):
        self.num_steps = num_steps
        self.agents = agents
        self.market = market
        self.parser = parser
        self.sentiment_analyzer = sentiment_analyzer
        self.reddit_instance = reddit_instance
        self.motor =  motor
        self.inter =  interpreter
        self.map = map
        # Diccionarios para almacenar historiales
        self.price_history = {crypto: [market.cryptocurrencies[crypto].price] for crypto in market.cryptocurrencies}
        self.volume_history = {crypto: [] for crypto in market.cryptocurrencies}
        self.sentiment_history = {crypto: [] for crypto in market.cryptocurrencies}
        self.agent_performances = {agent.nombre: [] for agent in agents}
        self.precomputed_sentiments = {crypto: [] for crypto in market.cryptocurrencies}


        # DataFrames separados para almacenar los mismos datos que los diccionarios
        # 1. Historial de Precios
        # Inicializamos el DataFrame con 'Time' y columnas de precio y volumen para cada criptomoneda
        self.price_history_df = pd.DataFrame(columns=['Time'] +
                                             [f'{crypto}_open' for crypto in market.cryptocurrencies] +
                                             [f'{crypto}_high' for crypto in market.cryptocurrencies] +
                                             [f'{crypto}_low' for crypto in market.cryptocurrencies] +
                                             [f'{crypto}_close' for crypto in market.cryptocurrencies] +
                                             [f'{crypto}_volume' for crypto in market.cryptocurrencies])

        # Añadir la fila inicial
        initial_row = {'Time': 0}
        for crypto in market.cryptocurrencies:
            initial_row[f'{crypto}_open'] = market.cryptocurrencies[crypto].price
            initial_row[f'{crypto}_high'] = market.cryptocurrencies[crypto].price
            initial_row[f'{crypto}_low'] = market.cryptocurrencies[crypto].price
            initial_row[f'{crypto}_close'] = market.cryptocurrencies[crypto].price
            initial_row[f'{crypto}_volume'] = market.cryptocurrencies[crypto].volume
        self.price_history_df = self.price_history_df._append(initial_row, ignore_index=True)

        # 2. Historial de Sentimientos
        self.sentiment_history_df = pd.DataFrame(columns=['Time'] +
                                                 [f'{crypto}_sentiment' for crypto in market.cryptocurrencies])

        # 3. Rendimiento de los Agentes
        self.agent_performances_df = pd.DataFrame(columns=['Time'] + [agent.nombre for agent in agents])
        initial_agent_row = {'Time': 0}
        for agent in agents:
            initial_agent_row[agent.nombre] = 0.0  # Suponemos que la ganancia inicial es 0
        self.agent_performances_df = self.agent_performances_df._append(initial_agent_row, ignore_index=True)

    def run(self):
        agent_gen = 1
        No_Agente = 0
        count = 1

        subreddits_list = {}
        post_limit = 10

        # Configurar subreddits por criptomoneda
        for crypto in self.market.cryptocurrencies:
            subreddits_list[crypto] = ['CryptoCurrency', 'CryptoTrading', 'CryptoInvesting', crypto]

        # # *** Precomputar los sentimientos antes de iniciar la simulación ***
        # for crypto in self.market.cryptocurrencies:
        #     # Obtener todos los sentimientos de una sola vez
        #     sentiment = Process(
        #         self.sentiment_analyzer,
        #         self.reddit_instance,
        #         subreddits_list[crypto],
        #         post_limit,
        #         crypto
        #     )
        #     # Almacenar el sentimiento precomputado para todos los pasos
        #     self.precomputed_sentiments[crypto] = [sentiment] * self.num_steps

        # Precomputar los sentimientos antes de iniciar la simulación
        for crypto in self.market.cryptocurrencies:
            self.precomputed_sentiments[crypto] = [random.uniform(-1, 1) for _ in range(self.num_steps)]

        # Iterar sobre cada paso de la simulación
        for step in range(1, self.num_steps + 1):  # Empezar desde 1 porque 0 es la fila inicial
            # Asignar los sentimientos precomputados

            # if step%100 == 0 or step == 1:
            #     self.precomputed_sentiments = {crypto: [] for crypto in self.market.cryptocurrencies}

            #     for crypto in self.market.cryptocurrencies:
            #         # Obtener todos los sentimientos de una sola vez
            #         sentiment = Process(
            #             self.sentiment_analyzer,
            #             self.reddit_instance,
            #             subreddits_list[crypto],
            #             post_limit,
            #             crypto
            #         )

            #         self.precomputed_sentiments[crypto] =  [float(sentiment) for _ in range(self.num_steps)]





            sentiment_row = {'Time': step}
            for crypto in self.market.cryptocurrencies:
                sentiment = self.precomputed_sentiments[crypto][step - 1]
                self.sentiment_history[crypto].append(sentiment)
                sentiment_row[f'{crypto}_sentiment'] = sentiment
            self.sentiment_history_df = self.sentiment_history_df._append(sentiment_row, ignore_index=True)

            # Actualizar el estado del mercado con los sentimientos actuales
            self.market.update(self.sentiment_history)

            # Los agentes toman decisiones y ejecutan operaciones
            agent_performance_row = {'Time': step}
            for agent in self.agents:
                # El agente realiza su ciclo BDI completo
                agent.action(self.market, self.sentiment_history)

                # Actualizar el rendimiento del agente
                # agent.actualizar_ganancia(self.market)
                ganancia_actual = agent.historia_ganancia[-1]
                self.agent_performances[agent.nombre].append(ganancia_actual)

                # Asignar la ganancia actual al agente en el DataFrame
                agent_performance_row[agent.nombre] = ganancia_actual

            # Añadir la fila de rendimiento de los agentes al DataFrame
            self.agent_performances_df = self.agent_performances_df._append(agent_performance_row, ignore_index=True)

            # Algoritmo Genético cada 10 pasos
            if count == 10:
                count = 1
                nuevos, peores = self.algoritmo_genetico(self.market, self.agents,creencias,self.motor,self.inter)
                # Registrar datos para análisis posterior
                for agente in nuevos:
                    print(agente.nombre)
                    print(agente.reglas)

                for agente in peores:
                    self.agents.remove(agente)

                for agente in nuevos:
                    nuevo_nombre = f'agente {No_Agente} generación {agent_gen}'
                    nuevo_agente = Agente(nuevo_nombre, agente.reglas, self.parser)# ver 
                    self.agents.append(nuevo_agente)
                    self.agent_performances[nuevo_nombre] = []  # Inicializar lista de rendimiento
                    # Añadir columna con NaN para todos los pasos anteriores
                    self.agent_performances_df[nuevo_nombre] = [np.nan] * len(self.agent_performances_df)
                    No_Agente += 1

                agent_gen += 1
                No_Agente = 0
            else:
                count += 1

            # Registrar datos de precios y volúmenes
            self._record_data()

            # Imprimir información del paso actual (opcional)
            # self._print_step_info(step)

    def mutar_regla(self, agcreencias:list,creencias):
        sobrantes = [elemento for elemento in creencias if elemento not in agcreencias]
        agcreencias.append(random.choice(sobrantes))
        return agcreencias
    # def mutar_regla(self, regla,creencias):
    #     # Separar la regla en 'SI', condiciones, 'ENTONCES', acción
    #     partes = regla.split(" ENTONCES ")
    #     if len(partes) != 2:
    #         # Regla mal formada, no puede mutar
    #         # print(f"Regla mal formada, no se puede mutar: {regla}")
    #         return regla

    #     condiciones = partes[0].replace("SI ", "")
    #     accion = partes[1]

    #     # Separar condiciones en palabras
    #     condiciones_partes = condiciones.split(" ")

    #     # Mutar condiciones
    #     valores_precio_volumen = ["alto", "bajo", "medio"]
    #     valores_sentimiento = ["negativo", "neutro", "positivo"]

    #     for i, palabra in enumerate(condiciones_partes):
    #         if palabra in valores_precio_volumen:
    #             nuevas_valores = [valor for valor in valores_precio_volumen if valor != palabra]
    #             condiciones_partes[i] = random.choice(nuevas_valores)
    #         elif palabra in valores_sentimiento:
    #             nuevas_valores = [valor for valor in valores_sentimiento if valor != palabra]
    #             condiciones_partes[i] = random.choice(nuevas_valores)

    #     condiciones_mutadas = " ".join(condiciones_partes)

    #     # Mutar la acción
    #     acciones = ["comprar", "vender", "mantener"]
    #     accion_mutada = accion
    #     if accion in acciones:
    #         accion_mutada = random.choice([a for a in acciones if a != accion])

    #     # Reconstruir la regla asegurando la estructura correcta
    #     regla_mutada = f"SI {condiciones_mutadas} ENTONCES {accion_mutada}"
    #     return regla_mutada

    def crossover(self, parent1, parent2, crossover_rate=0.5):
        # Asegurarse de que ambos padres tengan el mismo tamaño
        min_len = min(len(parent1), len(parent2))
        parent1, parent2 = parent1[:min_len], parent2[:min_len]

        child1 = []
        child2 = []

        # Iterar sobre cada regla en los padres
        for i in range(len(parent1)):
            if random.random() < crossover_rate:
                # Tomar la regla del primer padre para el primer hijo y del segundo para el segundo hijo
                child1.append(parent1[i])
                child2.append(parent2[i])
            else:
                # Tomar la regla del segundo padre para el primer hijo y del primero para el segundo hijo
                child1.append(parent2[i])
                child2.append(parent1[i])

        return child1, child2

    # def validar_regla(self, regla):
    #     # Intenta analizar la regla para verificar su validez
    #     try:
    #         parsed_conditions, accion = self.parser.parse_rule(regla)
    #         return True
    #     except ValueError as e:
    #         # Imprimir mensaje de error si la regla no es válida
    #         print(f"Regla inválida: {regla}. Error: {e}")
    #         return False

    # Función de Supervivencia Sigmoide Basada en Edad
    def probabilidad_supervivencia(self, age, fitness, k=0.1, t=600):
        return fitness / (1 + np.exp(k * (age - t)))

    def algoritmo_genetico(self, contexto, agentes, creencias,inference_engine , interpreter,tasa_mutacion=0.5):
        nuevos_agentes = []

        # Evaluar desempeño de cada agente
        desempeno_agentes = [(agente, self.probabilidad_supervivencia(agente.ciclo, agente.evaluar_desempeno(contexto))) for agente in agentes]

        # Ordenar los agentes por desempeño (mayor desempeño primero)
        desempeno_agentes.sort(key=lambda x: x[1], reverse=True)

        # Caso especial: Solo hay dos agentes
        if len(agentes) <= 3:
            mejor_agente = desempeno_agentes[0][0]  # Agente con mejor desempeño
            peor_agente = desempeno_agentes[-1][0]  # Agente con peor desempeño

            # Realizar crossover y mutación entre los dos agentes
            nuevas_reglas_padre1, nuevas_reglas_padre2 = self.crossover(mejor_agente.reglas, peor_agente.reglas)

            # Aplicar mutación a las reglas con una probabilidad definida
            if random.random() < tasa_mutacion:
                nuevas_reglas_padre1 = self.mutar_regla(nuevas_reglas_padre1,creencias)
            if random.random() < tasa_mutacion:
                nuevas_reglas_padre2 = self.mutar_regla(nuevas_reglas_padre2,creencias)

            # Validar reglas y generar un nuevo agente para reemplazar al peor
            nuevo_agente = Agente(
                f'agente {peor_agente.nombre}',
                nuevas_reglas_padre2,
                inference_engine ,
                interpreter,
                capital_inicial=peor_agente.capital_inicial  # Mantener el capital inicial
            )
            nuevos_agentes.append(nuevo_agente)

            # Retornar el nuevo agente creado y el agente reemplazado
            return nuevos_agentes, [peor_agente]

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
                    nuevas_reglas_padre1 = self.mutar_regla(nuevas_reglas_padre1,creencias)
                if random.random() < tasa_mutacion:
                    nuevas_reglas_padre2 = self.mutar_regla(nuevas_reglas_padre2,creencias)
                
                # Validar reglas y crear nuevos agentes
                nuevo_agente1 = Agente(
                    f'agente {len(nuevos_agentes)}',
                    nuevas_reglas_padre1,
                    inference_engine ,
                    interpreter,
                    capital_inicial=padre1.capital_inicial  # Mantener el capital inicial
                )
                nuevos_agentes.append(nuevo_agente1)
                self.agent_performances[nuevo_agente1.nombre] = []  # Inicializa el desempeño

                nuevo_agente2 = Agente(
                    f'agente {len(nuevos_agentes)}',
                    nuevas_reglas_padre2,
                    inference_engine ,
                    interpreter,
                    capital_inicial=padre2.capital_inicial  # Mantener el capital inicial
                )
                nuevos_agentes.append(nuevo_agente2)
                self.agent_performances[nuevo_agente2.nombre] = []  # Inicializa el desempeño

            # Retornar los nuevos agentes creados y los agentes que fueron reemplazados
            return nuevos_agentes, [agente[0] for agente in peores]

    def _print_step_info(self, step):
        print(f"Paso {step}: Timestamp = {self.market.timestamp}")
        for crypto_name, crypto in self.market.cryptocurrencies.items():
            print(f"  {crypto_name}: Precio = ${crypto.price:.2f}")

    def _record_data(self):
        current_time = len(self.price_history_df)
        row_data = {'Time': current_time}
        for crypto_name, crypto in self.market.cryptocurrencies.items():
            # 'open' es el 'close' del paso anterior
            if current_time > 0:
                row_data[f'{crypto_name}_open'] = self.price_history[crypto_name][-1]
            else:
                row_data[f'{crypto_name}_open'] = crypto.price
            # 'high', 'low' y 'close' son el precio actual
            row_data[f'{crypto_name}_high'] = crypto.price  # Puedes ajustar esto basado en tu lógica de volatilidad
            row_data[f'{crypto_name}_low'] = crypto.price   # Puedes ajustar esto basado en tu lógica de volatilidad
            row_data[f'{crypto_name}_close'] = crypto.price
            row_data[f'{crypto_name}_volume'] = crypto.volume

            # Actualizar los historiales
            self.price_history[crypto_name].append(crypto.price)
            self.volume_history[crypto_name].append(crypto.volume)

        # Añadir la fila al DataFrame de precios
        self.price_history_df = self.price_history_df._append(row_data, ignore_index=True)

    def plot_results(self):
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 18))

        # Graficar precios
        for crypto in self.market.cryptocurrencies:
            ax1.plot(self.price_history[crypto], label=crypto)
        ax1.set_title('Precio de las criptomonedas')
        ax1.set_xlabel('Pasos de tiempo')
        ax1.set_ylabel('Precio')
        ax1.legend()

        # Graficar sentimiento del mercado
        for crypto in self.market.cryptocurrencies:
            ax2.plot(self.sentiment_history[crypto], label=crypto)
        ax2.set_title('Sentimiento del mercado')
        ax2.set_xlabel('Pasos de tiempo')
        ax2.set_ylabel('Sentimiento')
        ax2.legend()

        # Graficar rendimiento de los agentes
        for agent in self.agents:
            ax3.plot(self.agent_performances[agent.nombre], label=agent.nombre)
        ax3.set_title('Rendimiento de los agentes')
        ax3.set_xlabel('Pasos de tiempo')
        ax3.set_ylabel('Ganancia (USD)')
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
                performance = (final_value) / initial_value * 100
                summary['agent_performance'][agent.nombre] = {
                    'initial_value': initial_value,
                    'final_value': final_value + initial_value,
                    'performance': performance,
                    'max_performance': (max(agent.historia_ganancia)) / initial_value * 100,
                    'min_performance': (min(agent.historia_ganancia)) / initial_value * 100,
                    'avg_performance': (sum(agent.historia_ganancia) / len(agent.historia_ganancia)) / initial_value * 100,
                    'rules': agent.reglas,
                    'beliefs': agent.beliefs,
                    'intentions': agent.historial_intenciones,
                    'desires': agent.desires,
                    'capital': agent.capital,
                    'portfolio': agent.portafolio
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
                if key in ['performance', 'max_performance', 'min_performance', 'avg_performance']:
                    print(f"  {key}: {value:.2f}%")
                else:
                    print(f"  {key}: {value}")

        # Determinar la estrategia más efectiva
        best_agent = max(summary['agent_performance'], key=lambda x: summary['agent_performance'][x]['performance'])
        print(f"\nLa estrategia más efectiva fue: {best_agent}\n\n")

        mejor_agente_data = summary['agent_performance'][best_agent]
        # print(mejor_agente_data.get('beliefs'))
        # print(mejor_agente_data.get('intentions'))
        # print(mejor_agente_data.get('desires'))

        return best_agent
    class MotInit:

        def __init__():
            self.rules = """SI ERES NO novato Y experto ENTONCES SI novato ENTONCES COMPRAR capital , SI experto ENTONCES COMPRAR capital
                SI ERES novato Y experto ENTONCES ELIMINAR SI novato ENTONCES COMPRAR capital, SI novato ENTONCES COMPRAR capital; SI experto ENTONCES COMPRAR capital
                SI ERES NO novato Y experto ENTONCES ERES novato [0.5 <= X < 0.5] , avanzado [0.5 < X <= 0.5] , experto [0.5 < X < 0.5]
                SI ERES novato Y experto ENTONCES ERES ELIMINAR novato, avanzado; experto [0.5 <= X < 0.5]
                SI ERES novato ENTONCES ERES impulsivo,tendencia, terco
                SI ERES avanzado ENTONCES ERES tendencia , analista , noticias
                SI ERES avanzado ENTONCES ERES NO novato


                SI ERES MIEDOSO ENTONCES ERES NO AVARICIOSO # ver regla MEjor poner NO y en la parte Lógica Negar
                SI ERES AVARICIOSO ENTONCES ERES NO MIEDOSO # [1.0 == X]
                SI ERES MIEDOSO O TERCO Y AVARICIOSO ENTONCES ERES NO ALEGRE
                SI ERES MIEDOSO Y NERVIOSO ENTONCES SI historia_precio(20) mayor que 5 ENTONCES COMPRAR capital * 0.20 , SI historia_precio(20) ENTONCES VENDER todo
                SI ERES AVARICIOSO Y TERCO ENTONCES SI historia_precio(20) ENTONCES COMPRAR capital , SI precio mayor que 500 ENTONCES VENDER todo
                CUANDO random() menor que 0.20 ENTONCES TERCO
                CUANDO random() mayor que 0.50 ENTONCES NERVIOSO
                CUANDO capital mayor que 5000 ENTONCES AVARICIOSO
                CUANDO capital menor que 100  ENTONCES MIEDOSO
                CUANDO sentimiento es alto ENTONCES ALEGRE, TONTO
            """

        def Init():
            lex = RuleLexer()
            par = RuleParser()

            
            result = par.parse(lex.tokenize(self.rules))
            # for instruction in result:
            #     print(instruction)

            nodes = create_graph_from_parser(result)
            # for n in nodes:
            #     print(n)

            return FuzzyInferenceEngine(nodes)

