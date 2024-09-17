import re
# Funciones de pertenencia con parámetros personalizados

# Función para calcular la pertenencia al conjunto "precio bajo"
def pertenencia_precio_bajo(precio, limite_inferior, limite_superior):
    if precio < limite_inferior:
        return 1  # Pertenece completamente al conjunto "bajo" si está por debajo del límite inferior
    elif limite_inferior <= precio <= limite_superior:
        # Pertenece parcialmente al conjunto "bajo" si está entre el límite inferior y superior
        return (limite_superior - precio) / (limite_superior - limite_inferior)
    else:
        return 0  # No pertenece al conjunto "bajo" si está por encima del límite superior

# Función para calcular la pertenencia al conjunto "precio medio"
def pertenencia_precio_medio(precio, limite_inferior, limite_superior):
    if limite_inferior <= precio <= limite_superior:
        # Pertenece parcialmente al conjunto "medio" si está dentro de los límites
        return (precio - limite_inferior) / (limite_superior - limite_inferior)
    else:
        return 0  # No pertenece al conjunto "medio" si está fuera de los límites

# Función para calcular la pertenencia al conjunto "precio alto"
def pertenencia_precio_alto(precio, limite_inferior, limite_superior):
    if precio > limite_superior:
        return 1  # Pertenece completamente al conjunto "alto" si está por encima del límite superior
    elif limite_inferior <= precio <= limite_superior:
        # Pertenece parcialmente al conjunto "alto" si está entre el límite inferior y superior
        return (precio - limite_inferior) / (limite_superior - limite_inferior)
    else:
        return 0  # No pertenece al conjunto "alto" si está por debajo del límite inferior

# Función para calcular la pertenencia al conjunto "volumen bajo"
def pertenencia_volumen_bajo(volumen, limite_inferior, limite_superior):
    if volumen < limite_inferior:
        return 1  # Pertenece completamente al conjunto "bajo" si está por debajo del límite inferior
    elif limite_inferior <= volumen <= limite_superior:
        # Pertenece parcialmente al conjunto "bajo" si está entre el límite inferior y superior
        return (limite_superior - volumen) / (limite_superior - limite_inferior)
    else:
        return 0  # No pertenece al conjunto "bajo" si está por encima del límite superior

# Función para calcular la pertenencia al conjunto "volumen medio"
def pertenencia_volumen_medio(volumen, limite_inferior, limite_superior):
    if limite_inferior <= volumen <= limite_superior:
        # Pertenece parcialmente al conjunto "medio" si está dentro de los límites
        return (volumen - limite_inferior) / (limite_superior - limite_inferior)
    else:
        return 0  # No pertenece al conjunto "medio" si está fuera de los límites

# Función para calcular la pertenencia al conjunto "volumen alto"
def pertenencia_volumen_alto(volumen, limite_inferior, limite_superior):
    if volumen > limite_superior:
        return 1  # Pertenece completamente al conjunto "alto" si está por encima del límite superior
    elif limite_inferior <= volumen <= limite_superior:
        # Pertenece parcialmente al conjunto "alto" si está entre el límite inferior y superior
        return (volumen - limite_inferior) / (limite_superior - limite_inferior)
    else:
        return 0  # No pertenece al conjunto "alto" si está por debajo del límite inferior

# Función para calcular la pertenencia al conjunto "sentimiento negativo"
def pertenencia_sentimiento_negativo(sentimiento):
    return max(0, (0 - sentimiento) / 1)  # Pertenece más al conjunto "negativo" cuanto más cerca de -1 esté

# Función para calcular la pertenencia al conjunto "sentimiento neutro"
def pertenencia_sentimiento_neutro(sentimiento):
    if -0.5 <= sentimiento <= 0.5:
        return 1 - abs(sentimiento)  # Pertenece al conjunto "neutro" si está cerca de 0
    else:
        return 0  # No pertenece al conjunto "neutro" si está fuera del rango de -0.5 a 0.5

# Función para calcular la pertenencia al conjunto "sentimiento positivo"
def pertenencia_sentimiento_positivo(sentimiento):
    return max(0, (sentimiento - 0) / 1)  # Pertenece más al conjunto "positivo" cuanto más cerca de 1 esté


# Definición de la clase ParserReglas
class ParserReglas:
    def __init__(self, pertenencia_map):
        # Inicializa el parser con un mapa de funciones de pertenencia para cada variable y criptomoneda
        self.pertenencia_map = pertenencia_map

    def parse_rule(self, rule):
        # Define el patrón para dividir la regla en condiciones y acción
        pattern = r"SI (.+) ENTONCES (.+)"
        match = re.match(pattern, rule)
        if not match:
            raise ValueError("Formato de regla no válido")  # Lanza un error si la regla no tiene el formato correcto

        # Extrae las condiciones y la acción de la regla
        conditions_str = match.group(1)
        action_str = match.group(2).strip()

        # Analiza las condiciones y la acción por separado
        parsed_conditions = self.parse_conditions(conditions_str)
        action = self.parse_action(action_str)

        return parsed_conditions, action

    def parse_conditions(self, conditions_str):
        # Reemplaza "NO", "Y", "O" para manejarlos como operadores lógicos
        conditions_str = conditions_str.replace(" NO ", " NOT ").replace(" Y ", " AND ").replace(" O ", " OR ")

        if "SI NO" in conditions_str:
            conditions_str = conditions_str.replace("SI NO", "IF NOT")  # Maneja la negación "SI NO"

        # Divide las condiciones por "OR" y luego por "AND" para analizarlas
        or_conditions = re.split(r'\sOR\s', conditions_str)
        parsed_conditions = []

        for or_cond in or_conditions:
            # Divide las condiciones por "AND" dentro de cada condición "OR"
            and_conditions = re.split(r'\sAND\s', or_cond)
            and_parsed = []

            for condition in and_conditions:
                if "NOT" in condition:
                    # Si la condición incluye "NOT", marca la condición como negada
                    condition = condition.replace("NOT", "").strip()  # Elimina "NOT" para su análisis
                    negated = True
                else:
                    negated = False

                # Analiza cada condición individualmente
                parsed_condition = self.parse_single_condition(condition)
                if negated:
                    parsed_condition = ("NOT", parsed_condition)  # Marca la condición como negada

                and_parsed.append(parsed_condition)

            parsed_conditions.append(and_parsed)

        return parsed_conditions

    def parse_single_condition(self, condition):
        # Expresión regular para analizar condiciones del tipo "variable de criptomoneda es valor"
        pattern = r"(\w+)\s(es|es mayor que|es menor que|es aproximadamente igual a|está entre)\s(.+)"
        match = re.match(pattern, condition)
        if not match:
            raise ValueError(f"Condición no válida: {condition}")  # Lanza un error si la condición no tiene el formato correcto

        # Extrae las partes de la condición: variable, operador, valor
        var, operator, val = match.groups()
        var, operator, val = var.strip(), operator.strip(), val.strip()

        if operator == "es":
            # Verifica si la condición es válida según el mapa de pertenencia
            return (var, val)
        else:
            # Devuelve la condición analizada con el operador y el valor correspondiente
            return (var, operator, val)

    def parse_action(self, action_str):
        # Asigna una acción numérica según la cadena de acción
        if action_str == "comprar":
            return 1
        elif action_str == "vender":
            return -1
        elif action_str == "mantener":
            return 0
        else:
            raise ValueError(f"Acción no válida: {action_str}")  # Lanza un error si la acción no es reconocida

    def aplicar_regla(self, parsed_conditions, action, contexto):
        resultados = {}
        for cripto, datos in contexto.cryptocurrencies.items():
            or_results = []
            for and_conditions in parsed_conditions:
                and_results = []
                for condition in and_conditions:
                    if condition[0] == "NOT":
                        # Verificar que la condición negada tenga tres elementos
                        if len(condition) < 2 or len(condition[1]) < 3:
                            print(f"Advertencia: Condición inválida {condition} para {cripto}. Se omite.")
                            continue
                        var, operator, val = condition[1]
                        pertenencia_valor = self.evaluate_condition(var, operator, val, cripto, datos)
                        pertenencia_valor = 1 - pertenencia_valor
                    else:
                        # Verificar que la condición tenga tres elementos
                        if len(condition) < 3:
                            print(f"Advertencia: Condición inválida {condition} para {cripto}. Se omite.")
                            continue
                        var, operator, val = condition
                        pertenencia_valor = self.evaluate_condition(var, operator, val, cripto, datos)

                    and_results.append(pertenencia_valor)

                # Manejar caso donde and_results está vacío
                if and_results:
                    and_result = min(and_results)
                    or_results.append(and_result)
                else:
                    # Asignar un valor predeterminado si no hay condiciones que se cumplan
                    or_results.append(0)

            # Manejar caso donde or_results está vacío
            if or_results:
                final_pert = max(or_results)
            else:
                final_pert = 0

            resultado = final_pert * action
            resultados[cripto] = resultado

        # Determinar la criptomoneda con el mayor impacto positivo
        if resultados:
            mejor_cripto = max(resultados, key=resultados.get)
            mejor_resultado = resultados[mejor_cripto]
        else:
            mejor_cripto = None
            mejor_resultado = 0

        return (mejor_resultado, mejor_cripto)


    def evaluate_operator(self, current_value, operator, val):
        # Evalúa operadores relacionales en las condiciones
        if operator == "es mayor que":
            return 1 if current_value > float(val) else 0
        elif operator == "es menor que":
            return 1 if current_value < float(val) else 0
        elif operator == "es aproximadamente igual a":
            return 1 if abs(current_value - float(val)) <= 0.05 * float(val) else 0
        elif operator == "está entre":
            # Divide el valor en límites inferior y superior, y verifica si el valor actual está entre ellos
            lower, upper = map(float, val.split(' y '))
            return 1 if lower <= current_value <= upper else 0