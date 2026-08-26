
import os
import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output

# ── Load data ──────────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOADS  = os.path.join(os.path.expanduser("~"), "Downloads")

def find_file(name):
    for folder in [SCRIPT_DIR, DOWNLOADS]:
        p = os.path.join(folder, name)
        if os.path.exists(p):
            print(f"✅ {name} found at {p}")
            return p
    if name == "owid-co2-data.csv":
        url = "https://raw.githubusercontent.com/owid/co2-data/master/owid-co2-data.csv"
        print(f"🌐 Fetching {name} online from {url}")
        return url
    elif name == "owid-energy-data.csv":
        url = "https://raw.githubusercontent.com/owid/energy-data/master/owid-energy-data.csv"
        print(f"🌐 Fetching {name} online from {url}")
        return url
    return None

def clean(df):
    return df[df["iso_code"].notna() & ~df["iso_code"].astype(str).str.startswith("OWID")]

co2_df    = clean(pd.read_csv(find_file("owid-co2-data.csv")))
energy_df = clean(pd.read_csv(find_file("owid-energy-data.csv")))

print(f"✅ CO2 rows: {len(co2_df)}")
print(f"✅ Energy rows: {len(energy_df)}")

TOP = ["United States","China","India","Germany","Brazil",
       "United Kingdom","Russia","Japan","Canada","Australia"]
countries_list = sorted(co2_df[co2_df["country"].isin(TOP)]["country"].unique())
DEFAULT = ["United States","China","India","Germany"]

COLORS = ["#4fc3f7","#ef5350","#66bb6a","#ffa726",
          "#ab47bc","#26c6da","#ff7043","#ec407a"]

# ── Chart builder ──────────────────────────────────────────────────────────────
def dark_base():
    """Base layout for line/area charts."""
    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#9aa0a6", size=11),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#e8eaed", size=11),
                    orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(gridcolor="#2d2f3e", linecolor="#3c4043"),
        yaxis=dict(gridcolor="#2d2f3e", linecolor="#3c4043"),
        margin=dict(l=40, r=10, t=30, b=30),
        hovermode="x unified"
    )

def dark_map():
    """Base layout for map (no x/y axis, zero margin)."""
    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#9aa0a6", size=11),
        margin=dict(l=0, r=0, t=0, b=0)
    )

def make_charts(countries, y0, y1):
    # ── CO2 line chart ─────────────────────────────────────────────────────────
    d1 = co2_df[
        co2_df["country"].isin(countries) &
        co2_df["year"].between(y0, y1) &
        co2_df["co2_per_capita"].notna()
    ]
    fig1 = px.line(d1, x="year", y="co2_per_capita", color="country",
                   color_discrete_sequence=COLORS,
                   labels={"co2_per_capita":"Tonnes / person", "year":""})
    fig1.update_layout(**dark_base())
    fig1.update_traces(line_width=2.5)

    # ── Renewable area chart ───────────────────────────────────────────────────
    d2 = energy_df[
        energy_df["country"].isin(countries) &
        energy_df["year"].between(y0, y1) &
        energy_df["renewables_share_elec"].notna()
    ]
    fig2 = px.area(d2, x="year", y="renewables_share_elec", color="country",
                   color_discrete_sequence=COLORS,
                   labels={"renewables_share_elec":"% renewable", "year":""})
    fig2.update_layout(**dark_base())
    fig2.update_traces(line_width=2)

    # ── World choropleth map ───────────────────────────────────────────────────
    d3 = co2_df[(co2_df["year"] == y1) & co2_df["co2"].notna()]
    fig3 = px.choropleth(
        d3, locations="iso_code", color="co2",
        hover_name="country", color_continuous_scale="YlOrRd",
        labels={"co2":"CO₂ (Mt)"}
    )
    fig3.update_layout(
        **dark_map(),
        geo=dict(
            bgcolor="#0f1117",
            showframe=False,
            showcoastlines=True, coastlinecolor="#3c4043",
            showland=True, landcolor="#1e2130",
            showocean=True, oceancolor="#0f1117"
        ),
        coloraxis_colorbar=dict(
            tickfont=dict(color="#9aa0a6", size=10),
            title=dict(font=dict(color="#9aa0a6", size=11))
        )
    )

    return fig1, fig2, fig3

# Pre-build at startup so charts appear immediately on load
f1, f2, f3 = make_charts(DEFAULT, 2000, 2022)
print("✅ Charts built successfully")

# ── Styles ─────────────────────────────────────────────────────────────────────
CARD = {"backgroundColor":"#1e2130","borderRadius":"10px",
        "padding":"16px","border":"1px solid #3c4043"}
H3ST = {"fontSize":"14px","fontWeight":"500","color":"#e8eaed","margin":"0 0 2px"}
PST  = {"fontSize":"11px","color":"#9aa0a6","margin":"0 0 10px"}

# ── App ────────────────────────────────────────────────────────────────────────
app = Dash(__name__)

app.layout = html.Div(
    style={"fontFamily":"'Segoe UI',sans-serif","backgroundColor":"#0f1117",
           "minHeight":"100vh","padding":"24px","color":"#e8eaed"},
    children=[

        # Header
        html.Div([
            html.H1("🌍 Global Climate & Sustainability Dashboard",
                    style={"fontSize":"24px","fontWeight":"600",
                           "color":"#4fc3f7","margin":"0 0 4px"}),
            html.P("CO₂ emissions and renewable energy trends by country",
                   style={"color":"#9aa0a6","margin":"0","fontSize":"13px"})
        ], style={"marginBottom":"24px"}),

        # Controls
        html.Div(style={**CARD, "marginBottom":"16px"}, children=[
            html.Div(style={"display":"flex","alignItems":"flex-end"}, children=[

                html.Div(style={"flex":"2","marginRight":"24px"}, children=[
                    html.Label("Select Countries",
                               style={"fontSize":"12px","color":"#9aa0a6",
                                      "marginBottom":"6px","display":"block"}),
                    dcc.Dropdown(
                        id="dd",
                        options=[{"label":c,"value":c} for c in countries_list],
                        value=DEFAULT,
                        multi=True
                    )
                ]),

                html.Div(style={"flex":"3"}, children=[
                    html.Label("Year Range",
                               style={"fontSize":"12px","color":"#9aa0a6",
                                      "marginBottom":"6px","display":"block"}),
                    dcc.RangeSlider(
                        id="sl", min=1990, max=2022, step=1, value=[2000,2022],
                        marks={y:{"label":str(y),
                                  "style":{"color":"#9aa0a6","fontSize":"11px"}}
                               for y in range(1990,2023,5)},
                        tooltip={"placement":"bottom","always_visible":False}
                    )
                ])
            ])
        ]),

        # Row 1 — two charts side by side
        html.Div(
            style={"display":"grid","gridTemplateColumns":"1fr 1fr",
                   "gap":"16px","marginBottom":"16px"},
            children=[
                html.Div(style=CARD, children=[
                    html.H3("CO₂ Emissions per Capita", style=H3ST),
                    html.P("Tonnes of CO₂ per person per year", style=PST),
                    dcc.Graph(id="g1", figure=f1,
                              config={"displayModeBar":False},
                              style={"height":"260px"})
                ]),
                html.Div(style=CARD, children=[
                    html.H3("Renewable Energy Share", style=H3ST),
                    html.P("% of electricity from renewable sources", style=PST),
                    dcc.Graph(id="g2", figure=f2,
                              config={"displayModeBar":False},
                              style={"height":"260px"})
                ])
            ]
        ),

        # Row 2 — world map
        html.Div(style={**CARD,"marginBottom":"16px"}, children=[
            html.H3("World CO₂ Emissions Map", style=H3ST),
            html.P("Total CO₂ by country for the selected end year", style=PST),
            dcc.Graph(id="g3", figure=f3,
                      config={"displayModeBar":False},
                      style={"height":"340px"})
        ]),

        # Footer
        html.Div("Data: Our World in Data · Built with Plotly Dash",
                 style={"textAlign":"center","color":"#5f6368","fontSize":"12px",
                        "paddingTop":"16px","borderTop":"1px solid #3c4043"})
    ]
)

# ── Callback ───────────────────────────────────────────────────────────────────
@app.callback(
    Output("g1","figure"),
    Output("g2","figure"),
    Output("g3","figure"),
    Input("dd","value"),
    Input("sl","value"),
)
def update(countries, yr):
    if not countries:
        countries = DEFAULT
    return make_charts(countries, yr[0], yr[1])

# ── Run ────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n🌍 Dashboard ready → http://127.0.0.1:8050\n")
    app.run(debug=False)