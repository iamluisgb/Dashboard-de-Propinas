import faicons as fa
import pandas as pd
import plotly.express as px

# Cargar datos y computar valores estáticos
from shared import app_dir, tips
from shiny import reactive, render
from shiny.express import input, ui
from shinywidgets import render_plotly

# Calcular el rango de valores de facturas para el control deslizante
bill_rng = (min(tips.total_bill), max(tips.total_bill))

# Añadir título de página y opciones - Configura fillable=True para aprovechar mejor el espacio
ui.page_opts(title='Propinas Restaurante', fillable=True)

# Crear la barra lateral con controles de filtrado
with ui.sidebar(open='desktop'):
    ui.input_slider(
        'total_bill',
        'Bill amount',
        min=bill_rng[0],
        max=bill_rng[1],
        value=bill_rng,
        post=' €',
    )
    ui.input_checkbox_group(
        'time',
        'Food service',
        ['Lunch', 'Dinner'],
        selected=['Lunch', 'Dinner'],
        inline=True,
    )
    ui.input_selectize(
        "day",                           # ID del input
        "Day of the week",               # Etiqueta para el usuario
        ["Thur", "Fri", "Sat", "Sun"],   # Opciones disponibles
        selected=["Thur", "Fri", "Sat", "Sun"], # Selección inicial
        multiple=True                    # Permitir selección múltiple
    )

    ui.input_action_button('reset', 'Reset filter')

# Definir iconos para la interfaz
ICONS = {
    'user': fa.icon_svg('user', 'regular'),
    'wallet': fa.icon_svg('wallet'),
    'currency-euro': fa.icon_svg('euro-sign'),
    'ellipsis':fa.icon_svg('ellipsis'),
    'users': fa.icon_svg('users'), 
}

# Crear fila de cajas de valores - usando col_widths=[3,3,3,3] para distribuir mejor
with ui.layout_columns(col_widths=[3,3,3,3], fill=False):
    with ui.value_box(showcase=ICONS['user']):
        "Total de Propinas"

        @render.express
        def total_tippers():
            tips_data().shape[0]

    
    with ui.value_box(showcase=ICONS["users"]):
        "Tamaño medio del grupo"

        @render.express
        def average_group_size():
            d = tips_data()
            if d.shape[0] > 0:
                avg_size = d["size"].mean()
                f"{avg_size:.1f} Personas"

    with ui.value_box(showcase=ICONS['wallet']):
        "Propina Media"

        @render.express
        def average_tip():
            d = tips_data()
            if d.shape[0] > 0:
                perc = d.tip / d.total_bill
                f"{perc.mean():.1%}" 

    
    with ui.value_box(showcase=ICONS['currency-euro']):
        "Factura Media"

        @render.express
        def average_bill():
            d = tips_data()
            if d.shape[0] > 0:
                bill = d.total_bill.mean()
                f"{bill:.2f}€" 


# Tabla y gráfico de dispersión en la primera fila
with ui.layout_columns(col_widths=[6, 6]):
    with ui.card(full_screen=True, height="400px"):  
        ui.card_header('Tabla de propinas')

        @render.data_frame
        def table():
            return render.DataGrid(tips_data())
        
    # Segunda tarjeta: Gráfico de dispersión
    with ui.card(full_screen=True, height="400px"):  
        with ui.card_header(class_="d-flex justify-content-between align-items-center"):
            "Total Factura vs Propina"
            # Menú emergente para opciones de color
            with ui.popover(title='Opciones de visualización', placement="top"):
                ICONS["ellipsis"]

                ui.input_radio_buttons(
                    "scatter_color",
                    "Color de puntos:",
                    ["none", "sex", "smoker", "day", "time"],
                    inline=True,
                )
                # Opción para tamaño
                ui.input_checkbox(
                    "show_size",
                    "Mostrar tamaño del grupo con tamaño de punto",
                    value=False
                )

        # Renderizar el gráfico de dispersión
        @render_plotly
        def scatterplot():
            color = input.scatter_color()
            use_size = input.show_size()

            fig = px.scatter(
                tips_data(),
                x="total_bill",
                y="tip",
                color=None if color == "none" else color,
                size="size" if use_size else None,  # Usar size condicionalmente
                trendline="lowess",  # Añadir línea de tendencia
            )
            
            # Ajustar el tamaño del gráfico para que ocupe todo el espacio disponible
            fig.update_layout(
                autosize=True,
                margin=dict(l=50, r=30, t=30, b=50)
            )
            
            return fig

# Segunda fila con los dos gráficos restantes
with ui.layout_columns(col_widths=[6, 6]):
    # Gráfico de densidad (ridgeplot)
    with ui.card(full_screen=True, height="400px"):  # Establecer altura fija
        with ui.card_header(class_="d-flex justify-content-between align-items-center"):
            'Porcentajes de propinas'
            with ui.popover(title='Opciones de visualización'):
                ICONS['ellipsis']
                ui.input_radio_buttons(
                    'tip_perc_y',
                    'Partir por:',
                    ["sex", "smoker", "day", "time"],
                    selected='day',
                    inline=False,
                )
        @render_plotly
        def tip_perc():
            from ridgeplot import ridgeplot

            dat = tips_data()
            dat['percent'] = dat.tip / dat.total_bill
            yvar = input.tip_perc_y()
            uvals = dat[yvar].unique()

            samples = [[dat.percent[dat[yvar] == val]] for val in uvals]

            plt = ridgeplot(
                samples=samples,
                labels=uvals,
                bandwidth=0.01,
                colorscale='viridis',
                colormode='row-index',
            )

            plt.update_layout(
                legend=dict(
                    orientation='h', yanchor='bottom', xanchor='center', x=0.5
                ),
                autosize=True,
                margin=dict(l=50, r=30, t=30, b=50)
            )

            return plt
    
    # Gráfico de barras por día de la semana
    with ui.card(full_screen=True, height="400px"):
        with ui.card_header(class_="d-flex justify-content-between align-items-center"):
            "Propinas por día de la semana"
            with ui.popover(title='Opciones de visualiación'):
                ICONS["ellipsis"]
                ui.input_radio_buttons(
                    'bar_metric',
                    'Métrica:',
                    ['Total propinas', 'Propina media', 'Porcentaje medio de propina'],
                    selected='Total propinas'
                )
                ui.input_checkbox(
                    'show_day_count',
                    "Muestra el número de visitas por día",
                    value=True
                )

        @render_plotly
        def tips_by_day():
            data = tips_data()
            
            if data.shape[0] == 0:
                return px.bar(title='No hay datos para mostrar con los filtros actuales')
            
            metric = input.bar_metric()

            if metric == 'Total propinas':
                day_tips = data.groupby('day')['tip'].sum().reset_index()
                y_title = 'Total propinas (€)'

            elif metric == 'Propina media':
                day_tips = data.groupby('day')['tip'].mean().reset_index()
                y_title = "Propina media (€)"                    

            else: #Porcentaje medio de propina
                data['percent'] = data.tip / data.total_bill * 100
                day_tips = data.groupby('day')['percent'].mean().reset_index()
                y_title = 'Porcentaje de propina medio (%)'
            
            # Renombrar columnas
            day_tips.columns = ['day', 'value']

            # Ordenar los días correctamente
            day_order = ['Thur', 'Fri', 'Sat', 'Sun']
            day_tips['day'] = pd.Categorical(day_tips['day'], categories=day_order, ordered=True)
            day_tips = day_tips.sort_values('day')

            # Configuración base para la gráfica
            fig_params = {
                'x': 'day',
                'y': 'value',
                'color': 'day',
                'labels': {'vañue': y_title, 'day': 'Día de la semana'},
                'title': f'{metric} por día de la semana'
            }

            # Mostrar conteo de visitas si está activado
            if input.show_day_count():
                day_count = data.groupby('day').size().reset_index()
                day_count.columns = ['day', 'count']
                day_count['day'] = pd.Categorical(day_count['day'], categories=day_order, ordered=True)
                day_count = day_count.sort_values('day')

                fig_params['custom_data'] = [day_count['count']]

                hover_template = "<b>%{x}</b><br>" + \
                            f"{y_title}: %{{y:.2f}}<br>" + \
                            "Número de visitas: %{customdata}<br>"
                fig = px.bar(day_tips, **fig_params)
                fig.update_traces(hovertemplate=hover_template)
            else:
                fig = px.bar(day_tips, **fig_params)

            fig.update_layout(
                showlegend=False,
                autosize=True,
                margin=dict(l=50, r=30, t=30, b=50)
            )

            return fig



                
            
        

# Añadir estilos CSS personalizados
ui.include_css(app_dir / "styles.css")


# --------------------------------------------------------
# Cálculos reactivos y efectos
# --------------------------------------------------------

# Función reactiva para filtrar datos según entradas del usuario
@reactive.calc
def tips_data():
    bill = input.total_bill()
    idx1 = tips.total_bill.between(bill[0], bill[1])
    idx2 = tips.time.isin(input.time())
    idx3 = tips.day.isin(input.day()) 
    return tips[idx1 & idx2 & idx3]

# Efecto reactivo para restablecer filtros cuando se hace clic en el botón
@reactive.effect
@reactive.event(input.reset)
def _():
    ui.update_slider('total_bill', value=bill_rng)
    ui.update_checkbox_group('time', selected=['Lunch', "Dinner"])
    ui.update_select("day", selected=["Thur", "Fri", "Sat", "Sun"])