from abc import ABC
from rules_interpreter import *
from typing import List, Dict
from market import *

class Agent(ABC):
    def __init__(self, name: str, initial_balance: Dict[str, float], intelligence):
        self.name = name
        self.initial_balance = initial_balance.copy()
        self.balance = initial_balance.copy()
        self.intelligence = intelligence
        self.portfolio = {crypto: 0 for crypto in initial_balance.keys() if crypto != "USD"}
        self.performance_history = []

    def calculate_total_value(self, market: Market):
        total_value = self.balance["USD"]
        for crypto, amount in self.portfolio.items():
            total_value += amount * market.cryptocurrencies[crypto].price
        return total_value

    def update_performance(self, market: Market):
        current_value = self.calculate_total_value(market)
        initial_value = sum(self.initial_balance.values())
        performance = (current_value - initial_value) / initial_value
        self.performance_history.append(performance)

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