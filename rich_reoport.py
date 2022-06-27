import pandas as pd
import datapane as dp
import altair as alt
import numpy as np

from vega_datasets import data as vega_data

def ignore_day(day):
    return day[:8] + "01"


def main():
    # download data & group by manufacturer
    df = pd.read_csv('https://covid.ourworldindata.org/data/vaccinations/vaccinations-by-manufacturer.csv', parse_dates=['date'], converters={"date": ignore_day})
    df.to_csv("raw_covid.csv")
    df = df.groupby(['vaccine', 'date'])['total_vaccinations'].sum()
    df.to_csv("covid.csv")
    df = df.tail(1000).reset_index()
    df.to_csv("covid_1000.csv")
    # plot vaccinations over time using Altair
    plot = alt.Chart(df).mark_area(opacity=0.4, stroke='black').encode(
        x='date:T',
        y=alt.Y('total_vaccinations:Q'),
        color=alt.Color('vaccine:N', scale=alt.Scale(scheme='set1')),
        tooltip='vaccine:N'
    ).interactive().properties(width='container')

    # tablulate total vaccinations by manufacturer
    total_df = df[df["date"] == df["date"].max()].sort_values("total_vaccinations", ascending=False).drop(["date"], axis="columns").reset_index(drop=True)
    # total_df = df.sort_values("total_vaccinations", ascending=False).drop(["date"], axis="columns").reset_index(drop=True)
    df.to_csv("covid_totals.csv")
    total_styled = total_df.style.bar(subset=["total_vaccinations"], color='#5fba7d', vmax=total_df["total_vaccinations"].sum())

    df = pd.DataFrame({
        'A': np.random.normal(-1, 1, 500),
        'B': np.random.normal(1, 2, 500),
    })

    some_data = dp.Group(columns=4,
                         blocks=[
                             dp.BigNumber(
                                 heading="Number of percentage points",
                                 value="84%",
                                 change="2%",
                                 is_upward_change=True
                             ),
                             dp.BigNumber(
                                 heading="Bad bad number",
                                 value="34%",
                                 change="-12%",
                                 is_upward_change=False
                             ),
                             dp.BigNumber(
                                 heading="Bad bad number",
                                 value="34%",
                                 prev_value="46%",
                                 is_positive_intent=False,
                                 change="-12%",
                                 is_upward_change=False
                             ),
                             dp.BigNumber(
                                 heading="Simple Statistic",
                                 value=100
                             )])
    gap = pd.read_json(vega_data.gapminder.url)

    select_year = alt.selection_single(
        name='select', fields=['year'], init={'year': 1955},
        bind=alt.binding_range(min=1955, max=2005, step=5)
    )
    alt_chart = alt.Chart(gap).mark_point(filled=True).encode(
        alt.X('fertility', scale=alt.Scale(zero=False)),
        alt.Y('life_expect', scale=alt.Scale(zero=False)),
        alt.Size('pop:Q'),
        alt.Color('cluster:N'),
        alt.Order('pop:Q', sort='descending'),
    ).add_selection(select_year).transform_filter(select_year)

    # embed into a Datapane Report
    report = dp.Report(
        dp.Page(title="first", blocks=[
            "## Vaccination Report",
            dp.Plot(plot, caption="Vaccinations by manufacturer over time"),
            dp.Plot(alt_chart, "With config"),
            some_data,
        ]),
        dp.Page(title="second", blocks=[
            dp.DataTable(df, caption="A DataTable", label="data table example"),
            dp.Table(total_df, caption="Current vaccination totals by manufacturer, unstyled"),
        ]),
        dp.Page(title="third", blocks=[
            dp.Table(total_styled, caption="Current vaccination totals by manufacturer"),
            dp.Table(df, caption="Initial Dataset (compressed by month)")
        ]),
    )
    report.save("report.html", open=True, formatting=dp.ReportFormatting(width=dp.ReportWidth.MEDIUM))


if __name__ == '__main__':
    main()
