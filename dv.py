import os
import sys
import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output

# Force stdout encoding to UTF-8 for Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ── Load data ──────────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOADS  = os.path.join(os.path.expanduser("~"), "Downloads")

def find_file(name):
    for folder in [SCRIPT_DIR, DOWNLOADS]:
        p = os.path.join(folder, name)
        if os.path.exists(p):
            print(f"[OK] {name} found at {p}")
            return p
    if name == "owid-co2-data.csv":
        url = "https://raw.githubusercontent.com/owid/co2-data/master/owid-co2-data.csv"
        print(f"[ONLINE] Fetching {name} online from {url}")
        return url
    elif name == "owid-energy-data.csv":
        url = "https://raw.githubusercontent.com/owid/energy-data/master/owid-energy-data.csv"
        print(f"[ONLINE] Fetching {name} online from {url}")
        return url
    return None

def clean(df):
    return df[df["iso_code"].notna() & ~df["iso_code"].astype(str).str.startswith("OWID")]

co2_df    = clean(pd.read_csv(find_file("owid-co2-data.csv")))
energy_df = clean(pd.read_csv(find_file("owid-energy-data.csv")))

print(f"[DATA] CO2 rows: {len(co2_df)}")
print(f"[DATA] Energy rows: {len(energy_df)}")

TOP = ["United States","China","India","Germany","Brazil",
       "United Kingdom","Russia","Japan","Canada","Australia"]
countries_list = sorted(co2_df[co2_df["country"].isin(TOP)]["country"].unique())
DEFAULT = ["United States","China","India","Germany"]

# ── "Cyber Emerald" Theme Palette ──────────────────────────────────────────────
BG          = "#0b0f19"   # Ultra-deep midnight obsidian background
CARD_BG     = "#111827"   # Rich slate dark card surface
CARD_BG_2   = "#1e293b"   # Slightly lighter slate for KPI cards
BORDER      = "#1f293d"   # Crisp card border
TEXT_PRI    = "#f8fafc"   # High contrast bright text
TEXT_SEC    = "#94a3b8"   # Readable secondary text
TEXT_MUTED  = "#cbd5e1"   # High visibility slider mark text
ACCENT_A    = "#10b981"   # Vibrant Emerald Green
ACCENT_B    = "#06b6d4"   # Electric Cyan
GRID        = "#1e293b"

COLORS = [
    "#10b981",  # Emerald
    "#06b6d4",  # Cyan
    "#f59e0b",  # Amber
    "#ec4899",  # Pink
    "#8b5cf6",  # Violet
    "#3b82f6",  # Blue
    "#14b8a6",  # Teal
    "#f43f5e"   # Rose
]

# ── Chart Builders ─────────────────────────────────────────────────────────────
def dark_base():
    """Base layout for line/area charts."""
    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT_SEC, size=11, family="Inter, 'Segoe UI', sans-serif"),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color=TEXT_PRI, size=11),
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        xaxis=dict(gridcolor=GRID, linecolor=BORDER, zeroline=False, tickfont=dict(color=TEXT_SEC)),
        yaxis=dict(gridcolor=GRID, linecolor=BORDER, zeroline=False, tickfont=dict(color=TEXT_SEC)),
        margin=dict(l=40, r=10, t=30, b=30),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor=CARD_BG_2,
            bordercolor=ACCENT_B,
            font=dict(color=TEXT_PRI, family="Inter, sans-serif")
        )
    )

def dark_map():
    """Base layout for map."""
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
    fig1 = px.line(
        d1, x="year", y="co2_per_capita", color="country",
        color_discrete_sequence=COLORS,
        labels={"co2_per_capita":"Tonnes / person", "year":""}
    )
    fig1.update_layout(**dark_base())
    fig1.update_traces(line_width=2.8)

    # ── Renewable area chart ───────────────────────────────────────────────────
    d2 = energy_df[
        energy_df["country"].isin(countries) &
        energy_df["year"].between(y0, y1) &
        energy_df["renewables_share_elec"].notna()
    ]
    fig2 = px.area(
        d2, x="year", y="renewables_share_elec", color="country",
        color_discrete_sequence=COLORS,
        labels={"renewables_share_elec":"% renewable", "year":""}
    )
    fig2.update_layout(**dark_base())
    fig2.update_traces(line_width=2)

    # ── World choropleth map ───────────────────────────────────────────────────
    d3 = co2_df[(co2_df["year"] == y1) & co2_df["co2"].notna()]
    fig3 = px.choropleth(
        d3, locations="iso_code", color="co2",
        hover_name="country", color_continuous_scale="Viridis",
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
            title=dict(font=dict(color=TEXT_PRI, size=11))
        )
    )

    return fig1, fig2, fig3

def make_kpis(countries, y0, y1):
    """Compute summary stats for KPI strip."""
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

# Pre-build at startup
f1, f2, f3 = make_charts(DEFAULT, 2000, 2022)
kpi_vals = make_kpis(DEFAULT, 2000, 2022)
print("[OK] Charts built successfully")

# ── Styles ─────────────────────────────────────────────────────────────────────
CARD = {
    "backgroundColor": CARD_BG,
    "borderRadius": "14px",
    "padding": "20px",
    "border": f"1px solid {BORDER}",
    "boxShadow": "0 8px 24px rgba(0,0,0,0.4)"
}
H3ST = {
    "fontSize":"15px","fontWeight":"600","color":TEXT_PRI,"margin":"0 0 2px",
    "letterSpacing":"0.3px"
}
PST  = {"fontSize":"12px","color":TEXT_SEC,"margin":"0 0 14px"}

KPI_CARD = {
    "backgroundColor": CARD_BG_2,
    "borderRadius": "12px",
    "border": f"1px solid {BORDER}",
    "padding": "16px 20px",
    "flex": "1",
    "minWidth": "160px",
    "textAlign": "center"
}
KPI_LABEL = {
    "fontSize":"11px","color":TEXT_SEC,"textTransform":"uppercase",
    "letterSpacing":"0.8px","margin":"0 0 6px","fontWeight":"600"
}
KPI_VALUE = {
    "fontSize":"24px","fontWeight":"700","margin":"0",
    "background":f"linear-gradient(90deg, {ACCENT_A}, {ACCENT_B})",
    "WebkitBackgroundClip":"text","WebkitTextFillColor":"transparent",
    "backgroundClip":"text"
}

# ── App ────────────────────────────────────────────────────────────────────────
app = Dash(__name__)

# Custom HTML shell — Google fonts, CSS controls & vibrant slider marks styling
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
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        html, body { background-color: #0b0f19; margin: 0; }
        * { font-family: 'Inter', 'Segoe UI', sans-serif; box-sizing: border-box; }

        ::-webkit-scrollbar { width: 10px; height: 10px; }
        ::-webkit-scrollbar-track { background: #0b0f19; }
        ::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 6px; }
        ::-webkit-scrollbar-thumb:hover { background: #10b981; }

        .kpi-card { transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease; }
        .kpi-card:hover { transform: translateY(-3px); border-color: #10b981; box-shadow: 0 8px 20px rgba(16,185,129,0.15); }

        .chart-card { transition: border-color 0.2s ease, box-shadow 0.2s ease; }
        .chart-card:hover { border-color: #06b6d4; box-shadow: 0 8px 25px rgba(6,182,212,0.15); }

        /* Dropdown custom styling */
        .Select-control, div[class*="-control"] {
            background-color: #1e293b !important;
            border: 1px solid #334155 !important;
            border-radius: 8px !important;
            color: #f8fafc !important;
            min-height: 42px !important;
        }
        div[class*="-menu"] {
            background-color: #1e293b !important;
            border: 1px solid #334155 !important;
            box-shadow: 0 10px 25px rgba(0,0,0,0.5) !important;
            border-radius: 8px !important;
        }
        div[class*="-option"] {
            background-color: #1e293b !important;
            color: #e2e8f0 !important;
            padding: 10px 14px !important;
        }
        div[class*="-option"]:hover, div[class*="-option"][class*="-isFocused"] {
            background-color: #334155 !important;
            color: #38bdf8 !important;
        }
        div[class*="-multiValue"] {
            background-color: rgba(16, 185, 129, 0.2) !important;
            border: 1px solid #10b981 !important;
            border-radius: 6px !important;
        }
        div[class*="-multiValueLabel"] {
            color: #34d399 !important;
            font-weight: 600 !important;
            font-size: 12px !important;
        }
        div[class*="-multiValueRemove"]:hover {
            background-color: rgba(239, 68, 68, 0.3) !important;
            color: #f87171 !important;
        }
        div[class*="-singleValue"], div[class*="-Input"] input { color: #f8fafc !important; }
        div[class*="-placeholder"] { color: #94a3b8 !important; }

        /* High Visibility Range Slider styling */
        .rc-slider-rail {
            background-color: #334155 !important;
            height: 6px !important;
        }
        .rc-slider-track {
            background: linear-gradient(90deg, #10b981, #06b6d4) !important;
            height: 6px !important;
        }
        .rc-slider-handle {
            border: 2px solid #ffffff !important;
            background-color: #06b6d4 !important;
            width: 18px !important;
            height: 18px !important;
            margin-top: -6px !important;
            box-shadow: 0 0 12px rgba(6, 182, 212, 0.7) !important;
        }
        .rc-slider-handle:hover, .rc-slider-handle:active {
            border-color: #ffffff !important;
            background-color: #10b981 !important;
            box-shadow: 0 0 16px rgba(16, 185, 129, 0.9) !important;
        }
        .rc-slider-dot {
            border-color: #475569 !important;
            background-color: #1e293b !important;
            width: 10px !important;
            height: 10px !important;
            bottom: -2px !important;
        }
        .rc-slider-dot-active {
            border-color: #38bdf8 !important;
            background-color: #06b6d4 !important;
        }
        .rc-slider-mark-text {
            color: #f1f5f9 !important;
            font-size: 12px !important;
            font-weight: 600 !important;
            margin-top: 8px !important;
            opacity: 0.95 !important;
        }
        .rc-slider-mark-text-active {
            color: #38bdf8 !important;
            font-weight: 700 !important;
            opacity: 1 !important;
        }
        .rc-slider-tooltip-inner {
            background-color: #1e293b !important;
            color: #f8fafc !important;
            border: 1px solid #06b6d4 !important;
            font-weight: 600;
            box-shadow: 0 4px 12px rgba(0,0,0,0.4);
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
           "minHeight":"100vh","padding":"30px 36px","color":TEXT_PRI},
    children=[

        # Header
        html.Div([
            html.H1("🌍 Global Climate & Sustainability Dashboard",
                    style={"fontSize":"26px","fontWeight":"800","margin":"0 0 6px",
                           "background":f"linear-gradient(90deg, {ACCENT_A}, {ACCENT_B})",
                           "WebkitBackgroundClip":"text","WebkitTextFillColor":"transparent",
                           "backgroundClip":"text","display":"inline-block",
                           "letterSpacing":"-0.5px"}),
            html.P("Real-time CO₂ emissions and renewable energy analytics across global economies",
                   style={"color":TEXT_SEC,"margin":"0","fontSize":"13px","fontWeight":"500"})
        ], style={"marginBottom":"24px"}),

        # KPI strip
        html.Div(
            id="kpi-row",
            style={"display":"flex","gap":"16px","marginBottom":"22px","flexWrap":"wrap"},
            children=[
                html.Div(className="kpi-card", style=KPI_CARD, children=[
                    html.P("Countries Selected", style=KPI_LABEL),
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
                    html.P("Selected Timeline", style=KPI_LABEL),
                    html.P(kpi_vals[4], id="kpi-span", style=KPI_VALUE)
                ]),
            ]
        ),

        # Controls Card
        html.Div(className="chart-card", style={**CARD, "marginBottom":"22px"}, children=[
            html.Div(style={"display":"flex","alignItems":"flex-end","flexWrap":"wrap","gap":"24px"}, children=[

                html.Div(style={"flex":"2","minWidth":"280px"}, children=[
                    html.Label("Select Countries",
                               style={"fontSize":"13px","color":TEXT_MUTED,
                                      "marginBottom":"8px","display":"block",
                                      "fontWeight":"600"}),
                    dcc.Dropdown(
                        id="dd",
                        options=[{"label":c,"value":c} for c in countries_list],
                        value=DEFAULT,
                        multi=True
                    )
                ]),

                html.Div(style={"flex":"3","minWidth":"360px"}, children=[
                    html.Label("Year Range Selection",
                               style={"fontSize":"13px","color":TEXT_MUTED,
                                      "marginBottom":"12px","display":"block",
                                      "fontWeight":"600"}),
                    dcc.RangeSlider(
                        id="sl", min=1990, max=2022, step=1, value=[2000,2022],
                        marks={
                            y: {
                                "label": str(y),
                                "style": {
                                    "color": "#f1f5f9",
                                    "fontSize": "12px",
                                    "fontWeight": "600"
                                }
                            }
                            for y in range(1990, 2023, 5)
                        },
                        tooltip={"placement":"bottom","always_visible":False}
                    )
                ])
            ])
        ]),

        # Row 1 — Charts
        html.Div(
            style={"display":"grid","gridTemplateColumns":"1fr 1fr",
                   "gap":"22px","marginBottom":"22px"},
            children=[
                html.Div(className="chart-card", style=CARD, children=[
                    html.H3("CO₂ Emissions per Capita", style=H3ST),
                    html.P("Tonnes of CO₂ per person annually across target nations", style=PST),
                    dcc.Graph(id="g1", figure=f1,
                               config={"displayModeBar":False},
                               style={"height":"280px"})
                ]),
                html.Div(className="chart-card", style=CARD, children=[
                    html.H3("Renewable Energy Share", style=H3ST),
                    html.P("Percentage of electricity generated from renewable sources", style=PST),
                    dcc.Graph(id="g2", figure=f2,
                               config={"displayModeBar":False},
                               style={"height":"280px"})
                ])
            ]
        ),

        # Row 2 — World Map
        html.Div(className="chart-card", style={**CARD,"marginBottom":"24px"}, children=[
            html.H3("World CO₂ Emissions Choropleth Map", style=H3ST),
            html.P("Global total CO₂ output distribution for the selected end year", style=PST),
            dcc.Graph(id="g3", figure=f3,
                      config={"displayModeBar":False},
                      style={"height":"360px"})
        ]),

        # Footer
        html.Div("Data: Our World in Data · Built with Plotly Dash & Python",
                 style={"textAlign":"center","color":TEXT_SEC,"fontSize":"12px",
                        "paddingTop":"18px","borderTop":f"1px solid {BORDER}"})
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
    print("\n[READY] Dashboard ready -> http://127.0.0.1:8050\n")
    app.run(debug=False)