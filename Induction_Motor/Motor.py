from collections import deque
import random

# Operadores lógicos difusos
def fuzzy_and(a, b):
    return min(a, b)

def fuzzy_or(a, b):
    return max(a, b)

def fuzzy_not(a):
    return 1 - a

def boolean_to_fuzzy(value, high_confidence):
    if value == True:
        return 0.9 if high_confidence else 0.7  # Representa un "verdadero" difuso
    else:
        return 0.1 if high_confidence else 0.3  # Representa un "falso" difuso
    
class Node:
    def __init__(self, id, condition, action=None):
        self.id = id
        self.condition = condition
        self.action = action
        self.incoming = set()
        self.outgoing = set()

    def AddEdge(self, node, expression):
        """Conectar nodos con una expresión (condición)"""
        self.incoming.add(node.id)
        node.outgoing.add((expression, self.id))

class Belief(Node):
    def __init__(self, id, condition, action=None):
        super().__init__(id, condition, action)
        self.belief_value = 0  # Vacalor actual de la creencia
    
    def __str__(self):
        return f'ID: {self.id} Condition:{self.condition} incoming: {self.incoming} outgoing: {self.outgoing}'
    
class ByRule(Node):
    def __init__(self, id, condition, rules, delrules, action= None):
        super().__init__(id, condition, action)
        self.conditions = condition
        self.rules = rules
        self.delrules = delrules


    def __str__(self):
        return f'ID: {self.id} Condition:{self.condition} Rules: {self.rules} DelRules: {self.rules} incoming: {self.incoming} outgoing: {self.outgoing}'
    
class ByEdges(Node):
    def __init__(self, id, condition, delbeliefs, action= None):
        super().__init__(id, condition, action)
        self.conditions = condition
        self.delbeliefs = delbeliefs

    def __str__(self):
        return f'ID: {self.id} Condition:{self.condition} Delbeliefs: {self.delbeliefs} incoming: {self.incoming} outgoing: {self.outgoing}'
    
def create_graph_from_parser(parser_result):
    nodes = []
    node_counter = 0
    
    def find_belief_node(id):
        nonlocal nodes

        for node in nodes:
            if isinstance(node, Belief):
                if node.id == id:
                    return node
                
        return None

    def parse_belief(belief_name, value):
        pass

    def parse_rule(condition, action):
        pass

    def parse_condition(condition):
        if condition != None:
            if len(condition) == 3:
                left = parse_condition(condition[0])
                #print(f"OP: {condition[1]}")
                rigth = parse_condition(condition[2])
                return left + rigth
            elif len(condition) == 2:
                if condition[0] == "NO":
                    #print(f"OP: {condition[0]}")
                    return parse_condition(condition[1])
                else:
                    #print(condition[1])
                    return [condition[1]]
                

    def handle_Belief(beliefs):
        nonlocal nodes
        beliefs_list = []

        for belief in beliefs[2]:
            tempbelief = find_belief_node(belief[1])
            if tempbelief == None:
                beliefs_list += [Belief(belief[1],beliefs[1])]
            else:
                tempbelief.condition = beliefs[1]
        nodes += beliefs_list

    
    def handle_ByRules(statement):
        nonlocal node_counter
        nonlocal nodes

        rules = []
        delrules = []
        for st in statement[2]:
            if st[0] == 'statement_rule':
                rules += [st]
            elif st[0] == 'eliminar':
                for delst in st[1]:
                    delrules += [delst]

        node = ByRule(f'ByRules{node_counter}',statement[1], rules, delrules)
        node_counter += 1
        nodes.append(node)
    
    def handle_ByEdges(statement):
        nonlocal node_counter
        nonlocal nodes
        delbeliefs = []
        edgestocreate = []


        for belief in statement[2]:
            if belief[0] == "eliminar":
                for be in belief[1]:
                    delbeliefs.append(be[1])
            elif belief[0] == "NO":
                delbeliefs.append(belief[1][1])
            else:
                if isinstance(belief[0], tuple):
                    tempbelief = find_belief_node(belief[0][1])
                    if tempbelief == None:
                        newbelief = Belief(belief[0][1],None)
                        nodes.append(newbelief)
                    else:
                        newbelief = tempbelief
                    edgestocreate.append((newbelief, belief[1]))
                else:
                    tempbelief = find_belief_node(belief[1])
                    if tempbelief == None:
                        newbelief = Belief(belief[1], None)
                        nodes.append(newbelief)
                    else:
                        newbelief = tempbelief
                    edgestocreate.append((newbelief, None))

            
        
        node = ByEdges(f'ByEdges{node_counter}',statement[1],delbeliefs)
        for edge in edgestocreate:
            node.AddEdge(edge[0], edge[1])

        node_counter += 1
        nodes.append(node)
    
    for instruction in parser_result:
        # Procesar cada instrucción
        if instruction[1][0] == 'creencia_construct':
            handle_Belief(instruction[1])

        elif instruction[1][0] == 'statement_ByRules':
            handle_ByRules(instruction[1])

        else:
            handle_ByEdges(instruction[1])
    
    for node in nodes:
        #print(node.id)
        belief_list = parse_condition(node.condition)
        if belief_list != None:
            for bel in belief_list:
                node.AddEdge(find_belief_node(bel),None)


    return nodes

class FuzzyInferenceEngine:
    def __init__(self, nodes):
        self.nodes = nodes
        self.beliefs = {}
        self.generated_new_rules = []

    def boolean_to_fuzzy(self, value, high_confidence):
        """Convertir valores booleanos a lógica difusa."""
        if value == True:
            return 0.9 if high_confidence else 0.7  # Grado de certeza alto para True
        else:
            return 0.1 if high_confidence else 0.3  # Grado de certeza bajo para False

    def set_beliefs(self, beliefs_dict):
        """Establecer los valores iniciales de las creencias con lógica difusa."""
        for node in self.nodes:
            if isinstance(node, Belief):  # Solo procesa nodos que son creencias
                belief_id = node.id  # El ID de la creencia
                if belief_id in beliefs_dict:
                    # Convierte True/False a difuso y lo asigna a self.beliefs
                    fuzzy_value = self.boolean_to_fuzzy(beliefs_dict[belief_id], True)
                    self.beliefs[belief_id] = fuzzy_value
                    print(f"Creencia en agente \"{belief_id}\" asignada con valor difuso: {fuzzy_value}")
                else:
                    # Convierte True/False a difuso y lo asigna a self.beliefs
                    fuzzy_value = self.boolean_to_fuzzy(False, False)
                    self.beliefs[belief_id] = fuzzy_value
                    print(f"Creencia en grafo \"{belief_id}\" asignada con valor difuso: {fuzzy_value}")
    
    def get_beliefs(self):
        beliefs = {} 
        for belief in self.beliefs:
            if self.beliefs[belief] >= 0.8:
                beliefs[belief]=True
            elif self.beliefs[belief] <= 0.2:
                beliefs[belief]=False
        return beliefs

    def evaluate_belief(self, belief_name):
        """Evaluar el valor de una creencia usando lógica difusa."""
        return self.beliefs.get(belief_name)

    def apply_rules(self):
        """Aplicar las reglas del grafo basado en las creencias actuales."""
        for node in self.nodes:
            if isinstance(node, ByRule):
                self.evaluate_by_rule(node)
            elif isinstance(node, ByEdges):
                self.evaluate_by_edges(node)
    
    def delete_rule(self, del_rule, node):
        """Eliminar una regla del nodo."""
        if del_rule in node.rules:
            node.rules.remove(del_rule)
            print(f"Regla {del_rule} eliminada del nodo {node.id}")
        else:
            print(f"Regla {del_rule} no encontrada en nodo {node.id}")

    def evaluate_by_rule(self, node):
        """Evaluar un nodo de tipo ByRule."""
        condition_value = self.evaluate_condition(node.conditions)

        if condition_value > 0:

            # Si la condición es verdadera (en términos difusos)
            for rule in node.rules:
                action = rule[1]  # Acción a realizar
                print(f"Evaluando regla: {rule}")
                
                # Aquí ejecutas la acción que está asociada con la regla
                self.execute_action(action, node.id, rule)
            
            # Eliminación de reglas especificadas en node.delrules
            for del_rule in node.delrules:
                print(f"Eliminando regla: {del_rule} en {node.id}")
                self.delete_rule(del_rule, node)

            # Generar nuevas creencias basadas en condiciones
            new_beliefs = self.generate_new_beliefs(condition_value)
            for belief_id, value in new_beliefs.items():
                print(f"Cambiando creencia: {belief_id} a valor: {value} en {node.id}")
                self.beliefs[belief_id] = value  # Actualizar la creencia
    
    
    def evaluate_action(self, action):
        print(f"Acción a evaluar: {action}")
        return random.random()
    
    def execute_action(self, action, node_id, rule):
        """Evaluar una acción basada en una regla y generar nuevas reglas."""
        # Evaluar la condición 'action' (es decir, si es verdadera o falsa en términos difusos)
        action_value = self.evaluate_action(action)

        # Convertir el valor de la evaluación a lógica difusa
        if action_value > 0.8:  # Umbral para considerarlo como 'verdadero'
            print(f"Acción {action} evaluada como verdadera (valor difuso: {action_value}) en nodo {node_id}")
            
            # Si existe una nueva regla en rule[2], la generamos
            if len(rule) > 2:
                print(f"Generando nuevas reglas en nodo: {node_id}")
                new_rules = self.generate_new_rules(action_value)
                # Agregar la nueva regla al nodo actual
                for new_rule in new_rules:
                    if new_rule not in self.generated_new_rules:
                        self.generated_new_rules.append(new_rule)
                        print(f"Agregando nueva regla: {new_rule} en nodo {node_id}")

        else:
            print(f"Acción {action} evaluada como falsa (valor difuso: {action_value}) en nodo {node_id}")

    def generate_new_rules(self, condition_value):
        """Generar nuevas reglas basadas en el valor de la condición."""
        new_rules = []

        # Verificar si la condición es alta para generar nuevas reglas
        if condition_value > 0.5:
            for node in self.nodes:
                if isinstance(node, ByRule):
                    # Iterar sobre las reglas existentes en el nodo
                    for rule in node.rules:
                        new_rules.append(rule)

        return new_rules

    def generate_new_beliefs(self, condition_value):
        """Generar nuevas creencias basadas en el valor de la condición."""
        new_beliefs = {}

        # Obtener las creencias a evaluar desde self.beliefs
        beliefs_to_evaluate = list(self.beliefs.keys())

        for belief in beliefs_to_evaluate:
            current_value = self.beliefs.get(belief, False)

            # Cambiar el estado de la creencia basado en condition_value
            if condition_value > 0.7:
                # Si la condición es alta, establecer la creencia como True
                if not current_value:
                    new_beliefs[belief] = 0.9
            else:
                # Si la condición es baja, establecer la creencia como False
                if current_value:
                    new_beliefs[belief] = 0.1

        return new_beliefs

    def evaluate_by_edges(self, node):
        """Evaluar un nodo de tipo ByEdges."""
        for belief_id in node.delbeliefs:
            print(f"Eliminando creencia: {belief_id} en {node.id}")

        for edge in node.outgoing:
            target_node_id = edge[1]
            if target_node_id is not None:
                target_node = self.find_node_by_id(target_node_id)
                if target_node:
                    print(f"Conectando {node.id} a {target_node.id} con expresión: {edge[0]}")

    def evaluate_condition(self, condition):
        """Evaluar una condición dada."""
        
        if len(condition) == 3:
            left_value = self.evaluate_condition(condition[0])
            right_value = self.evaluate_condition(condition[2])
            operator = condition[1]

            if operator == 'AND':
                return min(left_value, right_value)  # Lógica difusa AND
            elif operator == 'OR':
                return max(left_value, right_value)   # Lógica difusa OR

        elif len(condition) == 2:  # Creencia simple
            if condition[0] == "NO":
                return 1 - self.evaluate_condition(condition[1])
            else:
                return  self.evaluate_belief(condition[1])

        return 0.0

    def find_node_by_id(self, id):
        """Buscar un nodo por su ID."""
        for node in self.nodes:
            if node.id == id:
                return node
        return None

    def generated_rules(self):
        return self.generated_new_rules


    def format_rule(self, rule):
        """Convierte una regla en una cadena legible."""
        # Descomponer la regla
        rule_type, belief, action_tuple = rule

        # Extraer creencia y acción
        _, belief_value = belief  # Creencia: ('creencia', 'novato')
        action_type, action_value, capital_tuple = action_tuple  # Acción: ('accion', 'COMPRAR', ('accion_capital', 'CAPITAL'))

        # Extraer el valor del capital
        _, capital_value = capital_tuple  # Capital: ('accion_capital', 'CAPITAL')

        # Formatear la cadena
        formatted_string = f"SI {belief_value} ENTONCES {action_value} {capital_value}"

        return formatted_string
    
    def print_generated_rules(self):
        """Imprime las reglas generadas en el formato deseado."""
        for node in self.nodes:
            if isinstance(node, ByRule):
                print(f"Nodo ID: {node.id}")
                for rule in node.rules:
                    formatted_rule = self.format_rule(rule)
                    print(f"Regla generada: {formatted_rule}")