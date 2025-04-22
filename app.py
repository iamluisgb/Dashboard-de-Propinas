import faicons as fa
import plotly.express as px

# Cargar datos y computar valores estáticos
from shared import app_dir, tips
from shiny import reactive, render
from shiny.express import input, ui
from shinywidgets import render_plotly

# Calcular el rango de valores de facturas para el control deslizante
bill_rng = (min(tips.total_bill), max(tips.total_bill))

# Añadir título de página y opciones
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
}

# Crear fila de cajas de valores
with ui.layout_columns(fill=False):
    with ui.value_box(showcase=ICONS['user']):
        "Total de Propinas"

        @render.express
        def total_tippers():
            tips_data().shape[0]

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

# Crear diseño principal con tres tarjetas
with ui.layout_columns(col_widths=[6, 6, 12]):
    with ui.card(full_screen=True):
        ui.card_header('Tabla de propinas')

        @render.data_frame
        def table():
            return render.DataGrid(tips_data())
        
    # Segunda tarjeta: Gráfico de dispersión
    with ui.card(full_screen=True):
        with ui.card_header(class_="d-flex justify-content-between align-items-center"):
            "Total Factura vs Propina"
            # Menú emergente para opciones de color
            with ui.popover(title='Añade color a la variable', placement="top"):
                ICONS["ellipsis"]
                ui.input_radio_buttons(
                    "scatter_color",
                    None,
                    ["none", "sex", "smoker", "day", "time"],
                    inline=True,
                )

        # Renderizar el gráfico de dispersión
        @render_plotly
        def scatterplot():
            color = input.scatter_color()
            return px.scatter(
                tips_data(),
                x="total_bill",
                y="tip",
                color=None if color == "none" else color,
                trendline="lowess",  # Añadir línea de tendencia
            )

    # Tercera tarjeta: Gráfico de densidad (ridgeplot)
    with ui.card(full_screen=True):
        with ui.card_header(class_="d-flex justify-content-between align-items-center"):
            'Porcentajes de propinas'
            with ui.popover(title='Añade un color a la variable'):
                ICONS['ellipsis']
                ui.input_radio_buttons(
                    'tip_perc_y',
                    'Partir por:',
                    ["sex", "smoker", "day", "time"],
                    selected='day',
                    inline=True,
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
                )
            )

            return plt

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
