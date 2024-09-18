import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import seaborn as sns
import logging
from io import StringIO
import base64
from simulation import *
from rules_interpreter import *  # Asegúrate de que este módulo exista
import time


# Configurar el estilo de los gráficos
sns.set(style="whitegrid")

# Configurar el logging
logger = logging.getLogger('streamlit_simulation')
logger.setLevel(logging.INFO)
log_stream = StringIO()
stream_handler = logging.StreamHandler(log_stream)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

# Función para descargar datos como CSV
def get_table_download_link(df, filename="simulation_results.csv"):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # Codificar en base64
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">Descargar Resultados en CSV</a>'
    return href

# Función para cargar reglas desde archivos de texto
def load_rules_from_file(file_path):
    try:
        with open(file_path, 'r') as file:
            rules = [line.strip() for line in file if line.strip()]
        return rules
    except FileNotFoundError:
        st.error(f"Archivo de reglas no encontrado: {file_path}")
        return []

# Título de la aplicación
st.title("Simulación de Mercado de Criptomonedas")

# Sección de Configuración de la Simulación
st.sidebar.header("Configuración de la Simulación")

# Número de Pasos (Días) por Simulación con clave única
num_steps = st.sidebar.slider(
    "Número de Pasos (Días)",
    min_value=50,
    max_value=500,
    value=100,
    step=10,
    key='num_steps_slider'  # Clave única añadida
)

# Número de Simulaciones con clave única
num_simulations = st.sidebar.slider(
    "Número de Simulaciones",
    min_value=10,
    max_value=1000,
    value=30,
    step=10,
    key='num_simulations_slider'  # Clave única añadida
)

# Definir estrategias fijas
estrategias_disponibles = {
    "Comprar cuando el precio es bajo": [
        "SI precio es bajo ENTONCES comprar",
        "SI precio es alto ENTONCES mantener",
        "SI precio es medio ENTONCES mantener"
    ],
    "Vender cuando el precio es alto": [
        "SI precio es alto ENTONCES vender",
        "SI precio es bajo ENTONCES mantener",
        "SI precio es medio ENTONCES mantener"
    ],
    "Mantener cuando el precio es medio": [
        "SI precio es medio ENTONCES mantener",
        "SI precio es bajo ENTONCES comprar",
        "SI precio es alto ENTONCES vender"
    ]
}

# Botón para Iniciar la Simulación
if st.sidebar.button("Iniciar Simulación"):
    # Crear instancia de Map y obtener pertenencia_map
    map_obj = Map()
    pertenencia_map = map_obj.pertenencia_map

    # Crear instancia del ParserReglas
    parser_reglas = ParserReglas(pertenencia_map=pertenencia_map)

    # Definir valores iniciales para cada criptomoneda
    initial_prices = {
        "Bitcoin": 30000.0,
        "Ethereum": 2000.0,
        "Ripple": 1.0,
        "Litecoin": 150.0,
        "Cardano": 2.0,
        # Añadir más criptomonedas según sea necesario
    }

    initial_volatilities = {
        "Bitcoin": 0.9,
        "Ethereum": 0.7,
        "Ripple": 0.5,
        "Litecoin": 0.6,
        "Cardano": 0.8,
        # Añadir más criptomonedas según sea necesario
    }

    # Definir criptomonedas predefinidas desde `pertenencia_map` con valores numéricos
    criptos = []
    for nombre in pertenencia_map.keys():
        precio_inicial = initial_prices.get(nombre, 1000.0)        # Valor por defecto si no está definido
        volatilidad = initial_volatilities.get(nombre, 0.05)      # Valor por defecto si no está definido
        criptos.append(Cryptocurrency(name=nombre, initial_price=precio_inicial, initial_volatility=volatilidad))

    # Crear instancia del Mercado
    market = Market(cryptocurrencies=criptos)

    # Cargar reglas desde archivos de texto
    rules_buy_low_sell_high = load_rules_from_file('rules/rules_buy_low_sell_high.txt')
    rules_sentiment = load_rules_from_file('rules/rules_sentiment.txt')
    rules_inversor = load_rules_from_file('rules/rules_inversor.txt')

    # Crear agentes según las estrategias seleccionadas
    brokers = [
        Agente('Estrategia Guiado Por Sentimiento del Mercado', rules_sentiment, parser_reglas),
        Agente('Estrategia Comprar Bajo y Vender Alto', rules_buy_low_sell_high, parser_reglas),
        Agente('Estrategia Inversor', rules_inversor, parser_reglas)
    ]
    agentes = brokers  # Ya son los brokers especificados

    # Crear instancia de SentimentAnalyzer y CryptoTradingAgent una sola vez
    trainer = SentimentAnalyzer('.env')
    reddit_instance = CryptoTradingAgent('.env')

    # Crear instancia de la Simulación pasando las instancias de SentimentAnalyzer y CryptoTradingAgent
    simulation = Simulation(
        num_steps=num_steps,
        agents=agentes,
        market=market,
        parser=parser_reglas,
        sentiment_analyzer=trainer,
        reddit_instance=reddit_instance
    )

    # Ejecutar la simulación
    with st.spinner('Ejecutando simulaciones...'):
        simulation.run()
        logger.info("Simulación completada.")

    # Asegurar que todas las listas en agent_performances tengan la misma longitud
    max_length = max(len(lst) for lst in simulation.agent_performances.values())
    for key, lst in simulation.agent_performances.items():
        if len(lst) < max_length:
            lst.extend([np.nan] * (max_length - len(lst)))

    # Convertir los resultados a un DataFrame
    df_resultados = pd.DataFrame(simulation.agent_performances)

    # Guardar resultados en un archivo CSV
    df_resultados.to_csv("simulation_results.csv", index=False)

    # Obtener el mejor agente usando el método get_performance()
    mejor_agente = simulation.get_performance()

    # Obtener el rendimiento total de los agentes para el gráfico de pastel
    rendimiento_total = df_resultados.sum().dropna()

    # Filtrar valores negativos y cero para evitar errores en el gráfico de pastel
    rendimiento_total = rendimiento_total[rendimiento_total > 0]

    # Visualizaciones de Resultados
    st.header("Visualización de Resultados")

    # a. Historial de Precios
    st.subheader("Historial de Precios de las Criptomonedas")
    fig1 = px.line(
        simulation.price_history,
        labels={"value": "Precio ($)", "index": "Pasos de Tiempo", "variable": "Criptomoneda"},
        title="Evolución de los Precios de las Criptomonedas"
    )
    fig1.update_traces(mode='lines+markers')
    st.plotly_chart(fig1, use_container_width=True)
    st.markdown("""
    **Este gráfico muestra la evolución de los precios de cada criptomoneda a lo largo de los pasos de tiempo de la simulación. Las líneas representan el cambio en el precio, permitiendo observar tendencias y volatilidad.**
    """)

    # b. Historial de Sentimiento
    st.subheader("Historial de Sentimiento del Mercado")
    fig2 = px.line(
        simulation.sentiment_history,
        labels={"value": "Sentimiento", "index": "Pasos de Tiempo", "variable": "Criptomoneda"},
        title="Evolución del Sentimiento del Mercado"
    )
    fig2.update_traces(mode='lines+markers')
    st.plotly_chart(fig2, use_container_width=True)
    st.markdown("""
    **Este gráfico muestra cómo varió el sentimiento del mercado para cada criptomoneda durante la simulación. Un sentimiento positivo indica una percepción favorable, mientras que uno negativo refleja lo contrario.**
    """)

    # c. Rendimiento de los Agentes
    st.subheader("Rendimiento de los Agentes")
    fig3 = px.line(
        df_resultados,
        labels={"value": "Rendimiento (%)", "index": "Pasos de Tiempo", "variable": "Agente"},
        title="Rendimiento Acumulado de los Agentes"
    )
    fig3.update_traces(mode='lines+markers')
    st.plotly_chart(fig3, use_container_width=True)
    st.markdown("""
    **Este gráfico muestra el rendimiento acumulado de cada agente a lo largo de la simulación. Permite comparar qué agentes han sido más exitosos en sus estrategias de trading.**
    """)

    # d. Distribución de Ganancias
    st.subheader("Distribución de Ganancias de los Agentes")
    fig4 = px.histogram(
        df_resultados,
        nbins=20,
        title="Distribución de Ganancias por Agente",
        labels={"value": "Ganancia", "variable": "Agente"},
        histnorm='probability density'
    )
    fig4.update_traces(opacity=0.6)
    st.plotly_chart(fig4, use_container_width=True)
    st.markdown("""
    **Este histograma muestra la distribución de las ganancias obtenidas por cada agente durante la simulación. Permite visualizar la frecuencia de diferentes niveles de ganancia y evaluar la consistencia de las estrategias.**
    """)

    # *** Gráficas de Pastel sin Filtrado ***
    st.header("Distribución de Rendimiento de los Agentes")

    if rendimiento_total.empty:
        st.warning("No hay rendimientos positivos para mostrar en el gráfico de pastel.")
    else:
        # Crear gráfica de pastel con las reglas en hover
        # Obtener las reglas de cada agente
        reglas_agentes = {agente.nombre: agente.reglas for agente in simulation.agents if agente.nombre in rendimiento_total.index}

        hover_text = [f"{agente}<br>{'<br>'.join(reglas_agentes.get(agente, []))}" for agente in rendimiento_total.index]

        fig_pastel = px.pie(
            names=rendimiento_total.index,
            values=rendimiento_total.values,
            title="Distribución de Rendimiento de los Agentes",
            hover_data={'Reglas': hover_text},
            labels={"Reglas": "Reglas de la Estrategia"}
        )
        fig_pastel.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pastel, use_container_width=True)
        st.markdown("""
        **Este gráfico de pastel muestra la distribución del rendimiento total de los agentes. Al pasar el cursor sobre cada sección, se muestran las reglas que cada agente utilizó en su estrategia de trading.**
        """)

    # *** Identificar y Mostrar el Mejor Agente y su Estrategia ***
    # Obtener el mejor agente y sus reglas
    summary = simulation.get_summary()
    mejor_agente_nombre = simulation.get_performance()
    mejor_agente_data = summary['agent_performance'][mejor_agente_nombre]
    mejor_agente_reglas = mejor_agente_data.get('rules', "No disponible")

    # Mostrar el mejor agente y su estrategia de forma no HTML, usando Streamlit components
    st.header("Mejor Agente de la Simulación")
    st.write(f"**Nombre del Agente:** {mejor_agente_nombre}")
    st.write(f"**Rendimiento:** {mejor_agente_data['performance']:.2f}%")
    st.write("**Estrategia:**")
    for regla in mejor_agente_reglas:
        st.write(f"- {regla}")

    # Exportar Resultados
    st.header("Exportación de Datos")
    st.markdown(get_table_download_link(df_resultados), unsafe_allow_html=True)

    # *** Eliminado la sección de Logs de la Simulación ***
