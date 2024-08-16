import numpy as np
from typing import List
import matplotlib.pyplot as plt
from agents import *

class Simulation:
    def __init__(self, num_steps: int, agents: List[Agent], market: Market):
        self.num_steps = num_steps
        self.agents = agents
        self.market = market
        self.price_history = {crypto: [] for crypto in market.cryptocurrencies}
        self.volume_history = {crypto: [] for crypto in market.cryptocurrencies}
        self.sentiment_history = []
        self.agent_performances = {agent.name: [] for agent in agents}

    def run(self):
        for step in range(self.num_steps):
            # Simula el sentimiento del mercado
            market_sentiment = np.random.normal(0, 0.1)
            self.sentiment_history.append(market_sentiment)

            # Los agentes toman decisiones y ejecutan operaciones
            for agent in self.agents:
                decisions = agent.decide(self.market)
                agent.execute_trades(self.market, decisions)
                agent.update_performance(self.market)
                self.agent_performances[agent.name].append(agent.performance_history[-1])

            # Actualiza el estado del mercado
            self.market.update(market_sentiment)

            # Registra datos para análisis posterior
            self._record_data()

            # Imprime información del paso actual
            self._print_step_info(step)


    def _record_data(self):
        for crypto_name, crypto in self.market.cryptocurrencies.items():
            self.price_history[crypto_name].append(crypto.price)
            self.volume_history[crypto_name].append(crypto.volume)

    def _print_step_info(self, step):
        print(f"Step {step}: Timestamp = {self.market.timestamp}")
        for crypto_name, crypto in self.market.cryptocurrencies.items():
            print(f"  {crypto_name}: Price = ${crypto.price:.2f}, Volume = {crypto.volume:.2f}")

    def plot_results(self):
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 18))

        # Graficar precios
        for crypto, prices in self.price_history.items():
            ax1.plot(prices, label=crypto)
        ax1.set_title('Precio de las criptomonedas')
        ax1.set_xlabel('Pasos de tiempo')
        ax1.set_ylabel('Precio')
        ax1.legend()

        # Graficar volúmenes
        for crypto, volumes in self.volume_history.items():
            ax2.plot(volumes, label=crypto)
        ax2.set_title('Volumen de transacciones')
        ax2.set_xlabel('Pasos de tiempo')
        ax2.set_ylabel('Volumen')
        ax2.legend()

        # Graficar sentimiento del mercado
        ax3.plot(self.sentiment_history)
        ax3.set_title('Sentimiento del mercado')
        ax3.set_xlabel('Pasos de tiempo')
        ax3.set_ylabel('Sentimiento')

        ax4 = fig.add_subplot(414)
        for agent_name, performances in self.agent_performances.items():
            ax4.plot(performances, label=agent_name)
        ax4.set_title('Rendimiento de los agentes')
        ax4.set_xlabel('Pasos de tiempo')
        ax4.set_ylabel('Rendimiento (%)')
        ax4.legend()

        plt.tight_layout()
        plt.show()

    def get_summary(self):
        summary = {}
        for crypto_name, prices in self.price_history.items():
            summary[crypto_name] = {
                'initial_price': prices[0],
                'final_price': prices[-1],
                'price_change': (prices[-1] - prices[0]) / prices[0] * 100,
                'max_price': max(prices),
                'min_price': min(prices),
                'total_volume': sum(self.volume_history[crypto_name])
            }

        # Añadir resumen del rendimiento de los agentes
        summary['agent_performance'] = {}
        for agent in self.agents:
            final_value = agent.calculate_total_value(self.market)
            initial_value = sum(agent.initial_balance.values())
            performance = (final_value - initial_value) / initial_value * 100
            summary['agent_performance'][agent.name] = {
                'initial_value': initial_value,
                'final_value': final_value,
                'performance': performance,
                'max_performance': max(agent.performance_history) * 100,
                'min_performance': min(agent.performance_history) * 100,
                'avg_performance': sum(agent.performance_history) / len(agent.performance_history) * 100
            }

        return summary

    def get_performance(self):

        summary = self.get_summary()

        print("Resumen de la simulación:")
        for crypto, data in summary.items():
            if crypto != 'agent_performance':
                print(f"{crypto}:")
                for key, value in data.items():
                    print(f"  {key}: {value}")

        print("\nRendimiento de los agentes:")
        for agent_name, performance in summary['agent_performance'].items():
            print(f"{agent_name}:")
            for key, value in performance.items():
                print(f"  {key}: {value:.2%}")

        # Determinar la estrategia más efectiva
        best_agent = max(summary['agent_performance'], key=lambda x: summary['agent_performance'][x]['performance'])
        print(f"\nLa estrategia más efectiva fue: {best_agent}\n\n")

        return best_agent