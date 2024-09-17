import numpy as np
from typing import List
import matplotlib.pyplot as plt
from agents import *
#from gemini_ai import *


class Simulation:
    def __init__(self, num_steps: int, agents: List[Agente], market: Market,parser):
        self.num_steps = num_steps
        self.agents = agents
        self.market = market
        self.price_history = {crypto: [market.cryptocurrencies[crypto].price] for crypto in market.cryptocurrencies}
        #self.volume_history = {crypto: [] for crypto in market.cryptocurrencies}
        self.sentiment_history = {crypto: [] for crypto in market.cryptocurrencies}
        self.agent_performances = {agent.nombre: [] for agent in agents}
        self.parser = parser
    
    def run(self):
        agent_gen = 1
        No_Agente = 0
        count = 1

        subreddits_list = {}
        # trainer = SentimentAnalyzer('gem.env')
        # reddit_instance = CryptoTradingAgent('gem.env')
        post_limit = 100

        for crypto in self.market.cryptocurrencies:
            subreddits_list[crypto]=['CryptoCurrency', 'CryptoTrading', 'CryptoInvesting',crypto]
        #search_query = 'trading OR investment OR market OR price'
        for step in range(self.num_steps):
            # Simula el sentimiento del mercado
            for crypto in self.market.cryptocurrencies:
                # self.sentiment_history[crypto].append(Process( trainer,reddit_instance,subreddits_list[crypto],post_limit,crypto))
                self.sentiment_history[crypto].append(np.random.normal(0, 0.1))#quitar
            # Los agentes toman decisiones y ejecutan operaciones
            for agent in self.agents:
               
                #decision = agent.tomar_decision(self.market)
                decision = np.random.choice(["comprar","vender","mantener" ])#quitar
                                         
                agent.ejecutar_accion(decision,self.market,"Bitcoin")#cambiar
                agent.actualizar_ganancia(self.market)
                self.agent_performances[agent.name].append(agent.historia_ganancia[-1])

            # Actualiza el estado del mercado
            self.market.update(self.sentiment_history)

            if count == 10:
                count = 1
                nuevos,peores=self.algoritmo_genetico(self.market,self.agents,count)
                # Registra datos para análisis posterior
                print("**** Nuevos agentes y reglas *****")
                for agente in nuevos:
                    print(agente.nombre)
                    print(agente.reglas)

                for agente in peores:
                    self.agents.remove(agente)
                for agente in nuevos:
                    self.agents.append(Agente(f'agente {No_Agente} generación { agent_gen}',agente.reglas,self.parser))
                    No_Agente =  No_Agente +1
                agent_gen =  agent_gen + 1
                No_Agente = 0

            else: 
                count = count+1    
            # Imprime información del paso actual
            self._print_step_info(step)

    def mutar_regla(self, regla):
        # Divide la regla en partes usando espacios como delimitadores
        partes = regla.split(" ")
        
        # Listas de posibles valores para la mutación
        valores_precio_volumen = ["alto", "bajo", "medio"]
        valores_sentimiento = ["negativo", "neutro", "positivo"]
        
        # Identifica todas las posiciones donde se encuentran valores de precio/volumen
        indices_precio_volumen = [i for i, palabra in enumerate(partes) if palabra in valores_precio_volumen]

        # Mutar cada valor de precio/volumen encontrado en la regla
        for index in indices_precio_volumen:
            valor_actual = partes[index]
            nuevos_valores = [valor for valor in valores_precio_volumen if valor != valor_actual]
            partes[index] = random.choice(nuevos_valores)  # Sustituir por un nuevo valor

        # Identifica todas las posiciones donde se encuentran valores de sentimiento
        indices_sentimiento = [i for i, palabra in enumerate(partes) if palabra in valores_sentimiento]

        # Mutar cada valor de sentimiento encontrado en la regla
        for index in indices_sentimiento:
            valor_actual = partes[index]
            nuevos_valores = [valor for valor in valores_sentimiento if valor != valor_actual]
            partes[index] = random.choice(nuevos_valores)  # Sustituir por un nuevo valor

        # Si no se encontraron valores de precio/volumen ni de sentimiento, mutar la acción
        partes[-1] = random.choice(["comprar", "vender", "mantener"])

        return " ".join(partes)

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

        
    def algoritmo_genetico(self, contexto, agentes, tasa_mutacion=0.1):

        nuevos_agentes = []

        # Evaluar desempeño de cada agente
        desempeno_agentes = [(agente, agente.evaluar_desempeno(contexto)) for agente in agentes]
        
        # Ordenar los agentes por desempeño
        desempeno_agentes.sort(key=lambda x: x[1], reverse=True)
        # Caso especial: Solo hay dos agentes
        if len(agentes) <= 3:
            mejor_agente = desempeno_agentes[0]  # Agente con mejor desempeño
            peor_agente = desempeno_agentes[1]   # Agente con peor desempeño

            # Realizar crossover y mutación entre los dos agentes
            #print(len(mejor_agente[0].reglas))
            nuevas_reglas_padre1, nuevas_reglas_padre2 = self.crossover(mejor_agente[0].reglas, peor_agente[0].reglas)


            # Aplicar mutación a las reglas con una probabilidad definida
            if random.random() < tasa_mutacion:
                nuevas_reglas_padre1 = [self.mutar_regla(regla) for regla in nuevas_reglas_padre1]
            if random.random() < tasa_mutacion:
                nuevas_reglas_padre2 = [self.mutar_regla(regla) for regla in nuevas_reglas_padre2]

            # Validar reglas y generar un nuevo agente para reemplazar al peor
            if self.validar_regla(" ".join(nuevas_reglas_padre2)):
                nuevo_agente = Agente(f'Nuevo Agente {peor_agente[0].nombre}', nuevas_reglas_padre2, self.parser)
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
                padre1, padre2 = random.sample(mejores, 2)
                # Realizar crossover (cruce) entre las reglas de los padres
                nuevas_reglas_padre1, nuevas_reglas_padre2 = self.crossover(padre1[0].reglas, padre2[0].reglas)

                # Mutar reglas con probabilidad de tasa_mutacion
                if random.random() < tasa_mutacion:
                    nuevas_reglas_padre1 = [self.mutar_regla(regla) for regla in nuevas_reglas_padre1]
                if random.random() < tasa_mutacion:
                    nuevas_reglas_padre2 = [self.mutar_regla(regla) for regla in nuevas_reglas_padre2]

                # Validar reglas y crear nuevos agentes
                if self.validar_regla(" ".join(nuevas_reglas_padre1)):
                    nuevos_agentes.append(Agente(f'Agente {len(nuevos_agentes)}', nuevas_reglas_padre1, self.parser))
                if self.validar_regla(" ".join(nuevas_reglas_padre2)):
                    nuevos_agentes.append(Agente(f'Agente {len(nuevos_agentes)}', nuevas_reglas_padre2, self.parser))

            # Retornar los nuevos agentes creados y los agentes que fueron reemplazados
            return nuevos_agentes, [agente[0] for agente in peores]



    # def _record_data(self):
    #     for crypto_name, crypto in self.market.cryptocurrencies.items():
    #         self.price_history[crypto_name].append(crypto.price)
    #         self.volume_history[crypto_name].append(crypto.volume)

    # def _print_step_info(self, step):
    #     print(f"Step {step}: Timestamp = {self.market.timestamp}")
    #     for crypto_name, crypto in self.market.cryptocurrencies.items():
    #         #print(f"  {crypto_name}: Price = ${crypto.price:.2f}, Volume = {crypto.volume:.2f}")
    #         print(f"  {crypto_name}: Price = ${crypto.price:.2f}")


    # def plot_results(self):
    #     fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 18))

    #     # Graficar precios
    #     for crypto, prices in self.price_history.items():
    #         ax1.plot(prices, label=crypto)
    #     ax1.set_title('Precio de las criptomonedas')
    #     ax1.set_xlabel('Pasos de tiempo')
    #     ax1.set_ylabel('Precio')
    #     ax1.legend()

    #     # # Graficar volúmenes
    #     # for crypto, volumes in self.volume_history.items():
    #     #     ax2.plot(volumes, label=crypto)
    #     # ax2.set_title('Volumen de transacciones')
    #     # ax2.set_xlabel('Pasos de tiempo')
    #     # ax2.set_ylabel('Volumen')
    #     # ax2.legend()

    #     # # Graficar sentimiento del mercado
    #     # ax3.plot(self.sentiment_history)
    #     # ax3.set_title('Sentimiento del mercado')
    #     # ax3.set_xlabel('Pasos de tiempo')
    #     # ax3.set_ylabel('Sentimiento')

    #     # Graficar sentimiento del mercado
    #     for crypto, sentiment in self.sentiment_history.items():
    #         ax3.plot(sentiment, label=crypto)  # Graficar cada criptomoneda
    #     ax3.set_title('Sentimiento del mercado')
    #     ax3.set_xlabel('Pasos de tiempo')
    #     ax3.set_ylabel('Sentimiento')
    #     ax3.legend()  # Añadir leyenda para identificar cada criptomoneda

    #     ax4 = fig.add_subplot(414)
    #     for agent_name, performances in self.agent_performances.items():
    #         ax4.plot(performances, label=agent_name)
    #     ax4.set_title('Rendimiento de los agentes')
    #     ax4.set_xlabel('Pasos de tiempo')
    #     ax4.set_ylabel('Rendimiento (%)')
    #     ax4.legend()

    #     plt.tight_layout()
    #     plt.show()

    # def get_summary(self):
    #     summary = {}
    #     for crypto_name, prices in self.price_history.items():
    #         summary[crypto_name] = {
    #             'initial_price': prices[0],
    #             'final_price': prices[-1],
    #             'price_change': (prices[-1] - prices[0]) / prices[0] * 100,
    #             'max_price': max(prices),
    #             'min_price': min(prices),
    #             'total_volume': sum(self.volume_history[crypto_name])
    #         }

    #     # Añadir resumen del rendimiento de los agentes
    #     summary['agent_performance'] = {}
    #     for agent in self.agents:
    #         final_value = agent.calculate_total_value(self.market)
    #         initial_value = sum(agent.initial_balance.values())
    #         performance = (final_value - initial_value) / initial_value * 100
    #         summary['agent_performance'][agent.name] = {
    #             'initial_value': initial_value,
    #             'final_value': final_value,
    #             'performance': performance,
    #             'max_performance': max(agent.performance_history) * 100,
    #             'min_performance': min(agent.performance_history) * 100,
    #             'avg_performance': sum(agent.performance_history) / len(agent.performance_history) * 100
    #         }

    #     return summary

    # def get_performance(self):

    #     summary = self.get_summary()

    #     print("Resumen de la simulación:")
    #     for crypto, data in summary.items():
    #         if crypto != 'agent_performance':
    #             print(f"{crypto}:")
    #             for key, value in data.items():
    #                 print(f"  {key}: {value}")

    #     print("\nRendimiento de los agentes:")
    #     for agent_name, performance in summary['agent_performance'].items():
    #         print(f"{agent_name}:")
    #         for key, value in performance.items():
    #             print(f"  {key}: {value:.2%}")

    #     # Determinar la estrategia más efectiva
    #     best_agent = max(summary['agent_performance'], key=lambda x: summary['agent_performance'][x]['performance'])
    #     print(f"\nLa estrategia más efectiva fue: {best_agent}\n\n")

    #     return best_agent