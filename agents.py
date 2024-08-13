from abc import ABC
from rule_interpreter import *

class Agent(ABC):
    def __init__(self, name: str, initial_balance: Dict[str, float], intelligence: RuleInterpreter):
        # Inicializa un agente con un nombre, balance inicial y una inteligencia
        self.name = name
        self.balance = initial_balance
        self.intelligence = intelligence
        self.portfolio = {crypto: 0 for crypto in initial_balance.keys()}

    def decide(self, market: Market) -> Dict[str, List[tuple]]:
        # Toma decisiones de trading basadas en la inteligencia del agente
        return self.intelligence.make_decision(market, self.balance, self.portfolio)

    def execute_trades(self, market: Market, decisions: Dict[str, List[tuple]]):
        # Ejecuta las decisiones de trading en el mercado
        for crypto_name, orders in decisions.items():
            crypto = market.cryptocurrencies[crypto_name]
            for order_type, amount, price in orders:
                if order_type == "buy":
                    cost = amount * price
                    if self.balance["USD"] >= cost:
                        self.balance["USD"] -= cost
                        self.portfolio[crypto_name] += amount
                        crypto.add_order("buy", price, amount)
                elif order_type == "sell":
                    if self.portfolio[crypto_name] >= amount:
                        self.portfolio[crypto_name] -= amount
                        self.balance["USD"] += amount * price
                        crypto.add_order("sell", price, amount)