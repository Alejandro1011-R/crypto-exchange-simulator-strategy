from collections import deque
from rulelexer import RuleLexer
#from ..Rules_Interpreter.rulelexer import RuleLexer
#from ..Rules_Interpreter.ruleparser import RuleParser
from ruleparser import RuleParser


class Node:
    def __init__ (self,id,condition,action):
        self.id = id
        self.condition = condition
        self.action = action
        self.incoming = set()
        self.outgoing = set()
        

    def Indegree(self): return len(self.incoming)

    def Outdegree(self): return len(self.outgoing)

    def AddEdge(self, node, expression): 
        self.incoming.add(node.id)
        node.outgoing.add((expression,self.id))#ver luego


    def DoAction(self,graph,context):
        exec(self.action)

    def Induction(self,graph,context):
            exec(action)
            graph.inductedIds.add(self.id)
            for out in self.outgoing:
                if exec(out[0]):
                    if isinstance(graph.nodes[out[1]],AndNode):
                        out[1].vality[self.id] = True
                        if all(out[1].vality.values()):
                           graph.queue.append(out[1]) 
                    else:
                        graph.queue.append(out[1])

    
class AndNode(Node):
    def __init__ (self,id,condition,action):
       super().__init__(id,condition,action)
       self.vality = {}

    def AddEdge(self,node): 
        self.incoming.add(node.id)
        self.vality[node.id]= False

        node.outgoing.add((expression,self.id))#ver luego

    def Induction(self,graph,context):
            exec(action)
            self.vality = {key: False for key in self.vality}
            graph.inductedIds.add(self.id)
            for out in self.outgoing:
                if exec(out[0]):
                    if isinstance(graph.nodes[out[1]],AndNode):
                        out[1].vality[self.id] = True
                        if all(out[1].vality.values()):
                           graph.queue.append(out[1]) 
                    else:
                        graph.queue.append(out[1])
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
    
class Graph:
    def __init__ (self,nodes):
        self.nodes={node.id:node for node in nodes}
        self.inductedIds = set()
        self.inductedBelief = set()
        self.inductedDesires = set()
        self.queue = deque()

    def Validation(self,context):

        self.inductedIds.clear()
        self.inductedBelief.clear()
        self.inductedDesires.clear()
        for id,node in self.nodes.items():
            if eval(node.condition):#arreglar
                self.inductedIds.add(id)
                self.queue.append(id)
                exec(node.action)
        return  

    def Induction(self,context):
        self.Validation(context)
        while not(len(self.queue) == 0):
            node = self.nodes[self.queue.popleft()]
            node.Induction(self,context)
        return  self.inductedBelief,self.inductedDesires


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
        pass

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
    
    return nodes

if __name__ == '__main__':
    lex = RuleLexer()
    par = RuleParser()

    rules = """SI ERES NO novato Y experto ENTONCES SI novato ENTONCES COMPRAR capital , SI experto ENTONCES COMPRAR capital 
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
    result = par.parse(lex.tokenize(rules))
    for instruction in result:
        print(instruction)

    nodes = create_graph_from_parser(result)
    for n in nodes:
            print(n)
            