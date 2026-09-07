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

# ── "Aurora" theme palette ───────────────────────────────────────────────────
BG          = "#0d1117"   # page background
CARD_BG     = "#161b22"   # card surface
CARD_BG_2   = "#1c2330"   # slightly lighter surface (KPI cards)
BORDER      = "#30363d"
TEXT_PRI    = "#e6edf3"
TEXT_SEC    = "#8b949e"
ACCENT_A    = "#3fb950"   # green
ACCENT_B    = "#58a6ff"   # blue
GRID        = "#21262d"

COLORS = ["#3fb950","#58a6ff","#f7b955","#f0666e",
          "#bc8cff","#39c5cf","#ff9e64","#7ee787"]

# ── Chart builder ──────────────────────────────────────────────────────────────
def dark_base():
    """Base layout for line/area charts."""
    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT_SEC, size=11, family="Inter, 'Segoe UI', sans-serif"),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=TEXT_PRI, size=11),
                    orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(gridcolor=GRID, linecolor=BORDER, zeroline=False),
        yaxis=dict(gridcolor=GRID, linecolor=BORDER, zeroline=False),
        margin=dict(l=40, r=10, t=30, b=30),
        hovermode="x unified",
        hoverlabel=dict(bgcolor=CARD_BG_2, bordercolor=BORDER,
                         font=dict(color=TEXT_PRI, family="Inter, sans-serif"))
    )

def dark_map():
    """Base layout for map (no x/y axis, zero margin)."""
    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT_SEC, size=11, family="Inter, 'Segoe UI', sans-serif"),
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
        hover_name="country", color_continuous_scale="Tealgrn",
        labels={"co2":"CO₂ (Mt)"}
    )
    fig3.update_layout(
        **dark_map(),
        geo=dict(
            bgcolor=BG,
            showframe=False,
            showcoastlines=True, coastlinecolor=BORDER,
            showland=True, landcolor=CARD_BG,
            showocean=True, oceancolor=BG
        ),
        coloraxis_colorbar=dict(
            tickfont=dict(color=TEXT_SEC, size=10),
            title=dict(font=dict(color=TEXT_SEC, size=11))
        )
    )

    return fig1, fig2, fig3

def make_kpis(countries, y0, y1):
    """Compute quick summary stats for the KPI strip."""
    latest = y1
    co2_now = co2_df[(co2_df["country"].isin(countries)) & (co2_df["year"] == latest)]
    energy_now = energy_df[(energy_df["country"].isin(countries)) & (energy_df["year"] == latest)]

    avg_co2 = co2_now["co2_per_capita"].mean()
    avg_renew = energy_now["renewables_share_elec"].mean()
    total_co2 = co2_now["co2"].sum()

    n_countries = f"{len(countries)}"
    avg_co2_str = f"{avg_co2:.1f} t" if pd.notna(avg_co2) else "—"
    avg_renew_str = f"{avg_renew:.0f}%" if pd.notna(avg_renew) else "—"
    total_co2_str = f"{total_co2:,.0f} Mt" if pd.notna(total_co2) else "—"
    span_str = f"{y0}–{y1}"

    return n_countries, avg_co2_str, avg_renew_str, total_co2_str, span_str

# Pre-build at startup so charts appear immediately on load
f1, f2, f3 = make_charts(DEFAULT, 2000, 2022)
kpi_vals = make_kpis(DEFAULT, 2000, 2022)
print("✅ Charts built successfully")

# ── Styles ─────────────────────────────────────────────────────────────────────
CARD = {
    "backgroundColor": CARD_BG,
    "borderRadius": "14px",
    "padding": "18px",
    "border": f"1px solid {BORDER}",
    "boxShadow": "0 4px 18px rgba(0,0,0,0.25)"
}
H3ST = {"fontSize":"14px","fontWeight":"600","color":TEXT_PRI,"margin":"0 0 2px",
        "letterSpacing":"0.2px"}
PST  = {"fontSize":"11px","color":TEXT_SEC,"margin":"0 0 12px"}

KPI_CARD = {
    "backgroundColor": CARD_BG_2,
    "borderRadius": "12px",
    "border": f"1px solid {BORDER}",
    "padding": "14px 18px",
    "flex": "1",
    "textAlign": "center"
}
KPI_LABEL = {"fontSize":"10px","color":TEXT_SEC,"textTransform":"uppercase",
             "letterSpacing":"0.6px","margin":"0 0 6px","fontWeight":"600"}
KPI_VALUE = {"fontSize":"22px","fontWeight":"700","margin":"0",
             "background":f"linear-gradient(90deg, {ACCENT_A}, {ACCENT_B})",
             "WebkitBackgroundClip":"text","WebkitTextFillColor":"transparent",
             "backgroundClip":"text"}

# ── App ────────────────────────────────────────────────────────────────────────
app = Dash(__name__)

# Custom HTML shell — Google font, favicon, scrollbar & widget theming
app.index_string = """
<!DOCTYPE html>
<html>
<head>
    {%metas%}
    <title>Global Climate & Sustainability Dashboard</title>
    {%favicon%}
    {%css%}
    <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🌍</text></svg>">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        html, body { background-color: #0d1117; margin: 0; }
        * { font-family: 'Inter', 'Segoe UI', sans-serif; box-sizing: border-box; }

        ::-webkit-scrollbar { width: 10px; height: 10px; }
        ::-webkit-scrollbar-track { background: #0d1117; }
        ::-webkit-scrollbar-thumb { background: #30363d; border-radius: 6px; }
        ::-webkit-scrollbar-thumb:hover { background: #3fb950; }

        .kpi-card { transition: transform 0.15s ease, border-color 0.15s ease; }
        .kpi-card:hover { transform: translateY(-2px); border-color: #3fb950; }

        .chart-card { transition: border-color 0.15s ease, box-shadow 0.15s ease; }
        .chart-card:hover { border-color: #3fb950; box-shadow: 0 6px 22px rgba(63,185,80,0.12); }

        /* Dropdown theming */
        .Select-control, .Select-menu-outer, .Select-value, .Select-input > input,
        div[class*="-control"] {
            background-color: #0d1117 !important;
            border-color: #30363d !important;
            color: #e6edf3 !important;
        }
        div[class*="-menu"] { background-color: #161b22 !important; }
        div[class*="-option"] { background-color: #161b22 !important; color: #e6edf3 !important; }
        div[class*="-option"]:hover { background-color: #21262d !important; }
        .Select--multi .Select-value {
            background-color: rgba(63,185,80,0.15) !important;
            border-color: #3fb950 !important;
            color: #7ee787 !important;
        }
        div[class*="-singleValue"], div[class*="-Input"] input { color: #e6edf3 !important; }
        div[class*="-placeholder"] { color: #8b949e !important; }
        div[class*="-multiValue"] {
            background-color: rgba(63,185,80,0.15) !important;
            border-radius: 6px !important;
        }
        div[class*="-multiValueLabel"] { color: #7ee787 !important; }

        /* Range slider theming */
        .rc-slider-track { background-color: #3fb950 !important; }
        .rc-slider-rail { background-color: #30363d !important; }
        .rc-slider-handle {
            border-color: #3fb950 !important;
            background-color: #0d1117 !important;
        }
        .rc-slider-handle:hover, .rc-slider-handle:active { border-color: #58a6ff !important; }
        .rc-slider-dot { border-color: #30363d !important; background-color: #161b22 !important; }
        .rc-slider-tooltip-inner {
            background-color: #1c2330 !important;
            color: #e6edf3 !important;
            border: 1px solid #30363d;
        }
    </style>
</head>
<body>
    {%app_entry%}
    <footer>
        {%config%}
        {%scripts%}
        {%renderer%}
    </footer>
</body>
</html>
"""

app.layout = html.Div(
    style={"fontFamily":"'Inter','Segoe UI',sans-serif","backgroundColor":BG,
           "minHeight":"100vh","padding":"28px","color":TEXT_PRI},
    children=[

        # Header
        html.Div([
            html.H1("🌍 Global Climate & Sustainability Dashboard",
                    style={"fontSize":"25px","fontWeight":"700","margin":"0 0 4px",
                           "background":f"linear-gradient(90deg, {ACCENT_A}, {ACCENT_B})",
                           "WebkitBackgroundClip":"text","WebkitTextFillColor":"transparent",
                           "backgroundClip":"text","display":"inline-block"}),
            html.P("CO₂ emissions and renewable energy trends by country",
                   style={"color":TEXT_SEC,"margin":"0","fontSize":"13px"})
        ], style={"marginBottom":"22px"}),

        # KPI strip
        html.Div(
            id="kpi-row",
            style={"display":"flex","gap":"14px","marginBottom":"18px","flexWrap":"wrap"},
            children=[
                html.Div(className="kpi-card", style=KPI_CARD, children=[
                    html.P("Countries", style=KPI_LABEL),
                    html.P(kpi_vals[0], id="kpi-count", style=KPI_VALUE)
                ]),
                html.Div(className="kpi-card", style=KPI_CARD, children=[
                    html.P("Avg CO₂ / Capita", style=KPI_LABEL),
                    html.P(kpi_vals[1], id="kpi-co2", style=KPI_VALUE)
                ]),
                html.Div(className="kpi-card", style=KPI_CARD, children=[
                    html.P("Avg Renewable Share", style=KPI_LABEL),
                    html.P(kpi_vals[2], id="kpi-renew", style=KPI_VALUE)
                ]),
                html.Div(className="kpi-card", style=KPI_CARD, children=[
                    html.P("Total CO₂ (end year)", style=KPI_LABEL),
                    html.P(kpi_vals[3], id="kpi-total", style=KPI_VALUE)
                ]),
                html.Div(className="kpi-card", style=KPI_CARD, children=[
                    html.P("Year Range", style=KPI_LABEL),
                    html.P(kpi_vals[4], id="kpi-span", style=KPI_VALUE)
                ]),
            ]
        ),

        # Controls
        html.Div(style={**CARD, "marginBottom":"18px"}, children=[
            html.Div(style={"display":"flex","alignItems":"flex-end","flexWrap":"wrap","gap":"20px"}, children=[

                html.Div(style={"flex":"2","minWidth":"260px"}, children=[
                    html.Label("Select Countries",
                               style={"fontSize":"12px","color":TEXT_SEC,
                                      "marginBottom":"6px","display":"block",
                                      "fontWeight":"600"}),
                    dcc.Dropdown(
                        id="dd",
                        options=[{"label":c,"value":c} for c in countries_list],
                        value=DEFAULT,
                        multi=True
                    )
                ]),

                html.Div(style={"flex":"3","minWidth":"320px"}, children=[
                    html.Label("Year Range",
                               style={"fontSize":"12px","color":TEXT_SEC,
                                      "marginBottom":"6px","display":"block",
                                      "fontWeight":"600"}),
                    dcc.RangeSlider(
                        id="sl", min=1990, max=2022, step=1, value=[2000,2022],
                        marks={y:{"label":str(y),
                                  "style":{"color":TEXT_SEC,"fontSize":"11px"}}
                               for y in range(1990,2023,5)},
                        tooltip={"placement":"bottom","always_visible":False}
                    )
                ])
            ])
        ]),

        # Row 1 — two charts side by side
        html.Div(
            style={"display":"grid","gridTemplateColumns":"1fr 1fr",
                   "gap":"18px","marginBottom":"18px"},
            children=[
                html.Div(className="chart-card", style=CARD, children=[
                    html.H3("CO₂ Emissions per Capita", style=H3ST),
                    html.P("Tonnes of CO₂ per person per year", style=PST),
                    dcc.Graph(id="g1", figure=f1,
                              config={"displayModeBar":False},
                              style={"height":"260px"})
                ]),
                html.Div(className="chart-card", style=CARD, children=[
                    html.H3("Renewable Energy Share", style=H3ST),
                    html.P("% of electricity from renewable sources", style=PST),
                    dcc.Graph(id="g2", figure=f2,
                              config={"displayModeBar":False},
                              style={"height":"260px"})
                ])
            ]
        ),

        # Row 2 — world map
        html.Div(className="chart-card", style={**CARD,"marginBottom":"18px"}, children=[
            html.H3("World CO₂ Emissions Map", style=H3ST),
            html.P("Total CO₂ by country for the selected end year", style=PST),
            dcc.Graph(id="g3", figure=f3,
                      config={"displayModeBar":False},
                      style={"height":"340px"})
        ]),

        # Footer
        html.Div("Data: Our World in Data · Built with Plotly Dash",
                 style={"textAlign":"center","color":"#5f6368","fontSize":"12px",
                        "paddingTop":"16px","borderTop":f"1px solid {BORDER}"})
    ]
)

# ── Callback ───────────────────────────────────────────────────────────────────
@app.callback(
    Output("g1","figure"),
    Output("g2","figure"),
    Output("g3","figure"),
    Output("kpi-count","children"),
    Output("kpi-co2","children"),
    Output("kpi-renew","children"),
    Output("kpi-total","children"),
    Output("kpi-span","children"),
    Input("dd","value"),
    Input("sl","value"),
)
def update(countries, yr):
    if not countries:
        countries = DEFAULT
    fig1, fig2, fig3 = make_charts(countries, yr[0], yr[1])
    n, co2v, renewv, totalv, spanv = make_kpis(countries, yr[0], yr[1])
    return fig1, fig2, fig3, n, co2v, renewv, totalv, spanv

# ── Run ────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n🌍 Dashboard ready → http://127.0.0.1:8050\n")
    app.run(debug=False)