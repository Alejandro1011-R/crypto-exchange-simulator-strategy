from Rules_Interpreter.rulelexer import RuleLexer
from Rules_Interpreter.ruleparser import RuleParser
from Induction_Motor.Motor import *
from Rules_Interpreter.ruleinterpreter import RuleInterpreter
from agents import *


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

    inference_engine=FuzzyInferenceEngine(nodes)

    # Establecer creencias iniciales (ejemplo).
    initial_beliefs={
       'novato': True,
       'experto': False,
       'MIEDOSO': False,
       'AVARICIOSO': True,
    }
    initial_prices = {
        "Bitcoin": 30000.0,
        "Ethereum": 2000.0,
        "Ripple": 1.0,
        "Litecoin": 150.0,
        "Cardano": 2.0,
    }

    initial_volatilities = {
        "Bitcoin": 0.01,
        "Ethereum": 0.02,
        "Ripple": 0.07,
        "Litecoin": 0.04,
        "Cardano": 0.03,
    }

    interp = RuleInterpreter()
    # Crear brokers con diferentes estrategias
    market=Market(initial_prices,initial_volatilities)
    agent = Agente('Broker 11', initial_beliefs, inference_engine=inference_engine, interpreter=interp)

    agent.action(market)

    # print(agent.beliefs)



    # inference_engine.set_beliefs(initial_beliefs)

    # # Aplicar reglas e imprimir resultados.
    # inference_engine.apply_rules()
    #inference_engine.print_generated_rules()
    # Imprimir todas las reglas generadas para cada nodo.

    # print()
    # print("********** RESULTADOS MOTOR INFERENCIA **************")
    # print()
    # print("******************** NUEVAS REGLAS *************************")
    # for rule in inference_engine.generated_rules():
    #     print(f"{rule}")
    # print()
    # print("****************** NUEVAS CREENCIAS ************************")
    # # Imprimir todas las creencias actuales.
    # beliefs = inference_engine.get_beliefs()

    # for belief in beliefs:
    #     print(f"Creencia: {belief}")
