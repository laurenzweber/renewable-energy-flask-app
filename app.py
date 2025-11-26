from flask import Flask, render_template, request
import pandas as pd
import plotly.express as px

app = Flask(__name__)

# ---------------------------------------------------------
# Load data from Excel file
# ---------------------------------------------------------
excel_file = "Data.xlsx"

df1 = pd.read_excel(excel_file, sheet_name="General")
df_transport = pd.read_excel(excel_file, sheet_name="Transport")
df_electricity = pd.read_excel(excel_file, sheet_name="Electricity")
df_heating = pd.read_excel(excel_file, sheet_name="Heating.cooling")

# ---------------------------------------------------------
# Cleaning df1 (General)
# ---------------------------------------------------------
df1.columns = df1.columns.str.strip()

country_col = "Countries"
year_cols = df1.columns[1:]

df1[year_cols] = (
    df1[year_cols]
    .replace(",", ".", regex=True)
    .apply(pd.to_numeric, errors="coerce")
)

# List of countries for dropdowns
countries = sorted(df1[country_col].unique())

# Average renewable share in Europe per year
average_renewable_energy_europe = df1[year_cols].mean(axis=0)


# ---------------------------------------------------------
# FRONT PAGE
# ---------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


# ---------------------------------------------------------
# VISUALISATION 1: Renewables vs EU Target
# ---------------------------------------------------------
@app.route("/renewables")
def renewables():
    value_col = "2023"

    data = df1[[country_col, value_col]].copy()
    data = data.rename(columns={
        country_col: "Country",
        value_col: "Renewable (%)"
    })

    data = data.sort_values("Renewable (%)", ascending=True)

    eu_target = 32
    data["Status"] = data["Renewable (%)"].apply(
        lambda x: "Above target" if x >= eu_target else "Below target"
    )

    fig = px.bar(
        data,
        x="Renewable (%)",
        y="Country",
        color="Status",
        orientation="h",
        color_discrete_map={"Above target": "#C1E1C1", "Below target": "#FAA0A0"},
        hover_name=None,
        hover_data={"Renewable (%)": ":.1f"},
        title=None,
    )

    fig.update_traces(hovertemplate="%{x:.1f}%")
    fig.add_vline(
        x=eu_target,
        line_dash="dash",
        line_color="#02024d",
        annotation_text=f"EU Target {eu_target}%",
        annotation_position="top right",
    )

    fig.update_layout(
        height=1500,
        xaxis_title="Renewable energy share (in %)",
        yaxis_title=None,
        legend_title=None,
        template="plotly_white"
    )

    plot_html = fig.to_html(full_html=False, include_plotlyjs="cdn")
    return render_template("renewables.html", plot_html=plot_html)


# ---------------------------------------------------------
# VISUALISATION 2: Country comparison
# ---------------------------------------------------------
@app.route("/chart2")
def chart2():
    selected_countries = request.args.getlist("countries")

    if not selected_countries:
        selected_countries = countries[:3]

    subset = df1[df1[country_col].isin(selected_countries)].set_index(country_col)

    data_t = subset.T
    data_t.index.name = "Year"
    data_t = data_t.reset_index()

    fig = px.bar(
        data_t,
        x="Year",
        y=selected_countries,   # wide form
        barmode="group",
        title=None,
        labels={
            "Year": "Year",
            "value": "Share in %",
            "variable": "Country"
        },
        color_discrete_sequence=[
            "#A7C7E7",
            "#8ABAD3",
            "#7FB7A4",
            "#A8D5BA",
            "#C1E7E3",
            "#C6D8F0",
            "#AEC9C2"
        ]
    )

    fig.update_layout(
        template="plotly_white",
        width=900,
        height=600,
        legend_title=None,
        xaxis_title="Year",
        yaxis_title="Share in %",
    )

    # Prozentzeichen an der Skala der y-Achse
    fig.update_yaxes(ticksuffix="%")

    plot_html = fig.to_html(full_html=False, include_plotlyjs="cdn")

    return render_template(
        "chart2.html",
        plot_html=plot_html,
        countries=countries,
        selected_countries=selected_countries,
    )


# ---------------------------------------------------------
# VISUALISATION 3: Overview Europe
# ---------------------------------------------------------
@app.route("/chart3")
def chart3():
    df_avg = average_renewable_energy_europe.reset_index()
    df_avg.columns = ["Year", "Average Renewable Energy (%)"]
    df_avg["Year"] = df_avg["Year"].astype(int)

    fig = px.line(
        df_avg,
        x="Year",
        y="Average Renewable Energy (%)",
        markers=True,
        title=None,
        hover_data={"Year": True, "Average Renewable Energy (%)": ':.2f'}
    )

    fig.update_layout(
        template="plotly_white",
        height=500,
        margin=dict(l=30, r=30, t=10, b=40),
        xaxis_title="Year",
        yaxis_title="Average share in %",
    )

    fig.update_yaxes(ticksuffix="%")

    fig.update_traces(
        hovertemplate="Year: %{x}<br>Avg: %{y:.2f}%",
        line=dict(color="#02024d", width=3),
        marker=dict(color="#02024d", size=8)
    )

    plot_html = fig.to_html(full_html=False, include_plotlyjs="cdn")

    return render_template("chart3.html", plot_html=plot_html)


# ---------------------------------------------------------
# VISUALISATION 4: Progress
# ---------------------------------------------------------
@app.route("/chart4")
def chart4():
    years = ['2014', '2023']

    df_growth = df1[['Countries'] + years].copy()
    df_growth['growth'] = df_growth['2023'] - df_growth['2014']

    df_growth_sorted = df_growth.sort_values(by='growth', ascending=True)

    df_growth_sorted["Status"] = df_growth_sorted["growth"].apply(
        lambda v: "Negative Growth" if v < 0 else "Positive Growth"
    )

    fig = px.bar(
        df_growth_sorted,
        x="Countries",
        y="growth",
        color="Status",
        color_discrete_map={
            "Positive Growth": "#C1E1C1",  # pastel green
            "Negative Growth": "#FAA0A0",  # pastel red
        },
        hover_data={"Countries": False, "growth": ":.2f"},
        labels={"Countries": "Country", "growth": "Growth in %"},
        title=None
    )

    fig.update_layout(
        xaxis_title="Country",
        yaxis_title="Growth in renewable energy (in %)",
        xaxis_tickangle=45,
        legend_title=None,
        height=700,
        template="plotly_white",
        margin=dict(l=40, r=40, t=20, b=40)
    )

    fig.update_yaxes(ticksuffix="%")

    plot_html = fig.to_html(full_html=False, include_plotlyjs="cdn")
    return render_template("chart4.html", plot_html=plot_html)


# ---------------------------------------------------------
# VISUALISATION 5: Overview sectors
# ---------------------------------------------------------
@app.route("/chart5")
def chart5():
    years = [c for c in df_transport.columns if c != "Countries"]
    years = sorted(years)

    countries_list = sorted(df_transport["Countries"].unique())

    selected_year = request.args.get("year", default=years[-1])
    selected_country1 = request.args.get("country1", default=countries_list[0])
    default_country2 = (
        countries_list[1] if len(countries_list) > 1 else countries_list[0]
    )
    selected_country2 = request.args.get("country2", default=default_country2)

    selected_countries = [selected_country1, selected_country2]

    rows = []
    for c in selected_countries:
        t = df_transport.loc[df_transport["Countries"] == c, selected_year].iloc[0]
        e = df_electricity.loc[df_electricity["Countries"] == c, selected_year].iloc[0]
        h = df_heating.loc[df_heating["Countries"] == c, selected_year].iloc[0]

        rows.append({"Country": c, "Sector": "Transport", "Value": t})
        rows.append({"Country": c, "Sector": "Electricity", "Value": e})
        rows.append({"Country": c, "Sector": "Heating & Cooling", "Value": h})

    df_group = pd.DataFrame(rows)

    fig_group = px.bar(
        df_group,
        x="Sector",
        y="Value",
        color="Country",
        barmode="group",
        title=None,
        labels={
            "Sector": "Sector",
            "Value": "Share in %",
            "Country": "Country"
        },
        color_discrete_sequence=["#8ABAD3", "#7FB7A4"]
    )

    fig_group.update_layout(
        template="plotly_white",
        height=600,
        legend_title=None,
        xaxis_title="Sector",
        yaxis_title="Share in %",
        margin=dict(l=30, r=30, t=10, b=40)
    )

    fig_group.update_yaxes(ticksuffix="%")
    fig_group.update_traces(hovertemplate="%{y:.2f}%")

    plot_html_group = fig_group.to_html(full_html=False, include_plotlyjs="cdn")

    return render_template(
        "chart5.html",
        plot_html_group=plot_html_group,
        years=years,
        countries=countries_list,
        selected_year=selected_year,
        selected_country1=selected_country1,
        selected_country2=selected_country2,
    )


# ---------------------------------------------------------
# VISUALISATION 6: Sector by year
# ---------------------------------------------------------
@app.route("/chart6")
def chart6():
    selected_sector = request.args.get("sector", "Transport")

    if selected_sector == "Transport":
        df_sector = df_transport
    elif selected_sector == "Electricity":
        df_sector = df_electricity
    elif selected_sector in ["Heating", "Heating.cooling"]:
        df_sector = df_heating
    else:
        df_sector = df_transport  # fallback

    df_sector.columns = df_sector.columns.str.strip()

    years = [c for c in df_sector.columns if c != "Countries"]
    selected_year = request.args.get("year", years[-1])

    # Build data for chart
    data = df_sector[["Countries", selected_year]].copy()
    data = data.rename(columns={"Countries": "Country", selected_year: "Value"})
    data = data.sort_values("Value", ascending=False)

    fig = px.bar(
        data,
        x="Country",
        y="Value",
        title=None,
        labels={
            "Country": "Country",
            "Value": "Share in %"
        },
        color_discrete_sequence=["#A7C7E7"]
    )

    fig.update_layout(
        template="plotly_white",
        width=1000,
        height=600,
        xaxis_title="Country",
        yaxis_title="Share in %",
        showlegend=False
    )

    # Prozentzeichen an der y-Achse
    fig.update_yaxes(ticksuffix="%")

    plot_html = fig.to_html(full_html=False, include_plotlyjs="cdn")

    return render_template(
        "chart6.html",
        plot_html=plot_html,
        years=years,
        sectors=["Transport", "Electricity", "Heating.cooling"],
        selected_year=selected_year,
        selected_sector=selected_sector
    )


# ---------------------------------------------------------
# Run app
# ---------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
