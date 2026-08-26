# 🌍 Global Climate and Sustainability Dashboard

An interactive, dark-themed web dashboard built with **Python**, **Plotly**, and **Dash** to visualize global CO₂ emissions trends, renewable energy adoption, and total carbon output across countries.

---

## ✨ Features

- **CO₂ Emissions per Capita**: Dynamic line chart comparing annual per-person CO₂ output (tonnes/person) across selected countries.
- **Renewable Energy Share**: Dynamic area chart visualizing the percentage of electricity generated from renewable sources.
- **World CO₂ Emissions Map**: Interactive choropleth map highlighting global CO₂ emissions for any selected end year.
- **Interactive Controls**: Multi-select country dropdown and custom year range slider for flexible data exploration.
- **Sleek Modern UI**: Custom dark aesthetic built for enhanced data visualization and readability.

---

## 🛠️ Data Sources

The dashboard leverages public datasets provided by **Our World in Data (OWID)**:
- `owid-co2-data.csv` (CO₂ and Greenhouse Gas Emissions)
- `owid-energy-data.csv` (Energy Production and Consumption)

---

## 🚀 Getting Started

### Prerequisites

Ensure you have Python 3.8+ installed on your system.

### 1. Clone the Repository

```bash
git clone https://github.com/Rithan7/Global-Climate-and-Sustainability-Dashboard.git
cd Global-Climate-and-Sustainability-Dashboard
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Data Setup

Download the OWID datasets and place them in the project root directory (or your local `Downloads` directory):
- [OWID CO2 Dataset](https://raw.githubusercontent.com/owid/co2-data/master/owid-co2-data.csv)
- [OWID Energy Dataset](https://raw.githubusercontent.com/owid/energy-data/master/owid-energy-data.csv)

### 4. Run the Dashboard

```bash
python dv.py
```

Open your browser and navigate to:
`http://127.0.0.1:8050`

---

## 📁 Repository Structure

```
├── dv.py              # Main Dash application code & chart definitions
├── requirements.txt   # Python dependencies
├── .gitignore         # File exclusions
└── README.md          # Project documentation
```
