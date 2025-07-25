import dash
from dash import html, dcc
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd

# 1. Initialize the Dash app (and underlying Flask server)
app = dash.Dash(__name__)

# 2. Define the layout using Python objects that map to React components
df = pd.DataFrame({
    "Fruit": ["Apples", "Oranges", "Bananas", "Apples", "Oranges", "Bananas"],
    "Amount": [4, 1, 2, 2, 4, 5],
    "City": ["SF", "SF", "SF", "Montreal", "Montreal", "Montreal"]
})

app.layout = html.Div([
    dcc.Dropdown(
        id='city-dropdown',
        options=[{"label": c, "value": c} for c in df["City"].unique()],
        value='SF'
    ),
    dcc.Graph(id='bar-chart')
])

# 3. Define callbacks to make the app interactive
@app.callback(
    Output('bar-chart', 'figure'),         # what to update
    Input('city-dropdown', 'value')        # what triggers it
)
def update_chart(selected_city):
    filtered = df[df["City"] == selected_city]
    fig = px.bar(filtered, x="Fruit", y="Amount",
                 title=f"Fruit Amounts in {selected_city}")
    return fig

# 4. Run the server
if __name__ == '__main__':
    app.run(debug=True)
