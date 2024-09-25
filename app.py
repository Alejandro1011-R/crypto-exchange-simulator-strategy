import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import logging
from io import StringIO
import base64
from simulation import *
from rules_interpreter import *  # Asegúrate de que este módulo exista
import time
from scipy.stats import pearsonr
from llm import *
import plotly.express as px
import seaborn as sns

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

# Número de Simulaciones con clave única
num_simulations = st.sidebar.slider(
    "Número de Simulaciones",
    min_value=10,
    max_value=1000,
    value=30,
    step=10,
    key='num_simulations_slider'  # Clave única añadida
)

# Botón para reiniciar la simulación
def reset_simulation():
    for key in list(st.session_state.keys()):
        if key.startswith('price_history_df') or key.startswith('sentiment_history_df') \
           or key.startswith('df_resultados') or key.startswith('data_loaded') \
           or key.startswith('rendimiento_total') or key.startswith('agentes') \
           or key.startswith('mejor_agente') or key.startswith('summary'):
            del st.session_state[key]

if st.sidebar.button("Reiniciar Simulación"):
    reset_simulation()
    # Verificar si 'experimental_rerun' está disponible
    if hasattr(st, 'rerun'):
        st.rerun()
    else:
        st.warning("`st.experimental_rerun()` no está disponible en tu versión de Streamlit. Por favor, actualiza Streamlit ejecutando `pip install --upgrade streamlit`.")

# Verificar si los datos ya están en el estado de sesión o si se necesita recomputar
if 'data_loaded' not in st.session_state or not st.session_state['data_loaded']:
    if st.sidebar.button("Iniciar Simulación"):
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

        # Crear instancia de Map y obtener pertenencia_map
        map_obj = Map()
        pertenencia_map = map_obj.pertenencia_map

        # Crear instancia del ParserReglas
        parser_reglas = ParserReglas(pertenencia_map=pertenencia_map)

        # Definir criptomonedas predefinidas
        criptos = []
        for nombre in pertenencia_map.keys():
            precio_inicial = initial_prices.get(nombre, 1000.0)
            volatilidad = initial_volatilities.get(nombre, 0.05)
            criptos.append(Cryptocurrency(name=nombre, initial_price=precio_inicial, initial_volatility=volatilidad))

        # Crear instancia del Mercado
        market = Market(initial_prices, initial_volatilities)

        # Cargar reglas desde archivos de texto
        rules_buy_low_sell_high = load_rules_from_file('rules/rules_buy_low_sell_high.txt')
        rules_sentiment = load_rules_from_file('rules/rules_sentiment.txt')
        rules_inversor = load_rules_from_file('rules/rules_inversor.txt')

        # Crear agentes según las estrategias seleccionadas
        brokers = [
            Agente('Estrategia Guiado Por Sentimiento del Mercado', rules_sentiment, parser_reglas),
            Agente('Estrategia Comprar Bajo y Vender Alto', rules_buy_low_sell_high, parser_reglas),
            Agente('Estrategia Inversor', rules_inversor, parser_reglas),
        ]

        # Crear instancia de SentimentAnalyzer y CryptoTradingAgent
        trainer = SentimentAnalyzer('.env')
        reddit_instance = CryptoTradingAgent('.env')

        # Crear instancia de la Simulación
        simulation = Simulation(
            num_steps=num_simulations,
            agents=brokers,
            market=market,
            parser=parser_reglas,
            sentiment_analyzer=trainer,
            reddit_instance=reddit_instance
        )

        # Ejecutar la simulación
        with st.spinner('Ejecutando simulaciones...'):
            simulation.run()
            logger.info("Simulaciones completadas.")

        # Asegurar que todas las listas en agent_performances tengan la misma longitud
        max_length = max(len(lst) for lst in simulation.agent_performances.values())
        for key, lst in simulation.agent_performances.items():
            if len(lst) < max_length:
                lst.extend([np.nan] * (max_length - len(lst)))

        # Convertir los resultados a un DataFrame
        df_resultados = pd.DataFrame(simulation.agent_performances)

        # Obtener el mejor agente usando el método get_performance()
        mejor_agente = simulation.get_performance()

        # Obtener el rendimiento total de los agentes para el gráfico de pastel
        rendimiento_total = df_resultados.sum().dropna()

        # Filtrar valores negativos y cero para evitar errores en el gráfico de pastel
        rendimiento_total = rendimiento_total[rendimiento_total > 0]

        # Convertir los resultados a un DataFrame y guardar en el estado de la sesión
        st.session_state['price_history_df'] = simulation.price_history_df
        st.session_state['rendimiento_total'] = rendimiento_total
        st.session_state['agentes'] = simulation.agents
        st.session_state['sentiment_history_df'] = simulation.sentiment_history_df
        st.session_state['df_resultados'] = df_resultados
        st.session_state['data_loaded'] = True
        st.session_state['mejor_agente'] = mejor_agente
        st.session_state['summary'] = simulation.get_summary()

        st.success("Simulación completada y datos cargados en el estado de la sesión.")

# Si los datos están cargados, mostrar resultados sin recalcular
if 'data_loaded' in st.session_state and st.session_state['data_loaded']:
    # Filtrar columnas para excluir 'Time' o cualquier otra columna no relacionada con criptomonedas
    crypto_columns = [col.split('_')[0] for col in st.session_state['price_history_df'].columns if '_' in col]
    crypto_options = sorted(set(crypto_columns))

    # Selectbox único para seleccionar la criptomoneda
    crypto_to_plot = st.selectbox(
        "Selecciona la Criptomoneda para Visualizar",
        options=crypto_options,
        index=0
    )

    # Gráfico de precios usando datos del estado de sesión
    df_crypto = st.session_state['price_history_df']
    st.write("### Gráfico de Precios")
    fig = go.Figure(data=[go.Candlestick(
        x=df_crypto['Time'],
        open=df_crypto[f'{crypto_to_plot}_open'],
        high=df_crypto[f'{crypto_to_plot}_high'],
        low=df_crypto[f'{crypto_to_plot}_low'],
        close=df_crypto[f'{crypto_to_plot}_close'],
        increasing_line_color='green',
        decreasing_line_color='red'
    )])
    fig.update_layout(title=f"Evolución de los Precios de {crypto_to_plot}", xaxis_title='Tiempo de la Simulación', yaxis_title='Precio ($)')
    st.plotly_chart(fig, use_container_width=True)

    # Gráfico de Sentimientos del Mercado
    st.write("### Historial de Sentimiento del Mercado")

    df_sentiment = st.session_state['sentiment_history_df']

    # Verificar y corregir la columna 'Time' si es necesario
    if 'Time' not in df_sentiment.columns:
        # Resetear el índice y renombrar 'index' a 'Time' solo si 'Time' no existe
        df_sentiment = df_sentiment.reset_index().rename(columns={'index': 'Time'})
    else:
        # Si 'Time' ya existe, resetear el índice sin renombrar
        df_sentiment = df_sentiment.reset_index(drop=True)

    # Asegurarse de que 'Time' sea integer (pasos de simulación)
    if not np.issubdtype(df_sentiment['Time'].dtype, np.integer):
        try:
            df_sentiment['Time'] = df_sentiment['Time'].astype(int)
        except Exception as e:
            st.error(f"Error al convertir 'Time' a integer: {e}")

    # Asegurarse de que el 'Time' esté ordenado
    df_sentiment = df_sentiment.sort_values(by='Time')

    # Crear el gráfico de barras para el sentimiento
    fig2 = go.Figure()

    # Definir colores basados en el sentimiento
    colors = ['green' if val > 0 else 'red' if val < 0 else 'gray' for val in df_sentiment[f'{crypto_to_plot}_sentiment']]

    # Añadir el gráfico de barras
    fig2.add_trace(go.Bar(
        x=df_sentiment['Time'],
        y=df_sentiment[f'{crypto_to_plot}_sentiment'],
        marker_color=colors,  # Colores basados en el sentimiento
        name='Sentimiento'
    ))

    # Añadir una línea horizontal en 0 para referencia
    fig2.add_trace(go.Scatter(
        x=df_sentiment['Time'],
        y=[0]*len(df_sentiment),
        mode='lines',
        line=dict(color='black', width=1, dash='dash'),
        name='Neutral'
    ))

    # Configurar el layout
    fig2.update_layout(
        title=f"Evolución del Sentimiento del Mercado para {crypto_to_plot}",
        xaxis_title='Pasos de Tiempo',
        yaxis_title='Sentimiento',
        hovermode='x unified',
        template="plotly_white",  # Puedes cambiar a "plotly_dark" si prefieres
        xaxis=dict(showline=True, showgrid=False),
        yaxis=dict(showline=True, showgrid=True)
    )

    # Mostrar el gráfico en Streamlit
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown(f"""
    **Este gráfico de barras muestra cómo varió el sentimiento del mercado para {crypto_to_plot} durante la simulación. Un sentimiento positivo indica una percepción favorable (verde), mientras que uno negativo refleja una percepción desfavorable (rojo). El color gris indica un sentimiento neutral. La línea negra punteada en 0 sirve como referencia neutral.**
    """)

    # Distribución de Rendimiento de los Agentes
    st.header("Distribución de Rendimiento de los Agentes")

    rendimiento_total = st.session_state['rendimiento_total']

    if rendimiento_total.empty:
        st.warning("No hay rendimientos positivos para mostrar en el gráfico de pastel.")
    else:
        # Obtener las reglas de cada agente
        reglas_agentes = {agente.nombre: agente.reglas for agente in st.session_state['agentes'] if agente.nombre in rendimiento_total.index}

        # Crear hover text con las reglas
        hover_text = []
        for agente in rendimiento_total.index:
            reglas = reglas_agentes.get(agente, ["No hay reglas disponibles"])
            reglas_formateadas = '<br>'.join(reglas)
            hover_text.append(f"{agente}<br><br><b>Reglas:</b><br>{reglas_formateadas}")

        # Crear el gráfico de pastel
        fig_pastel = go.Figure(data=[go.Pie(
            labels=rendimiento_total.index,
            values=rendimiento_total.values,
            hovertext=hover_text,
            hoverinfo="text",
            textinfo='percent+label',
            textposition='inside',
            marker=dict(colors=px.colors.qualitative.Plotly)
        )])

        # Configurar el layout
        fig_pastel.update_layout(
            title="Distribución de Rendimiento de los Agentes",
        )

        # Mostrar el gráfico en Streamlit
        st.plotly_chart(fig_pastel, use_container_width=True)

        st.markdown("""
        **Este gráfico de pastel muestra la distribución del rendimiento total de los agentes. Al pasar el cursor sobre cada sección, se muestran las reglas que cada agente utilizó en su estrategia de trading.**
        """)

    # Rendimiento de los Agentes - Gráfico de Líneas
    st.subheader("Rendimiento de los Agentes")

    fig3 = go.Figure()

    # Definir colores para cada agente
    colors = px.colors.qualitative.Plotly  # Puedes elegir otro esquema de colores si lo prefieres

    for idx, agent in enumerate(st.session_state['df_resultados'].columns):
        fig3.add_trace(go.Scatter(
            x=st.session_state['df_resultados'].index,
            y=st.session_state['df_resultados'][agent],
            mode='lines+markers',
            name=agent,
            line=dict(color=colors[idx % len(colors)], width=2),
            marker=dict(size=6)
        ))

    # Configurar el layout
    fig3.update_layout(
        title="Rendimiento Acumulado de los Agentes",
        xaxis_title='Pasos de Tiempo',
        yaxis_title='Rendimiento (%)',
        hovermode='x unified',
        template="plotly_white",  # Puedes cambiar a "plotly_dark" si prefieres
        xaxis=dict(showline=True, showgrid=True),
        yaxis=dict(showline=True, showgrid=True)
    )

    # Mostrar el gráfico en Streamlit
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown("""
    **Este gráfico muestra el rendimiento acumulado de cada agente a lo largo de la simulación. Las líneas representan el crecimiento o decrecimiento de las estrategias de trading de cada agente, permitiendo una comparación visual de su efectividad.**
    """)

    # Mostrar Información del Mejor Agente con Toggle para Deseos y Creencias
    st.header("Mejor Agente de la Simulación")

    summary = st.session_state['summary']
    mejor_agente_nombre = st.session_state['mejor_agente']
    mejor_agente_data = summary['agent_performance'][mejor_agente_nombre]
    mejor_agente_reglas = mejor_agente_data.get('rules', "No disponible")

    st.write(f"**Nombre del Agente:** {mejor_agente_nombre}")
    st.write(f"**Rendimiento:** {mejor_agente_data['performance']:.2f}%")
    st.write(f"**Capital al culminar la simulación:** {mejor_agente_data['capital']:.2f} USD")
    st.write("**Estrategia:**")
    for regla in mejor_agente_reglas:
        st.write(f"- {regla}")

    st.write("**Portafolio:**")
    st.json(mejor_agente_data.get('portfolio', {}))

    # Botón para desplegar Deseos y Creencias
    if st.checkbox("Mostrar Deseos y Creencias del Mejor Agente"):
        st.subheader("Creencias del Mejor Agente")
        st.json(mejor_agente_data.get('beliefs', {}))

        st.subheader("Deseos del Mejor Agente al Culminar la Simulación")
        for deseo in mejor_agente_data.get('desires', []):
            accion, cripto = deseo
            st.write(f"- {accion} {cripto}")

        st.subheader("Historial de Intenciones del Mejor Agente")
        historial_intenciones = mejor_agente_data.get('intentions', [])
        for ciclo, intenciones in historial_intenciones:
            st.write(f"Ciclo {ciclo}:")
            for accion, cripto in intenciones:
                st.write(f"- {accion} {cripto}")

    # Exportar Resultados
    st.header("Exportación de Datos")
    st.markdown(get_table_download_link(st.session_state['df_resultados']), unsafe_allow_html=True)

    # Mostrar Logs de la Simulación (Opcional)
    # st.header("Logs de la Simulación")
    # st.text(log_stream.getvalue())


    # Mostrar Logs de la Simulación (Opcional)
    # st.header("Logs de la Simulación")
    # st.text(log_stream.getvalue())



    # # # **Análisis Estadístico para Historial de Precios**
    # # st.subheader("Análisis Estadístico de los Precios de las Criptomonedas")

    # # # Convertir price_history a DataFrame
    # # df_price_history = pd.DataFrame(simulation.price_history)

    # # # Calcular estadísticas descriptivas
    # # stats_precio = pd.DataFrame({
    # #     'Precio Promedio ($)': df_price_history.mean(),
    # #     'Precio Máximo ($)': df_price_history.max(),
    # #     'Precio Mínimo ($)': df_price_history.min(),
    # #     'Volatilidad (%)': df_price_history.std()
    # # })

    # # st.table(stats_precio)

    # # st.markdown("""
    # # **Preguntas Clave:**
    # # - ¿Cuál criptomoneda mostró la mayor volatilidad?
    # # - ¿Cuál criptomoneda alcanzó el precio más alto y el más bajo durante la simulación?
    # # - ¿Existe una tendencia clara de aumento o disminución en los precios de alguna criptomoneda?

    # # **Conclusiones:**
    # # - La criptomoneda con la mayor volatilidad fue **{max_volatility_crypto}**, lo que indica que sus precios fluctuaron más significativamente a lo largo de la simulación.
    # # - **{max_price_crypto}** alcanzó el precio máximo de ${max_price_value} y el precio mínimo de ${min_price_value}, mostrando una amplia gama de precios.
    # # - Observamos que **{trend_crypto}** presenta una tendencia **{trend_direction}**, lo que sugiere **{trend_conclusion}**.
    # # """.format(
    # #     max_volatility_crypto=stats_precio['Volatilidad (%)'].idxmax(),
    # #     max_price_crypto=stats_precio['Precio Máximo ($)'].idxmax(),
    # #     max_price_value=stats_precio['Precio Máximo ($)'].max(),
    # #     min_price_value=stats_precio['Precio Mínimo ($)'].min(),
    # #     trend_crypto="Bitcoin",  # Reemplaza con lógica si es necesario
    # #     trend_direction="alcista",  # Reemplaza con lógica si es necesario
    # #     trend_conclusion="una tendencia positiva en el precio"
    # # ))

    # # b. Historial de Sentimiento
    # # st.subheader("Historial de Sentimiento del Mercado")
    # # fig2 = px.line(
    # #     simulation.sentiment_history,
    # #     labels={"value": "Sentimiento", "index": "Pasos de Tiempo", "variable": "Criptomoneda"},
    # #     title="Evolución del Sentimiento del Mercado"
    # # )
    # # fig2.update_traces(mode='lines+markers')
    # # st.plotly_chart(fig2, use_container_width=True)
    # # st.markdown("""
    # # **Este gráfico muestra cómo varió el sentimiento del mercado para cada criptomoneda durante la simulación. Un sentimiento positivo indica una percepción favorable, mientras que uno negativo refleja lo contrario.**
    # # """)
    # # b. Historial de Sentimiento - Gráfico de Líneas con Colores Condicionales


    # # st.subheader("Historial de Sentimiento del Mercado")

    # # # Seleccionar la criptomoneda a visualizar
    # # crypto_to_plot = 'Bitcoin'  # Puedes hacerlo dinámico usando st.selectbox

    # # # Preparar los datos
    # # df_sentiment = simulation.sentiment_history_df.reset_index().rename(columns={'index': 'Time'})
    # # df_sentiment['Time'] = df_sentiment['Time']  # Asegúrate de que 'Time' esté correctamente formateado

    # # # Crear el gráfico de líneas con colores condicionales
    # # fig2 = go.Figure()

    # # # Definir colores basados en el sentimiento
    # # colors = df_sentiment[f'{crypto_to_plot}_sentiment'].apply(
    # #     lambda x: 'green' if x > 0 else ('red' if x < 0 else 'gray')
    # # )

    # # # Añadir la línea de sentimiento
    # # fig2.add_trace(go.Scatter(
    # #     x=df_sentiment['Time'],
    # #     y=df_sentiment[f'{crypto_to_plot}_sentiment'],
    # #     mode='lines+markers',
    # #     line=dict(color='blue', width=2),
    # #     marker=dict(color=colors),
    # #     name='Sentimiento'
    # # ))

    # # # Añadir una línea horizontal en 0 para referencia
    # # fig2.add_trace(go.Scatter(
    # #     x=df_sentiment['Time'],
    # #     y=[0]*len(df_sentiment),
    # #     mode='lines',
    # #     line=dict(color='black', width=1, dash='dash'),
    # #     name='Neutral'
    # # ))

    # # # Configurar el layout
    # # fig2.update_layout(
    # #     title=f"Evolución del Sentimiento del Mercado para {crypto_to_plot}",
    # #     xaxis_title='Tiempo',
    # #     yaxis_title='Sentimiento',
    # #     hovermode='x unified'
    # # )

    # # # Mejorar el diseño de las marcas y líneas
    # # fig2.update_traces(marker=dict(size=6))

    # # # Mostrar el gráfico en Streamlit
    # # st.plotly_chart(fig2, use_container_width=True)

    # # st.markdown("""
    # # **Este gráfico muestra cómo varió el sentimiento del mercado para {crypto} durante la simulación. Un sentimiento positivo indica una percepción favorable (verde), mientras que uno negativo refleja una percepción desfavorable (rojo). El color gris indica un sentimiento neutral. La línea negra punteada en 0 sirve como referencia neutral.**
    # # """.format(crypto=crypto_to_plot))

    # # # **Análisis Estadístico para Historial de Sentimiento**
    # # st.subheader("Análisis Estadístico del Sentimiento del Mercado")

    # # # Convertir sentiment_history a DataFrame
    # # df_sentiment_history = pd.DataFrame(simulation.sentiment_history)

    # # # Calcular estadísticas descriptivas
    # # stats_sentimiento = pd.DataFrame({
    # #     'Sentimiento Promedio': df_sentiment_history.mean(),
    # #     'Sentimiento Máximo': df_sentiment_history.max(),
    # #     'Sentimiento Mínimo': df_sentiment_history.min(),
    # #     'Desviación Estándar': df_sentiment_history.std()
    # # })

    # # st.table(stats_sentimiento)

    # # st.markdown("""
    # # **Preguntas Clave:**
    # # - ¿Cuál criptomoneda tuvo el sentimiento más positivo y el más negativo?
    # # - ¿Existe alguna correlación entre el sentimiento del mercado y los cambios de precio?
    # # - ¿Cómo varió la estabilidad del sentimiento a lo largo de la simulación?

    # # **Conclusiones:**
    # # - **{max_sentiment_crypto}** mostró el sentimiento promedio más positivo, lo que podría haber influido en **{impact_positive}**.
    # # - Se encontró una correlación de **{correlation_value}** entre el sentimiento del mercado y los cambios de precio, indicando que **{correlation_interpretation}**.
    # # - La estabilidad del sentimiento fue **{sentiment_stability}**, lo que sugiere que **{stability_conclusion}**.
    # # """.format(
    # #     max_sentiment_crypto=stats_sentimiento['Sentimiento Promedio'].idxmax(),
    # #     impact_positive="un aumento en el precio de {0}".format(stats_precio['Precio Promedio ($)'].idxmax()),
    # #     correlation_value="0.5",  # Reemplaza con el valor real si calculas la correlación
    # #     correlation_interpretation="un efecto moderado de los sentimientos en los precios",
    # #     sentiment_stability="alta" if stats_sentimiento['Desviación Estándar'].mean() < 0.5 else "baja",
    # #     stability_conclusion="una variabilidad significativa en el sentimiento"
    # # ))

    # # c. Rendimiento de los Agentes
    # # st.subheader("Rendimiento de los Agentes")
    # # fig3 = px.line(
    # #     df_resultados,
    # #     labels={"value": "Rendimiento (%)", "index": "Pasos de Tiempo", "variable": "Agente"},
    # #     title="Rendimiento Acumulado de los Agentes"
    # # )
    # # fig3.update_traces(mode='lines+markers')
    # # st.plotly_chart(fig3, use_container_width=True)
    # # st.markdown("""
    # # **Este gráfico muestra el rendimiento acumulado de cada agente a lo largo de la simulación. Permite comparar qué agentes han sido más exitosos en sus estrategias de trading.**
    # # """)

    # # # **Análisis Estadístico para Rendimiento de los Agentes**
    # # st.subheader("Análisis Estadístico del Rendimiento de los Agentes")

    # # # Calcular estadísticas descriptivas
    # # stats_rendimiento = pd.DataFrame({
    # #     'Rendimiento Promedio (%)': df_resultados.mean(),
    # #     'Rendimiento Máximo (%)': df_resultados.max(),
    # #     'Rendimiento Mínimo (%)': df_resultados.min(),
    # #     'Desviación Estándar (%)': df_resultados.std()
    # # })

    # # st.table(stats_rendimiento)

    # # st.markdown("""
    # # **Preguntas Clave:**
    # # - ¿Qué agente tuvo el mejor rendimiento promedio?
    # # - ¿Cuál fue la variabilidad en el rendimiento de cada agente?
    # # - ¿Existen agentes que consistentemente superaron o quedaron por debajo del promedio?

    # # **Conclusiones:**
    # # - El agente con el mejor rendimiento promedio fue **{best_agent}**, lo que indica que su estrategia fue más efectiva.
    # # - Algunos agentes mostraron una alta variabilidad en su rendimiento, lo que sugiere **{high_variability}**.
    # # - La consistencia en el rendimiento de **{consistent_agent}** indica que **{consistency_conclusion}**.
    # # """.format(
    # #     best_agent=stats_rendimiento['Rendimiento Promedio (%)'].idxmax(),
    # #     high_variability="una estrategia inestable o adaptable",
    # #     consistent_agent=stats_rendimiento['Desviación Estándar (%)'].idxmin(),
    # #     consistency_conclusion="una estrategia robusta y predecible"
    # # ))

    # # d. Distribución de Ganancias
    # # st.subheader("Distribución de Ganancias de los Agentes")
    # # fig4 = px.histogram(
    # #     df_resultados,
    # #     nbins=20,
    # #     title="Distribución de Ganancias por Agente",
    # #     labels={"value": "Ganancia (%)", "variable": "Agente"},
    # #     histnorm='probability density'
    # # )
    # # fig4.update_traces(opacity=0.6)
    # # st.plotly_chart(fig4, use_container_width=True)
    # # st.markdown("""
    # # **Este histograma muestra la distribución de las ganancias obtenidas por cada agente durante la simulación. Permite visualizar la frecuencia de diferentes niveles de ganancia y evaluar la consistencia de las estrategias.**
    # # """)

    # # # # **Análisis Estadístico para Distribución de Ganancias**
    # # st.subheader("Análisis Estadístico de la Distribución de Ganancias")

    # # # Calcular estadísticas descriptivas
    # # stats_ganancias = pd.DataFrame({
    # #     'Ganancia Promedio (%)': df_resultados.mean(),
    # #     'Ganancia Mediana (%)': df_resultados.median(),
    # #     'Ganancia Máxima (%)': df_resultados.max(),
    # #     'Ganancia Mínima (%)': df_resultados.min(),
    # #     'Desviación Estándar (%)': df_resultados.std(),
    # #     'Skewness': df_resultados.skew()
    # # })

    # # st.table(stats_ganancias)

    # # st.markdown("""
    # # **Preguntas Clave:**
    # # - ¿Cuál es la ganancia promedio y mediana de los agentes?
    # # - ¿Existe asimetría en la distribución de ganancias de los agentes?
    # # - ¿Qué agentes tienen ganancias significativamente superiores o inferiores al promedio?

    # # **Conclusiones:**
    # # - La ganancia promedio de los agentes fue de **{avg_gain}%**, mientras que la mediana fue de **{median_gain}%**, indicando que **{avg_median_interpretation}**.
    # # - La distribución muestra una **{skewness_direction}** asimetría, lo que sugiere que **{skewness_conclusion}**.
    # # - Algunos agentes, como **{top_agents}**, lograron ganancias significativamente superiores, lo que podría atribuirse a **{top_agents_conclusion}**.
    # # """.format(
    # #     avg_gain=stats_ganancias['Ganancia Promedio (%)'].mean().round(2),
    # #     median_gain=stats_ganancias['Ganancia Mediana (%)'].median().round(2),
    # #     avg_median_interpretation="la mayoría de los agentes están cerca de la media",
    # #     skewness_direction="positiva" if stats_ganancias['Skewness'].mean() > 0 else "negativa",
    # #     skewness_conclusion="hay una tendencia hacia mayores ganancias",
    # #     top_agents=', '.join(stats_ganancias['Ganancia Promedio (%)'].nlargest(2).index),
    # #     top_agents_conclusion="su combinación de reglas les permitió adaptarse mejor al mercado"
    # # ))


    # st.header("Distribución de Rendimiento de los Agentes")

    # if rendimiento_total.empty:
    #     st.warning("No hay rendimientos positivos para mostrar en el gráfico de pastel.")
    # else:
    #     # Obtener las reglas de cada agente
    #     reglas_agentes = {agente.nombre: agente.reglas for agente in simulation.agents if agente.nombre in rendimiento_total.index}

    #     # Crear hover text con las reglas
    #     hover_text = []
    #     for agente in rendimiento_total.index:
    #         reglas = reglas_agentes.get(agente, ["No hay reglas disponibles"])
    #         reglas_formateadas = '<br>'.join(reglas)
    #         hover_text.append(f"{agente}<br><br><b>Reglas:</b><br>{reglas_formateadas}")

    #     # Crear el gráfico de pastel
    #     fig_pastel = go.Figure(data=[go.Pie(
    #         labels=rendimiento_total.index,
    #         values=rendimiento_total.values,
    #         hovertext=hover_text,
    #         hoverinfo="text",
    #         textinfo='percent+label',
    #         textposition='inside',
    #         marker=dict(colors=px.colors.qualitative.Plotly)
    #     )])

    #     # Configurar el layout
    #     fig_pastel.update_layout(
    #         title="Distribución de Rendimiento de los Agentes",
    #     )

    #     # Mostrar el gráfico en Streamlit
    #     st.plotly_chart(fig_pastel, use_container_width=True)

    #     st.markdown("""
    #     **Este gráfico de pastel muestra la distribución del rendimiento total de los agentes. Al pasar el cursor sobre cada sección, se muestran las reglas que cada agente utilizó en su estrategia de trading.**
    #     """)
    # # *** Gráficas de Pastel sin Filtrado ***
    # # st.header("Distribución de Rendimiento de los Agentes")

    # # if rendimiento_total.empty:
    # #     st.warning("No hay rendimientos positivos para mostrar en el gráfico de pastel.")
    # # else:
    # #     # Crear gráfica de pastel con las reglas en hover
    # #     # Obtener las reglas de cada agente
    # #     reglas_agentes = {agente.nombre: agente.reglas for agente in simulation.agents if agente.nombre in rendimiento_total.index}

    # #     hover_text = [f"{agente}<br>{'<br>'.join(reglas_agentes.get(agente, []))}" for agente in rendimiento_total.index]

    # #     fig_pastel = px.pie(
    # #         names=rendimiento_total.index,
    # #         values=rendimiento_total.values,
    # #         title="Distribución de Rendimiento de los Agentes",
    # #         hover_data={'Reglas': hover_text},
    # #         labels={"Reglas": "Reglas de la Estrategia"}
    # #     )
    # #     fig_pastel.update_traces(textposition='inside', textinfo='percent+label')
    # #     st.plotly_chart(fig_pastel, use_container_width=True)
    # #     st.markdown("""
    # #     **Este gráfico de pastel muestra la distribución del rendimiento total de los agentes. Al pasar el cursor sobre cada sección, se muestran las reglas que cada agente utilizó en su estrategia de trading.**
    # #     """)
    # # c. Rendimiento de los Agentes - Gráfico de Líneas con Colores Personalizados


    # st.subheader("Rendimiento de los Agentes")

    # # Crear el gráfico de líneas
    # fig3 = go.Figure()

    # # Definir colores para cada agente
    # colors = px.colors.qualitative.Plotly  # Puedes elegir otro esquema de colores si lo prefieres

    # for idx, agent in enumerate(df_resultados.columns):
    #     fig3.add_trace(go.Scatter(
    #         x=df_resultados.index,
    #         y=df_resultados[agent],
    #         mode='lines+markers',
    #         name=agent,
    #         line=dict(color=colors[idx % len(colors)], width=2),
    #         marker=dict(size=6)
    #     ))

    # # Configurar el layout
    # fig3.update_layout(
    #     title="Rendimiento Acumulado de los Agentes",
    #     xaxis_title='Pasos de Tiempo',
    #     yaxis_title='Rendimiento (%)',
    #     hovermode='x unified'
    # )

    # # Mostrar el gráfico en Streamlit
    # st.plotly_chart(fig3, use_container_width=True)

    # st.markdown("""
    # **Este gráfico muestra el rendimiento acumulado de cada agente a lo largo de la simulación. Las líneas representan el crecimiento o decrecimiento de las estrategias de trading de cada agente, permitiendo una comparación visual de su efectividad.**
    # """)

    #     # # **Análisis Estadístico para Distribución de Rendimiento de los Agentes**
    #     # st.subheader("Análisis Estadístico de la Distribución de Rendimiento de los Agentes")
    #     # porcentaje_rendimiento = rendimiento_total / rendimiento_total.sum() * 100
    #     # stats_pastel = pd.DataFrame({
    #     #     'Porcentaje de Rendimiento (%)': porcentaje_rendimiento
    #     # })
    #     # st.table(stats_pastel)

    #     # st.markdown("""
    #     # **Preguntas Clave:**
    #     # - ¿Qué agentes contribuyeron más significativamente al rendimiento total?
    #     # - ¿Existe una concentración del rendimiento en unos pocos agentes o está distribuido de manera equitativa?
    #     # - ¿Cómo se comparan las reglas de los agentes de mayor rendimiento con las de menor rendimiento?

    #     # **Conclusiones:**
    #     # - Los agentes como **{top_contributors}** aportaron el **{top_percentage}%** del rendimiento total, indicando que su estrategia fue altamente efectiva.
    #     # - Observamos que el rendimiento está **{distribution}**, lo que sugiere que **{distribution_conclusion}**.
    #     # - Las reglas utilizadas por los agentes de mayor rendimiento incluyen **{top_rules}**, las cuales parecen ser **{top_rules_interpretation}** en el contexto actual del mercado.
    #     # """.format(
    #     #     top_contributors=', '.join(stats_pastel['Porcentaje de Rendimiento (%)'].nlargest(2).index),
    #     #     top_percentage=stats_pastel['Porcentaje de Rendimiento (%)'].nlargest(2).values.round(2),
    #     #     distribution="concentrado" if porcentaje_rendimiento.max() > 50 else "distribuido de manera equitativa",
    #     #     distribution_conclusion="algunos agentes dominan el rendimiento total",
    #     #     top_rules=', '.join(reglas_agentes.get(stats_pastel['Porcentaje de Rendimiento (%)'].nlargest(2).index[0], [])),
    #     #     top_rules_interpretation="especialmente efectivas"
    #     # ))

    # # *** Identificar y Mostrar el Mejor Agente y su Estrategia ***
    # # Obtener el mejor agente y sus reglas
    # summary = simulation.get_summary()
    # mejor_agente_nombre = simulation.get_performance()
    # mejor_agente_data = summary['agent_performance'][mejor_agente_nombre]
    # mejor_agente_reglas = mejor_agente_data.get('rules', "No disponible")

    # # Mostrar el mejor agente y su estrategia de forma no HTML, usando Streamlit components
    # st.header("Mejor Agente de la Simulación")
    # st.write(f"**Nombre del Agente:** {mejor_agente_nombre}")
    # st.write(f"**Rendimiento:** {mejor_agente_data['performance']:.2f}%")
    # st.write(f"**Capital al culminar la simulación:** {mejor_agente_data['capital']:.2f} USD")
    # st.write("**Estrategia:**")
    # for regla in mejor_agente_reglas:
    #     st.write(f"- {regla}")

    # st.write("**Portafolio:**")
    # st.json(mejor_agente_data.get('portfolio', {}))


    # # Mostrar las creencias (beliefs) del mejor agente
    # st.write("**Creencias del Mejor Agente:**")
    # st.json(mejor_agente_data.get('beliefs', {}))

    # # Mostrar todas las intenciones con su ciclo de acción
    # st.write("**Historial de Intenciones del Mejor Agente:**")
    # historial_intenciones = mejor_agente_data.get('intentions', [])
    # for ciclo, intenciones in historial_intenciones:
    #     st.write(f"Ciclo {ciclo}:")
    #     for accion, cripto in intenciones:
    #         st.write(f"- {accion} {cripto}")

    # # Si deseas mostrar los deseos actuales
    # st.write("**Deseos del Mejor Agente al culminar la simulación:**")
    # for deseo in mejor_agente_data.get('desires', []):
    #     accion, cripto = deseo
    #     st.write(f"- {accion} {cripto}")


    # # # **Análisis Estadístico del Mejor Agente**
    # # st.subheader("Análisis del Mejor Agente")
    # # st.write(f"**Nombre:** {mejor_agente_nombre}")
    # # st.write(f"**Rendimiento Total:** {mejor_agente_data['performance']:.2f}%")
    # # st.write("**Reglas de la Estrategia:**")
    # # for regla in mejor_agente_reglas:
    # #     st.write(f"- {regla}")

    # # st.markdown("""
    # # **Preguntas Clave:**
    # # - ¿Qué hizo que este agente fuera el mejor en términos de rendimiento?
    # # - ¿Cómo se alinean las reglas de este agente con los patrones de mercado observados?
    # # - ¿Podría replicarse esta estrategia en diferentes contextos de mercado?

    # # **Conclusiones:**
    # # - El agente **{best_agent}** logró el mejor rendimiento gracias a **{performance_factors}**.
    # # - Las reglas utilizadas por este agente, como **{best_rules}**, fueron especialmente efectivas en el contexto del mercado simulado.
    # # - Esta estrategia podría ser **{replicable}** en diferentes escenarios de mercado debido a **{replicable_reason}**.
    # # """.format(
    # #     best_agent=mejor_agente_nombre,
    # #     performance_factors="su capacidad para adaptarse rápidamente a las fluctuaciones del mercado",
    # #     best_rules=', '.join(mejor_agente_reglas),
    # #     replicable="replicable" if True else "no replicable",  # Reemplaza con lógica si es necesario
    # #     replicable_reason="su estrategia está basada en principios fundamentales que son consistentes en diversos entornos de mercado"
    # # ))

    # # Exportar Resultados
    # st.header("Exportación de Datos")
    # st.markdown(get_table_download_link(df_resultados), unsafe_allow_html=True)

    # # *** Eliminado la sección de Logs de la Simulación ***
