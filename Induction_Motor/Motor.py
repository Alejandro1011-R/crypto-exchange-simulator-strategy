from collections import deque
class Node:
    def __init__ (self,id,condition,action):
        self.id = id
        self.condition = condition
        self.action = action
        self.incoming = set()
        self.outgoing = set()
        

    def Indegree(self): return len(self.incoming)

    def Outdegree(self): return len(self.outgoing)

    def AddEdge(self,node): 
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



            