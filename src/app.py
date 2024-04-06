import dash
import dash_html_components as html
import dash_core_components as dcc
import dash_vega_components as dvc
from dash.dependencies import Input, Output
import altair as alt
import dash_bootstrap_components as dbc
import pandas as pd
import dash_mantine_components as dmc
from dash import dash_table


# Read in data
data = pd.read_csv("data/raw/world_air_quality.csv", delimiter=';')
data = data.rename(columns={'Last Updated': 'time', 
                     'Country Label': 'countryname',
                     'Value': 'value',
                     'Pollutant': 'pollutant'})
data['time'] = pd.to_datetime(data['time']).dt.date

# Setup app and layout/frontend
app = dash.Dash(
    __name__, title="Air Quality Tracker", external_stylesheets=['https://bootswatch.com/4/lux/bootstrap.css']
)
server = app.server

app.layout = html.Div([
    dbc.Row(html.H1('Pollutant Tracker')),
    dbc.Row([
        dbc.Col([
            # Filters column
            html.Div([
                html.Label('Select type of pollutant shown on the dashboard'),
                dcc.RadioItems(
                    id='pollutant_type_filter',
                    options=[{'label': i, 'value': i} for i in ['PM2.5', 'SO2', 'NO', 'CO', 'NOX', 'NO2', 'PM1', 'PM10']],
                    value='PM2.5',  
                    labelStyle={'display': 'inline-block', 'margin-right': '20px'}  
                ),
                html.Label('Select region(s)'),
                dcc.Dropdown(
                    id='region_filter',
                    options=[{"label": region, "value": region} for region in ['Africa', 'Antarctica', 'Asia', 'Europe', 'North America', 'Oceania', 'South America']],
                    value=['Asia'],  # default selected value
                    multi=True
                ),
                html.Label('Select country'),
                dcc.Dropdown(
                    id='country_filter',
                    options=[{"label": country, "value": country} for country in data['countryname']],
                    value='Japan',  # default selected value
                ),
                html.Label('Select time period'),
                dmc.DateRangePicker(
                    id="date_range_picker",
                    minDate=min(data['time']),
                    maxDate=max(data['time']),
                    value=[min(data['time']), max(data['time'])],
                    style={"width": "100%"},
                )
            ], style={'margin-right': '20px'})
        ], width=3),  # Filters column width
        dbc.Col([
            # Main content column
            html.Label('Pollution Tracker'),
            dcc.Graph(id='pollution_map', figure={}),  # Placeholder for the pollution map
            dbc.Row([
                dbc.Col([
                    html.H3('Top 15 Countries of Pollutant'),
                    dvc.Vega(id='top_countries_chart', spec={}, style={'width': '100%', 'height': '100%'})
                ], md=4),
                dbc.Col([
                    html.H3('Trend of Pollutant over time'),
                    dvc.Vega(id='trend_chart', spec={}, style={'width': '100%', 'height': '100%'})
                ], md=5),
                dbc.Col(
                    html.Div([
                        html.H3('Data Summary'),
                        dash_table.DataTable(
                            id='data-summary-table',
                            style_cell={'textAlign': 'center'},
                            style_header={
                                'backgroundColor': 'white',
                                'fontWeight': 'bold'
                            },
                        )
                    ], style={'width': '80%'}),
                md=3),
            ]),
        ], width=9)  # Main content column width
    ])
])




# Set up callbacks/backend
@app.callback(
    Output("world_map", "srcDoc"),
    Input("pollutant", "value"),
    Input("region", "value"),
    Input("Country Label", "value"),
    Input("year", "value"),
)
def plot_map():
    return map


@app.callback(
    Output("top_countries_chart", "spec"),
    Input("pollutant_type_filter", "value"),
    #Input("region_filter", "value"),
    #Input("country_filter", "value"),
    Input("date_range_picker", "value"),
)
def plot_bar(pollutant, time_range):
    start_date, end_date = time_range
    start_date = pd.to_datetime(start_date).date()
    end_date = pd.to_datetime(end_date).date()
    #if not isinstance(countries, list):
    #    countries = [countries]

    filtered_data = data[
        (data['time'] >= start_date) &
        (data['time'] <= end_date) &
        #(pollutant['region'].isin(regions)) &
    #    (data['countryname'].isin(countries)) &
        (data['pollutant'] == pollutant)
    ]
    top_countries_data = filtered_data.groupby('countryname', as_index=False)['value'].mean().sort_values(by='value', ascending=False).head(15)
    bar = alt.Chart(top_countries_data).mark_bar(fill='black').encode(
        x=alt.X('value:Q', title='Average AQI Value'),
        y=alt.Y('countryname:N',  title='Country').sort('-x'),
        tooltip=[
        alt.Tooltip('countryname:N', title='Country'),
        alt.Tooltip('value:Q', title='AQI value')
        ]
    ).properties(
        title='Top 15 Countries by AQI Value',
        width=250,
        height=300
    ).to_dict()
    return bar


@app.callback(
    Output("trend_chart", "spec"),
    Input("pollutant_type_filter", "value"),
    #Input("region_filter", "value"),
    Input("country_filter", "value"),
    Input("date_range_picker", "value"),
)
def plot_line(pollutant, countries, time_range):
    start_date, end_date = time_range
    start_date = pd.to_datetime(start_date).date()
    end_date = pd.to_datetime(end_date).date()
    #if not isinstance(countries, list):
    #    countries = [countries]
    
    filtered_data = data[
        (data['time'] >= start_date) &
        (data['time'] <= end_date) &
        #(pollutant['region'].isin(regions)) &
        (data['countryname']== countries) &
        (data['pollutant'] == pollutant)
    ]
    filtered_data['time'] = filtered_data['time'].astype(str)
    line = alt.Chart(filtered_data).mark_line(color='black').encode(
        x=alt.X('time:T', axis=alt.Axis(title='Date', format='%Y-%m')), 
        y=alt.Y('value:Q', axis=alt.Axis(title='Value')),  
        #color=alt.Color('countryname:N', legend=alt.Legend(title='Country')),
        tooltip=[
        alt.Tooltip('time:T', title='Date', format='%Y-%m-%d'),
        alt.Tooltip('value:Q', title='AQI value'),
        alt.Tooltip('countryname:N', title='Country')
        ]
        ).properties(
            title='Air Quality Index (AQI) Over Time',
            width=400,
            height=300
        ).to_dict()
    return line

@app.callback(
    Output('data-summary-table', 'columns'),
    Output('data-summary-table', 'data'),
    Input("pollutant_type_filter", "value"),
    #Input("region_filter", "value"),
    Input("country_filter", "value"),
    Input("date_range_picker", "value"),
)
def summary(pollutant, countries, time_range):
    start_date, end_date = time_range
    start_date = pd.to_datetime(start_date).date()
    end_date = pd.to_datetime(end_date).date()
    #if not isinstance(countries, list):
    #    countries = [countries]
    
    filtered_data = data[
        (data['time'] >= start_date) &
        (data['time'] <= end_date) &
        #(pollutant['region'].isin(regions)) &
        (data['countryname'] == countries) &
        (data['pollutant'] == pollutant)
    ]
    summary = filtered_data.describe().reset_index()
    summary.rename(columns={'index': 'Statistic'}, inplace=True)

    columns = [{"name": i, "id": i} for i in summary.columns]
    summary_data = summary.to_dict('records')

    return columns, summary_data


if __name__ == '__main__':
    app.run_server(debug=True)
