class ASTNode:
    pass

class StatementNode(ASTNode):
    def __init__(self, condiciones, accion):
        self.condiciones = condiciones
        self.accion = accion

class ConditionNode(ASTNode):
    def __init__(self, left, operator, right):
        self.left = left
        self.operator = operator
        self.right = right

class ActionNode(ASTNode):
    def __init__(self, action_type, value):
        self.action_type = action_type
        self.value = value

class ExpressionNode(ASTNode):
    def __init__(self, variable, multiplier=None):
        self.variable = variable
        self.multiplier = multiplier

    def evaluate(self):
        if self.multiplier is not None:
            return f"{self.variable} * {self.multiplier}"
        return self.variable
    
def evaluate(ast):
    if isinstance(ast, StatementNode):
        # Evaluar condiciones
        if evaluate(ast.condiciones):
            return execute_action(ast.accion)
        else:
            return "Condiciones no cumplidas"

    elif isinstance(ast, ConditionNode):
        left_value = evaluate(ast.left)
        right_value = evaluate(ast.right)
        if ast.operator == 'AND':
            return left_value and right_value
        elif ast.operator == 'OR':
            return left_value or right_value
        # Aquí deberías manejar los comparadores
        return compare_values(left_value, right_value, ast.operator)

    elif isinstance(ast, ActionNode):
        return ast.action_type, evaluate(ast.value) if ast.value else None

    elif isinstance(ast, ExpressionNode):
        # Aquí podrías realizar cálculos adicionales según tu lógica
        return ast.evaluate()

def execute_action(action):
    if action.action_type == "COMPRAR":
        # Aquí iría tu lógica para comprar
        return f"Ejecutando acción: Comprar {action.value.evaluate()}"
    elif action.action_type == "VENDER":
        # Aquí iría tu lógica para vender
        return f"Ejecutando acción: Vender {action.value.evaluate()}"
    elif action.action_type == "MANTENER":
        return "Ejecutando acción: Mantener"

def compare_values(left, right, operator):
    # Implementa la lógica de comparación aquí según el operador
    return True  # Placeholder, debe ser reemplazado con la lógica real