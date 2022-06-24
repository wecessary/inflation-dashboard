import requests
import pandas as pd
from dash import Dash, html, dcc, Input, Output
import plotly.express as px
import plotly.graph_objects as go
import datetime

now = datetime.datetime.now()
now = now.strftime("%d %b %Y")

# ------- Getting data from ONS API-------- #

# ONS API for CPIH
# CPIH is the most comprehensive measure of inflation.
# It extends CPI to include a measure of the costs associated with owning, maintaining and living in one's own home,
# known as owner occupiers' housing costs (OOH), along with council tax
# This endpoint returns all the versions released on CPIH
API_URL = "https://api.beta.ons.gov.uk/v1/datasets/cpih01/editions/time-series/versions"

response = requests.get(API_URL)
response_json = response.json()

# this takes the latest version of the data from the API
csv_url = response_json["items"][0]["downloads"]["csv"]["href"]

# read the csv as df
storage_options = {'User-Agent': 'Mozilla/5.0'}
df = pd.read_csv(csv_url,
                 storage_options=storage_options)

# inflation categories
# getting rid of the numbers and special characters
inflation_cats = df["Aggregate"]
renamed_inflation_cats = []
for row in inflation_cats:
    if row != "Overall Index":
        renamed_inflation_cats.append(row.split(" ", 1)[1])
    else:
        renamed_inflation_cats.append(row)
df["renamed_aggregate"] = renamed_inflation_cats

# df["Time"] = pd.to_datetime(df["Time"], format="%b-%y")
# df.sort_values(by=["Time", "renamed_aggregate"], inplace=True)
# df.set_index("Time", inplace=True)
#
# # freq = "MS" means month start
# # https://stackoverflow.com/questions/35339139/what-values-are-valid-in-pandas-freq-tags
# df["inflation_oty"] = (df["v4_0"] - df["v4_0"].shift(12, freq="MS")) / (df["v4_0"].shift(12, freq="MS"))

# ------ Dash --------- #

app = Dash(__name__)
server = app.server


app.layout = html.Div(children=[
    html.H1(children="UK Annual Inflation Rate (CPIH Index)", className="header"),
    html.Div(children="Use the drop down menu to look at UK inflation in different sectors"),
    dcc.Dropdown(df["renamed_aggregate"].unique(),
                 ["Overall Index"],
                 id="yaxis-column",
                 multi=True),
    dcc.Graph(id="inflation-graph"),
    html.P(children=["source:",
                     html.A(href="https://api.beta.ons.gov.uk/v1/datasets/cpih01/editions/time-series/versions",
                            children="ONS API")]),
    html.P(children=["Last update: ", now]),
    html.P(children=["Made by ",
                     html.A(href="https://www.wesleyjessie.com",
                            children="Wesley Jessie")])
])

# in the callback function:
# # The arguments are positional by default: first the Input items and then any State items are given in the same order
# as in the decorator
@app.callback(
    Output("inflation-graph", "figure"),
    Input("yaxis-column", "value"))
def update_graph(selected_cats):

    # create a dictionary that contains multiple dataframes
    # each one is a dataframe that contains the category that the user selects on the dashboard
    df_dict = {}
    for cat in selected_cats:
        df_dict[cat] = df[df["renamed_aggregate"] == cat].copy()

        df_dict[cat]["Time"] = pd.to_datetime(df_dict[cat]["Time"], format="%b-%y")
        df_dict[cat].sort_values(by=["Time"], inplace=True)
        df_dict[cat].set_index("Time", inplace=True)

        # freq = "MS" means month start
        # https://stackoverflow.com/questions/35339139/what-values-are-valid-in-pandas-freq-tags
        df_dict[cat]["inflation_oty"] = (df_dict[cat]["v4_0"] - df_dict[cat]["v4_0"].shift(12,freq="MS")) / (df_dict[cat]["v4_0"].shift(12, freq="MS"))


    fig = go.Figure()
    for cat in selected_cats:
        fig.add_trace(go.Scatter(x=df_dict[cat].index, y=df_dict[cat]["inflation_oty"],
                      mode="lines", name=cat))
    graph_background = "#FAF3F3"
    fig.update_layout(yaxis_tickformat=".2%", plot_bgcolor=graph_background,
                      paper_bgcolor=graph_background)


    return fig


if __name__ == "__main__":
    app.run_server(debug=True)
