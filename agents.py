from abc import ABC
from rules_interpreter import *
from typing import List, Dict
from market import *

# class Agent(ABC):
#     def __init__(self, name: str, initial_balance: Dict[str, float], intelligence):
#         self.name = name
#         self.initial_balance = initial_balance.copy()
#         self.balance = initial_balance.copy()
#         self.intelligence = intelligence
#         self.portfolio = {crypto: 0 for crypto in initial_balance.keys() if crypto != "USD"}
#         self.performance_history = []

#     def calculate_total_value(self, market: Market):
#         total_value = self.balance["USD"]
#         for crypto, amount in self.portfolio.items():
#             total_value += amount * market.cryptocurrencies[crypto].price
#         return total_value

#     def update_performance(self, market: Market):
#         current_value = self.calculate_total_value(market)
#         initial_value = sum(self.initial_balance.values())
#         performance = (current_value - initial_value) / initial_value
#         self.performance_history.append(performance)

#     def decide(self, market: Market) -> Dict[str, List[tuple]]:
#         # Toma decisiones de trading basadas en la inteligencia del agente
#         return self.intelligence.make_decision(market, self.balance, self.portfolio)

#     def execute_trades(self, market: Market, decisions: Dict[str, List[tuple]]):
#         # Ejecuta las decisiones de trading en el mercado
#         for crypto_name, orders in decisions.items():
#             crypto = market.cryptocurrencies[crypto_name]
#             for order_type, amount, price in orders:
#                 if order_type == "buy":
#                     cost = amount * price
#                     if self.balance["USD"] >= cost:
#                         self.balance["USD"] -= cost
#                         self.portfolio[crypto_name] += amount
#                         crypto.add_order("buy", price, amount)
#                 elif order_type == "sell":
#                     if self.portfolio[crypto_name] >= amount:
#                         self.portfolio[crypto_name] -= amount
#                         self.balance["USD"] += amount * price
#                         crypto.add_order("sell", price, amount)


# Definición de la clase Agente
class Agente:
    def __init__(self, nombre, reglas, parser_reglas , capital_inicial = 1000):#*****bien
        # Inicializa el agente con un nombre, capital inicial, conjunto de reglas, parser de reglas y portafolio vacío
        self.nombre = nombre
        self.capital_inicial = capital_inicial
        self.capital = self.capital_inicial
        self.reglas = reglas
        self.parser_reglas = parser_reglas
        self.mejor_reglas = []  # Almacena las mejores reglas seleccionadas
        self.portafolio = {}  # Portafolio para almacenar las criptomonedas compradas
    
    def tomar_decision(self, contexto):#ver
        # Inicializa variables para rastrear la mejor acción y el mejor resultado
        mejor_resultado = 0
        mejor_accion = "mantener"
        
        # Itera sobre cada regla para evaluarla en el contexto actual
        for regla in self.reglas:
            # Analiza la regla y la aplica al contexto de mercado
            parsed_conditions, accion = self.parser_reglas.parse_rule(regla)
            resultado = self.parser_reglas.aplicar_regla(parsed_conditions, accion, contexto)
            
            # Actualiza la mejor acción si el resultado de esta regla es superior
            if abs(resultado[0]) > abs(mejor_resultado[0]):
                mejor_resultado = resultado
                mejor_accion = accion
        
        # Interpreta el resultado y muestra la decisión tomada
        interpretacion = self.interpretar_resultado(mejor_resultado, mejor_accion)
        print(f"{self.nombre} decidió: {interpretacion}")
        
        # Retorna la mejor acción y el resultado asociado
        return mejor_accion, mejor_resultado
    
    def interpretar_resultado(self, resultado, accion):
        # Convierte la acción numérica en una cadena descriptiva
        if accion == 1:
            accion_str = "comprar"
        elif accion == -1:
            accion_str = "vender"
        else:
            accion_str = "mantener"
        
        # Interpreta el resultado de la acción basada en la confianza (valor de resultado)
        if resultado[0] == 0:
            return f"La regla sugiere no {accion_str} en este contexto."
        elif resultado[0] > 0:
            if resultado[0] >= 0.8:
                return f"Fuerte recomendación para {accion_str} {resultado[1]} con confianza de {resultado[0]:.2f}."
            elif resultado[0] >= 0.5:
                return f"Moderada recomendación para {accion_str} {resultado[1]} con confianza de {resultado[0]:.2f}."
            else:
                return f"Débil recomendación para {accion_str} {resultado[1]} con confianza de {resultado[0]:.2f}."
        elif resultado[0] < 0:
            if resultado[0] <= -0.8:
                return f"Fuerte recomendación para no {accion_str} {resultado[1]} con confianza de {resultado[0]:.2f}."
            elif resultado[0] <= -0.5:
                return f"Moderada recomendación para no {accion_str} {resultado[1]} con confianza de {resultado[0]:.2f}."
            else:
                return f"Débil recomendación para no {accion_str} {resultado[1]} con confianza de {resultado[0]:.2f}."
    
    def ejecutar_accion(self, accion, contexto, cripto):
        # Obtiene el precio actual de la criptomoneda del contexto de mercado
        precio = contexto.obtener_dato(cripto, "precio")
        
        if accion == "comprar" and self.capital > precio:
            # Calcula cuántas unidades se pueden comprar y actualiza el capital y portafolio del agente
            cantidad = self.capital // precio
            self.capital -= cantidad * precio
            if cripto in self.portafolio:
                self.portafolio[cripto] += cantidad
            else:
                self.portafolio[cripto] = cantidad
            print(f"{self.nombre} compró {cantidad} unidades de {cripto}.")
            
            contexto.cryptocurrencies[cripto].add_order("buy",precio,cantidad)

        elif accion == "vender":
            # Verifica si el agente tiene unidades para vender
            if cripto in self.portafolio and self.portafolio[cripto] > 0:
                cantidad = self.portafolio[cripto]
                self.capital += cantidad * precio
                self.portafolio[cripto] = 0  # Vender todas las unidades
                print(f"{self.nombre} vendió {cantidad} unidades de {cripto}.")
                
                # Actualizar el precio en el contexto: la venta disminuye el precio ligeramente
                nuevo_precio = precio * (1 - cantidad / 100000)  # Simplificación: pequeña caída de precio

                contexto.cryptocurrencies[cripto].add_order("sell",precio,cantidad)
            else:
                print(f"{self.nombre} no tiene unidades de {cripto} para vender.")

    def evaluar_desempeno(self,contexto):
        # Evalúa el desempeño del agente basado en las ganancias obtenidas
        ganancia = 0
        for crypto,value in self.portafolio:
            ganancia =  ganancia + (contexto.Cryptocurrency[crypto].price * value)
        ganancia = ganancia + capital

        return (self.nombre,ganancia/self.capital_inicial)

    #     def update_performance(self, market: Market):
    #         current_value = self.calculate_total_value(market)
    #         initial_value = sum(self.initial_balance.values())
    #         performance = (current_value - initial_value) / initial_value
    #         self.performance_history.append(performance)

    # def mutar_regla(self, regla):
    #     # Divide la regla en partes usando espacios como delimitadores
    #     partes = regla.split(" ")
        
    #     # Listas de posibles valores para la mutación
    #     valores_precio_volumen = ["alto", "bajo", "medio"]
    #     valores_sentimiento = ["negativo", "neutro", "positivo"]
        
    #     # Identifica todas las posiciones donde se encuentran valores de precio/volumen
    #     indices_precio_volumen = [i for i, palabra in enumerate(partes) if palabra in valores_precio_volumen]

    #     # Mutar cada valor de precio/volumen encontrado en la regla
    #     for index in indices_precio_volumen:
    #         valor_actual = partes[index]
    #         nuevos_valores = [valor for valor in valores_precio_volumen if valor != valor_actual]
    #         partes[index] = random.choice(nuevos_valores)  # Sustituir por un nuevo valor

    #     # Identifica todas las posiciones donde se encuentran valores de sentimiento
    #     indices_sentimiento = [i for i, palabra in enumerate(partes) if palabra in valores_sentimiento]

    #     # Mutar cada valor de sentimiento encontrado en la regla
    #     for index in indices_sentimiento:
    #         valor_actual = partes[index]
    #         nuevos_valores = [valor for valor in valores_sentimiento if valor != valor_actual]
    #         partes[index] = random.choice(nuevos_valores)  # Sustituir por un nuevo valor

    #     # Si no se encontraron valores de precio/volumen ni de sentimiento, mutar la acción
    #     partes[-1] = random.choice(["comprar", "vender", "mantener"])

    #     return " ".join(partes)

    # # def crossmutation(self, regla1, regla2):
    # #     # Realiza un crossover entre dos reglas, combinando partes de ambas
    # #     partes1 = regla1.split(" ")
    # #     partes2 = regla2.split(" ")
    # #     punto_cruce = random.randint(1, len(partes1) - 2)
    # #     nueva_regla = partes1[:punto_cruce] + partes2[punto_cruce:]
    # #     return " ".join(nueva_regla)

    # def crossover(parent1, parent2, crossover_rate=0.5):
    #     # Asegúrate de que ambos padres tengan el mismo tamaño
    #     if len(parent1) != len(parent2):
    #         raise ValueError("Los padres deben tener el mismo tamaño")
        
    #     child1 = []
    #     child2 = []
        
    #     # Iterar sobre cada gen/law en los padres
    #     for i in range(len(parent1)):
    #         if random.random() < crossover_rate:
    #             # Tomar el gen/law del primer padre para el primer hijo, y del segundo para el segundo hijo
    #             child1.append(parent1[i])
    #             child2.append(parent2[i])
    #         else:
    #             # Tomar el gen/law del segundo padre para el primer hijo, y del primero para el segundo hijo
    #             child1.append(parent2[i])
    #             child2.append(parent1[i])
        
    #     return child1, child2


    # def validar_regla(self, regla):
    #     # Intenta analizar la regla para verificar su validez
    #     try:
    #         parsed_conditions, accion = self.parser_reglas.parse_rule(regla)
    #         return True
    #     except ValueError as e:
    #         # Imprime un mensaje de error si la regla no es válida
    #         print(f"Regla inválida: {regla}. Error: {e}")
    #         return False

    # def algoritmo_genetico(self, contexto,agentes,count, tasa_mutacion=0.1 ):
    #     # Ejecuta el algoritmo genético para evolucionar las reglas del agente
        
    #         if count < 10:
    #            count = count+1
    #         else:
    #             nuevos_agentes = []
    #             ganancias = self.evaluar_desempeno(self.capital)
                
    #             # Selecciona las mejores reglas según el desempeño
    #             reglas_seleccionadas = sorted(self.reglas, key=lambda x: self.evaluar_desempeno(ganancias), reverse=True)[:len(self.reglas)//2]
                
    #             agentes_orden = [agente.evaluar_desempeno(contexto) for agente in agentes].sort(key=lambda x: x[1])#ver si esta bien
    #             corte = len(agentes_orden)//2
    #             mejores = agentes_orden[:corte]
    #             # Realiza crossover y mutación en las reglas seleccionadas
    #             while len(nuevos_agentes) < ( agentes_orden-corte):
    #                 padre1 = random.choice(mejores)
    #                 padre2 = random.choice(mejores)
    #                 if padre1[0] != padre2[0]:
    #                     nuevas_regla = self.crossover(padre1[1], padre2[1])

    #                     if random.random() < tasa_mutacion:
    #                        regla1 = self.mutar_regla(regla1)

    #                     if random.random() < tasa_mutacion:
    #                        regla2 = self.mutar_regla(regla2)
                        
    #                     # Valida la nueva regla antes de agregarla
    #                     if self.validar_regla(regla1):
    #                         nuevas_reglas.append(regla1)
    #                     else:
    #                         print(f"Regla generada no válida y descartada")

    #                     # Valida la nueva regla antes de agregarla
    #                     if self.validar_regla(regla2):
    #                         nuevos_agentes.append(regla2)
    #                     else:
    #                         print(f"Regla generada no válida y descartada")
    #             return  nuevos_agentes 
    #         #     # Reemplaza las reglas antiguas con las nuevas reglas generadas
    #         #     self.mejor_agentes = mejores 

    #         # # Imprime el mejor conjunto de reglas obtenido
    #         # print(f"Mejor conjunto de reglas para {self.nombre}: {self.mejor_reglas}")

    # # def simular(self, contexto, ciclos=100):
    # #     """Simula la operación del agente en el mercado durante un número dado de ciclos."""
    # #     capital_inicial = self.capital
    # #     ganancias = []
        
    # #     for _ in range(ciclos):
    # #         accion, _ = self.tomar_decision(contexto)
    # #         cripto = random.choice(list(contexto.datos.keys()))  # Selecciona una criptomoneda aleatoria
    # #         self.ejecutar_accion(accion, contexto, cripto)
    # #         ganancias.append(self.capital - capital_inicial)
    # #         actualizar_mercado(contexto)  # Supone que tienes una función para actualizar el mercado
            
    # #     return ganancias

    # def comparar_reglas(self, contexto, generaciones=10, ciclos=100):
    #     """Compara el desempeño del agente antes y después del algoritmo genético."""
        
    #     # Simular con las reglas originales
    #     print("Simulación con reglas originales...")
    #     rendimiento_original = self.simular(contexto, ciclos=ciclos)
    #     capital_final_original = self.capital
        
    #     # Aplicar algoritmo genético
    #     print("Aplicando algoritmo genético...")
    #     self.algoritmo_genetico(contexto, generaciones=generaciones)
        
    #     # Reiniciar capital del agente para una nueva simulación
    #     self.capital = capital_final_original
    #     self.portafolio = {}
        
    #     # Simular con las reglas modificadas
    #     print("Simulación con reglas modificadas...")
    #     rendimiento_modificado = self.simular(contexto, ciclos=ciclos)
    #     capital_final_modificado = self.capital
        
    #     # Comparar los resultados
    #     print(f"Capital final con reglas originales: {capital_final_original}")
    #     print(f"Capital final con reglas modificadas: {capital_final_modificado}")
        
    #     # Visualizar o analizar los resultados
    #     import matplotlib.pyplot as plt
    #     plt.plot(rendimiento_original, label="Original")
    #     plt.plot(rendimiento_modificado, label="Modificado")
    #     plt.xlabel("Ciclos")
    #     plt.ylabel("Ganancias Acumuladas")
    #     plt.legend()
    #     plt.show()

    #     # Retornar la comparación
    #     return capital_final_modificado > capital_final_original, rendimiento_original, rendimiento_modificado