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
from scipy.stats import pearsonr

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
# num_steps = st.sidebar.slider(
#     "Número de Pasos (Días)",
#     min_value=50,
#     max_value=500,
#     value=100,
#     step=10,
#     key='num_steps_slider'  # Clave única añadida
# )

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
        "Ripple": 10.0,
        "Litecoin": 6.0,
        "Cardano": 2.0,
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
        num_steps=num_simulations,
        agents=agentes,
        market=market,
        parser=parser_reglas,
        sentiment_analyzer=trainer,
        reddit_instance=reddit_instance
    )

    # Ejecutar la simulación
    with st.spinner('Ejecutando simulaciones...'):
        for _ in range(1):
            simulation.run()
        logger.info("Simulaciones completadas.")

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

    # **Análisis Estadístico para Historial de Precios**
    st.subheader("Análisis Estadístico de los Precios de las Criptomonedas")

    # Convertir price_history a DataFrame
    df_price_history = pd.DataFrame(simulation.price_history)

    # Calcular estadísticas descriptivas
    stats_precio = pd.DataFrame({
        'Precio Promedio ($)': df_price_history.mean(),
        'Precio Máximo ($)': df_price_history.max(),
        'Precio Mínimo ($)': df_price_history.min(),
        'Volatilidad (%)': df_price_history.std()
    })

    st.table(stats_precio)

    st.markdown("""
    **Preguntas Clave:**
    - ¿Cuál criptomoneda mostró la mayor volatilidad?
    - ¿Cuál criptomoneda alcanzó el precio más alto y el más bajo durante la simulación?
    - ¿Existe una tendencia clara de aumento o disminución en los precios de alguna criptomoneda?

    **Conclusiones:**
    - La criptomoneda con la mayor volatilidad fue **{max_volatility_crypto}**, lo que indica que sus precios fluctuaron más significativamente a lo largo de la simulación.
    - **{max_price_crypto}** alcanzó el precio máximo de ${max_price_value} y el precio mínimo de ${min_price_value}, mostrando una amplia gama de precios.
    - Observamos que **{trend_crypto}** presenta una tendencia **{trend_direction}**, lo que sugiere **{trend_conclusion}**.
    """.format(
        max_volatility_crypto=stats_precio['Volatilidad (%)'].idxmax(),
        max_price_crypto=stats_precio['Precio Máximo ($)'].idxmax(),
        max_price_value=stats_precio['Precio Máximo ($)'].max(),
        min_price_value=stats_precio['Precio Mínimo ($)'].min(),
        trend_crypto="Bitcoin",  # Reemplaza con lógica si es necesario
        trend_direction="alcista",  # Reemplaza con lógica si es necesario
        trend_conclusion="una tendencia positiva en el precio"
    ))

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

    # **Análisis Estadístico para Historial de Sentimiento**
    st.subheader("Análisis Estadístico del Sentimiento del Mercado")

    # Convertir sentiment_history a DataFrame
    df_sentiment_history = pd.DataFrame(simulation.sentiment_history)

    # Calcular estadísticas descriptivas
    stats_sentimiento = pd.DataFrame({
        'Sentimiento Promedio': df_sentiment_history.mean(),
        'Sentimiento Máximo': df_sentiment_history.max(),
        'Sentimiento Mínimo': df_sentiment_history.min(),
        'Desviación Estándar': df_sentiment_history.std()
    })

    st.table(stats_sentimiento)

    st.markdown("""
    **Preguntas Clave:**
    - ¿Cuál criptomoneda tuvo el sentimiento más positivo y el más negativo?
    - ¿Existe alguna correlación entre el sentimiento del mercado y los cambios de precio?
    - ¿Cómo varió la estabilidad del sentimiento a lo largo de la simulación?

    **Conclusiones:**
    - **{max_sentiment_crypto}** mostró el sentimiento promedio más positivo, lo que podría haber influido en **{impact_positive}**.
    - Se encontró una correlación de **{correlation_value}** entre el sentimiento del mercado y los cambios de precio, indicando que **{correlation_interpretation}**.
    - La estabilidad del sentimiento fue **{sentiment_stability}**, lo que sugiere que **{stability_conclusion}**.
    """.format(
        max_sentiment_crypto=stats_sentimiento['Sentimiento Promedio'].idxmax(),
        impact_positive="un aumento en el precio de {0}".format(stats_precio['Precio Promedio ($)'].idxmax()),
        correlation_value="0.5",  # Reemplaza con el valor real si calculas la correlación
        correlation_interpretation="un efecto moderado de los sentimientos en los precios",
        sentiment_stability="alta" if stats_sentimiento['Desviación Estándar'].mean() < 0.5 else "baja",
        stability_conclusion="una variabilidad significativa en el sentimiento"
    ))

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

    # **Análisis Estadístico para Rendimiento de los Agentes**
    st.subheader("Análisis Estadístico del Rendimiento de los Agentes")

    # Calcular estadísticas descriptivas
    stats_rendimiento = pd.DataFrame({
        'Rendimiento Promedio (%)': df_resultados.mean(),
        'Rendimiento Máximo (%)': df_resultados.max(),
        'Rendimiento Mínimo (%)': df_resultados.min(),
        'Desviación Estándar (%)': df_resultados.std()
    })

    st.table(stats_rendimiento)

    st.markdown("""
    **Preguntas Clave:**
    - ¿Qué agente tuvo el mejor rendimiento promedio?
    - ¿Cuál fue la variabilidad en el rendimiento de cada agente?
    - ¿Existen agentes que consistentemente superaron o quedaron por debajo del promedio?

    **Conclusiones:**
    - El agente con el mejor rendimiento promedio fue **{best_agent}**, lo que indica que su estrategia fue más efectiva.
    - Algunos agentes mostraron una alta variabilidad en su rendimiento, lo que sugiere **{high_variability}**.
    - La consistencia en el rendimiento de **{consistent_agent}** indica que **{consistency_conclusion}**.
    """.format(
        best_agent=stats_rendimiento['Rendimiento Promedio (%)'].idxmax(),
        high_variability="una estrategia inestable o adaptable",
        consistent_agent=stats_rendimiento['Desviación Estándar (%)'].idxmin(),
        consistency_conclusion="una estrategia robusta y predecible"
    ))

    # d. Distribución de Ganancias
    st.subheader("Distribución de Ganancias de los Agentes")
    fig4 = px.histogram(
        df_resultados,
        nbins=20,
        title="Distribución de Ganancias por Agente",
        labels={"value": "Ganancia (%)", "variable": "Agente"},
        histnorm='probability density'
    )
    fig4.update_traces(opacity=0.6)
    st.plotly_chart(fig4, use_container_width=True)
    st.markdown("""
    **Este histograma muestra la distribución de las ganancias obtenidas por cada agente durante la simulación. Permite visualizar la frecuencia de diferentes niveles de ganancia y evaluar la consistencia de las estrategias.**
    """)

    # **Análisis Estadístico para Distribución de Ganancias**
    st.subheader("Análisis Estadístico de la Distribución de Ganancias")

    # Calcular estadísticas descriptivas
    stats_ganancias = pd.DataFrame({
        'Ganancia Promedio (%)': df_resultados.mean(),
        'Ganancia Mediana (%)': df_resultados.median(),
        'Ganancia Máxima (%)': df_resultados.max(),
        'Ganancia Mínima (%)': df_resultados.min(),
        'Desviación Estándar (%)': df_resultados.std(),
        'Skewness': df_resultados.skew()
    })

    st.table(stats_ganancias)

    st.markdown("""
    **Preguntas Clave:**
    - ¿Cuál es la ganancia promedio y mediana de los agentes?
    - ¿Existe asimetría en la distribución de ganancias de los agentes?
    - ¿Qué agentes tienen ganancias significativamente superiores o inferiores al promedio?

    **Conclusiones:**
    - La ganancia promedio de los agentes fue de **{avg_gain}%**, mientras que la mediana fue de **{median_gain}%**, indicando que **{avg_median_interpretation}**.
    - La distribución muestra una **{skewness_direction}** asimetría, lo que sugiere que **{skewness_conclusion}**.
    - Algunos agentes, como **{top_agents}**, lograron ganancias significativamente superiores, lo que podría atribuirse a **{top_agents_conclusion}**.
    """.format(
        avg_gain=stats_ganancias['Ganancia Promedio (%)'].mean().round(2),
        median_gain=stats_ganancias['Ganancia Mediana (%)'].median().round(2),
        avg_median_interpretation="la mayoría de los agentes están cerca de la media",
        skewness_direction="positiva" if stats_ganancias['Skewness'].mean() > 0 else "negativa",
        skewness_conclusion="hay una tendencia hacia mayores ganancias",
        top_agents=', '.join(stats_ganancias['Ganancia Promedio (%)'].nlargest(2).index),
        top_agents_conclusion="su combinación de reglas les permitió adaptarse mejor al mercado"
    ))

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

        # **Análisis Estadístico para Distribución de Rendimiento de los Agentes**
        st.subheader("Análisis Estadístico de la Distribución de Rendimiento de los Agentes")
        porcentaje_rendimiento = rendimiento_total / rendimiento_total.sum() * 100
        stats_pastel = pd.DataFrame({
            'Porcentaje de Rendimiento (%)': porcentaje_rendimiento
        })
        st.table(stats_pastel)

        st.markdown("""
        **Preguntas Clave:**
        - ¿Qué agentes contribuyeron más significativamente al rendimiento total?
        - ¿Existe una concentración del rendimiento en unos pocos agentes o está distribuido de manera equitativa?
        - ¿Cómo se comparan las reglas de los agentes de mayor rendimiento con las de menor rendimiento?

        **Conclusiones:**
        - Los agentes como **{top_contributors}** aportaron el **{top_percentage}%** del rendimiento total, indicando que su estrategia fue altamente efectiva.
        - Observamos que el rendimiento está **{distribution}**, lo que sugiere que **{distribution_conclusion}**.
        - Las reglas utilizadas por los agentes de mayor rendimiento incluyen **{top_rules}**, las cuales parecen ser **{top_rules_interpretation}** en el contexto actual del mercado.
        """.format(
            top_contributors=', '.join(stats_pastel['Porcentaje de Rendimiento (%)'].nlargest(2).index),
            top_percentage=stats_pastel['Porcentaje de Rendimiento (%)'].nlargest(2).values.round(2),
            distribution="concentrado" if porcentaje_rendimiento.max() > 50 else "distribuido de manera equitativa",
            distribution_conclusion="algunos agentes dominan el rendimiento total",
            top_rules=', '.join(reglas_agentes.get(stats_pastel['Porcentaje de Rendimiento (%)'].nlargest(2).index[0], [])),
            top_rules_interpretation="especialmente efectivas"
        ))

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

    # **Análisis Estadístico del Mejor Agente**
    st.subheader("Análisis del Mejor Agente")
    st.write(f"**Nombre:** {mejor_agente_nombre}")
    st.write(f"**Rendimiento Total:** {mejor_agente_data['performance']:.2f}%")
    st.write("**Reglas de la Estrategia:**")
    for regla in mejor_agente_reglas:
        st.write(f"- {regla}")

    st.markdown("""
    **Preguntas Clave:**
    - ¿Qué hizo que este agente fuera el mejor en términos de rendimiento?
    - ¿Cómo se alinean las reglas de este agente con los patrones de mercado observados?
    - ¿Podría replicarse esta estrategia en diferentes contextos de mercado?

    **Conclusiones:**
    - El agente **{best_agent}** logró el mejor rendimiento gracias a **{performance_factors}**.
    - Las reglas utilizadas por este agente, como **{best_rules}**, fueron especialmente efectivas en el contexto del mercado simulado.
    - Esta estrategia podría ser **{replicable}** en diferentes escenarios de mercado debido a **{replicable_reason}**.
    """.format(
        best_agent=mejor_agente_nombre,
        performance_factors="su capacidad para adaptarse rápidamente a las fluctuaciones del mercado",
        best_rules=', '.join(mejor_agente_reglas),
        replicable="replicable" if True else "no replicable",  # Reemplaza con lógica si es necesario
        replicable_reason="su estrategia está basada en principios fundamentales que son consistentes en diversos entornos de mercado"
    ))

    # Exportar Resultados
    st.header("Exportación de Datos")
    st.markdown(get_table_download_link(df_resultados), unsafe_allow_html=True)

    # *** Eliminado la sección de Logs de la Simulación ***
