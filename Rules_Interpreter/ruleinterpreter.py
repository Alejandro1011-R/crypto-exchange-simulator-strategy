class RuleInterpreter():

    def evaluate(self, node, context):
        if isinstance(node, tuple):
            tipo = node[0]

            if tipo == "instruccion":
                return self.evaluate(node[1], context)
            elif tipo == "statement_rule":
                # Evaluamos la condición y luego ejecutamos la acción asociada
                condicion = self.evaluate(node[1], context)
                #accion = self.evaluate(node[2], context)
                return (condicion, node[2])
            elif tipo == 'number':
                return float(node[1])
            elif tipo == "AND":
                return min(self.evaluate(node[1], context), self.evaluate(node[2], context))
            elif tipo == "OR":
                return max(self.evaluate(node[1], context) or self.evaluate(node[2], context))

            elif tipo == "*":
                return self.evaluate(node[1], context) * self.evaluate(node[2], context)

            elif tipo == 'es':
                return 0.9 if self.evaluate(node[1], context) == self.evaluate(node[2], context) else 0.1

            elif tipo == 'no es':
                return 0.9 if self.evaluate(node[1], context) != self.evaluate(node[2], context) else 0.1

            elif tipo == 'menor o igual que':
                return 0.9 if self.evaluate(node[1], context) <= self.evaluate(node[2], context) else 0.1

            elif tipo == 'menor que':
                return 0.9 if self.evaluate(node[1], context) < self.evaluate(node[2], context) else 0.1

            elif tipo == 'mayor o igual que':
                return 0.9 if self.evaluate(node[1], context) >= self.evaluate(node[2], context) else 0.1

            elif tipo == 'mayor que':
                return 0.9 if self.evaluate(node[1], context) > self.evaluate(node[2], context) else 0.1

            elif tipo == "accion":
                return node
            elif tipo == "creencia":
                # Aquí accedemos a la creencia en el diccionario `beliefs`
                creencia_name = node[1]
                if creencia_name in context["beliefs"]:
                    return context["beliefs"][creencia_name]
                else:
                    print(f"Creencia {creencia_name} no encontrada.")
                    return None
            elif tipo == "variable":
                # Evaluamos una variable específica dentro de beliefs
                var_name = node[1]
                if var_name in context:
                    return context[var_name]
                else:
                    print(f"Variable {var_name} no encontrada.")
                    return None

            else:
                print(f"Tipo desconocido: {tipo}")
                return None
        else:
            return node