import numpy as np
from typing import List
import matplotlib.pyplot as plt
from agents import *

class Simulation:
    def __init__(self, num_steps: int,agent_gen:int, agents: List[Agent], market: Market,parser):
        self.num_steps = num_steps
        self.agent_gen = agent_gen
        self.agents = agents
        self.market = market
        self.price_history = {crypto: [] for crypto in market.cryptocurrencies}
        self.volume_history = {crypto: [] for crypto in market.cryptocurrencies}
        self.sentiment_history = {crypto: [] for crypto in market.cryptocurrencies}
        self.agent_performances = {agent.name: [] for agent in agents}
        self.parser = parser

    def run(self):
        generacion = 1
        No_Agente = 0
        count = 1

        subreddits_list = {}
        trainer = SentimentAnalyzer()
        reddit_instance = CryptoTradingAgent()
        post_limit = 100

        for crypto in market.cryptocurrencie:
                new_subreddits[crypto.name] = [ 'CryptoInvesting',crypto.name]
        #search_query = 'trading OR investment OR market OR price'
        for step in range(self.num_steps):
            # Simula el sentimiento del mercado
            for crypto in market.cryptocurrencie:
                self.sentiment_history[crypto].append(Process( trainer,reddit_instance,new_subreddits[crypto.name],post_limit,))

            # Los agentes toman decisiones y ejecutan operaciones
            for agent in self.agents:
                #decisions = agent.decide(self.market)
                decision = agent.tomar_decision(self.market)
                # agent.execute_trades(self.market, decisions)
                agent.ejecutar_accion(decision,self.market,decision[1])
                agent.update_performance(self.market)
                self.agent_performances[agent.name].append(agent.performance_history[-1])

            # Actualiza el estado del mercado
            self.market.update(market_sentiment)

            if count == 10:
                count = 1
                nuevos,peores=self.algoritmo_genetico(self.market,self.agents,count)
                # Registra datos para análisis posterior
                for agente in peores:
                    self.agents.remove(agent)
                for reglas in nuevo:
                    self.agents.append(agent(f'agente {No_Agente} generación {generacion}',reglas,parser))
                    No_Agente =  No_Agente +1
                generacion = generacion + 1
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

    # def crossmutation(self, regla1, regla2):
    #     # Realiza un crossover entre dos reglas, combinando partes de ambas
    #     partes1 = regla1.split(" ")
    #     partes2 = regla2.split(" ")
    #     punto_cruce = random.randint(1, len(partes1) - 2)
    #     nueva_regla = partes1[:punto_cruce] + partes2[punto_cruce:]
    #     return " ".join(nueva_regla)

    def crossover(parent1, parent2, crossover_rate=0.5):
        # Asegúrate de que ambos padres tengan el mismo tamaño
        if len(parent1) != len(parent2):
            raise ValueError("Los padres deben tener el mismo tamaño")
        
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
            parsed_conditions, accion = self.parser_reglas.parse_rule(regla)
            return True
        except ValueError as e:
            # Imprime un mensaje de error si la regla no es válida
            print(f"Regla inválida: {regla}. Error: {e}")
            return False

    def algoritmo_genetico(self, contexto,agentes, tasa_mutacion=0.1 ):
        # Ejecuta el algoritmo genético para evolucionar las reglas del agente
        
            nuevos_agentes = []
            ganancias = self.evaluar_desempeno(self.capital)
                
            # Selecciona las mejores reglas según el desempeño
            reglas_seleccionadas = sorted(self.reglas, key=lambda x: self.evaluar_desempeno(ganancias), reverse=True)[:len(self.reglas)//2]
                
            agentes_orden = [agente.evaluar_desempeno(contexto) for agente in agentes].sort(key=lambda x: x[1])
            corte = len(agentes_orden)//2
            mejores = agentes_orden[:corte]
            peores = agentes_orden[-corte:]
            # Realiza crossover y mutación en las reglas seleccionadas
            while len(nuevos_agentes) < ( agentes_orden-corte):
                padre1 = random.choice(mejores)
                padre2 = random.choice(mejores)
                if padre1[0] != padre2[0]:
                    nuevas_regla = self.crossover(padre1[1], padre2[1])

                    if random.random() < tasa_mutacion:
                        regla1 = self.mutar_regla(regla1)

                    if random.random() < tasa_mutacion:
                        regla2 = self.mutar_regla(regla2)
                        
                    # Valida la nueva regla antes de agregarla
                    if self.validar_regla(regla1):
                        nuevas_reglas.append(regla1)
                    else:
                        print(f"Regla generada no válida y descartada")

                    # Valida la nueva regla antes de agregarla
                    if self.validar_regla(regla2):
                        nuevos_agentes.append(regla2)
                    else:
                        print(f"Regla generada no válida y descartada")
            return  nuevos_agentes,peores
            #     # Reemplaza las reglas antiguas con las nuevas reglas generadas
            #     self.mejor_agentes = mejores 

            # # Imprime el mejor conjunto de reglas obtenido
            # print(f"Mejor conjunto de reglas para {self.nombre}: {self.mejor_reglas}")

    # def simular(self, contexto, ciclos=100):
    #     """Simula la operación del agente en el mercado durante un número dado de ciclos."""
    #     capital_inicial = self.capital
    #     ganancias = []
        
    #     for _ in range(ciclos):
    #         accion, _ = self.tomar_decision(contexto)
    #         cripto = random.choice(list(contexto.datos.keys()))  # Selecciona una criptomoneda aleatoria
    #         self.ejecutar_accion(accion, contexto, cripto)
    #         ganancias.append(self.capital - capital_inicial)
    #         actualizar_mercado(contexto)  # Supone que tienes una función para actualizar el mercado
            
    #     return ganancias

    def comparar_reglas(self, contexto, generaciones=10, ciclos=100):
        """Compara el desempeño del agente antes y después del algoritmo genético."""
        
        # Simular con las reglas originales
        print("Simulación con reglas originales...")
        rendimiento_original = self.simular(contexto, ciclos=ciclos)
        capital_final_original = self.capital
        
        # Aplicar algoritmo genético
        print("Aplicando algoritmo genético...")
        self.algoritmo_genetico(contexto, generaciones=generaciones)
        
        # Reiniciar capital del agente para una nueva simulación
        self.capital = capital_final_original
        self.portafolio = {}
        
        # Simular con las reglas modificadas
        print("Simulación con reglas modificadas...")
        rendimiento_modificado = self.simular(contexto, ciclos=ciclos)
        capital_final_modificado = self.capital
        
        # Comparar los resultados
        print(f"Capital final con reglas originales: {capital_final_original}")
        print(f"Capital final con reglas modificadas: {capital_final_modificado}")
        
        # Visualizar o analizar los resultados
        import matplotlib.pyplot as plt
        plt.plot(rendimiento_original, label="Original")
        plt.plot(rendimiento_modificado, label="Modificado")
        plt.xlabel("Ciclos")
        plt.ylabel("Ganancias Acumuladas")
        plt.legend()
        plt.show()

        # Retornar la comparación
        return capital_final_modificado > capital_final_original, rendimiento_original, rendimiento_modificado

    def _record_data(self):
        for crypto_name, crypto in self.market.cryptocurrencies.items():
            self.price_history[crypto_name].append(crypto.price)
            self.volume_history[crypto_name].append(crypto.volume)

    def _print_step_info(self, step):
        print(f"Step {step}: Timestamp = {self.market.timestamp}")
        for crypto_name, crypto in self.market.cryptocurrencies.items():
            print(f"  {crypto_name}: Price = ${crypto.price:.2f}, Volume = {crypto.volume:.2f}")

    def plot_results(self):
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 18))

        # Graficar precios
        for crypto, prices in self.price_history.items():
            ax1.plot(prices, label=crypto)
        ax1.set_title('Precio de las criptomonedas')
        ax1.set_xlabel('Pasos de tiempo')
        ax1.set_ylabel('Precio')
        ax1.legend()

        # Graficar volúmenes
        for crypto, volumes in self.volume_history.items():
            ax2.plot(volumes, label=crypto)
        ax2.set_title('Volumen de transacciones')
        ax2.set_xlabel('Pasos de tiempo')
        ax2.set_ylabel('Volumen')
        ax2.legend()

        # Graficar sentimiento del mercado
        ax3.plot(self.sentiment_history)
        ax3.set_title('Sentimiento del mercado')
        ax3.set_xlabel('Pasos de tiempo')
        ax3.set_ylabel('Sentimiento')

        ax4 = fig.add_subplot(414)
        for agent_name, performances in self.agent_performances.items():
            ax4.plot(performances, label=agent_name)
        ax4.set_title('Rendimiento de los agentes')
        ax4.set_xlabel('Pasos de tiempo')
        ax4.set_ylabel('Rendimiento (%)')
        ax4.legend()

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
            final_value = agent.calculate_total_value(self.market)
            initial_value = sum(agent.initial_balance.values())
            performance = (final_value - initial_value) / initial_value * 100
            summary['agent_performance'][agent.name] = {
                'initial_value': initial_value,
                'final_value': final_value,
                'performance': performance,
                'max_performance': max(agent.performance_history) * 100,
                'min_performance': min(agent.performance_history) * 100,
                'avg_performance': sum(agent.performance_history) / len(agent.performance_history) * 100
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
                print(f"  {key}: {value:.2%}")

        # Determinar la estrategia más efectiva
        best_agent = max(summary['agent_performance'], key=lambda x: summary['agent_performance'][x]['performance'])
        print(f"\nLa estrategia más efectiva fue: {best_agent}\n\n")

        return best_agent