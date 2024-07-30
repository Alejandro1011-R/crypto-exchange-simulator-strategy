from abc import ABC

class Agent(ABC):
    def __init__(self, name, rules):
        self.name = name
        self.rules = rules
        self.holdings = 0
        self.cash = 10000  # cada broker comienza con $10,000 en efectivo
        self.transaction_history = []

    def decide(self, price, price_history, rule_interpreter):
        rule_interpreter.run_rules(self.rules, self, price, price_history)