"""
Test datapane as report generator for performance tests

all data: test + measurment

SELECT tr.id AS tid, started, ended, type, attr1, attr2, attr3, attr4, attr5, attr6,
       m.id AS mid , name, label1, label2, label3,label4, value
FROM test_run AS tr
INNER JOIN measurement AS m
ON tr.id = m.test_run_id

"""

import pandas as pd
import datapane as dp
import altair as alt

# from mysql_data import get_sdk_size
from mongo_data import get_sdk_size, get_performance_data
from version import last_minor_releases


def main():
    report = get_report()
    report.save("sdk_performance.html", open=True, formatting=dp.ReportFormatting(width=dp.ReportWidth.MEDIUM))


def get_report():
    return dp.Report(
        sdk_size(),
        latest_releases()
    )


def sdk_size():
    text = """
# SKD Size

Sdk size evolution.
    """
    sdk_vals = get_sdk_size()

    return dp.Page(title="SDK Size", blocks=[
        text,
        dp.Plot(get_sdk_trend_plot(sdk_vals)),
        dp.DataTable(sdk_vals)
    ])


def get_sdk_trend_plot(sdk_vals):
    all_points = alt.Chart(sdk_vals)

    all_dots = all_points.encode(
        x="started",
        y="value",
        tooltip="version",
        color="measurement",
        shape=alt.Shape("measurement"),
    ).mark_point(size=10, opacity=0.5)

    trend_line = all_points.encode(
        x="started",
        y="value",
        color=alt.Color("measurement", legend=None)
    ).mark_line(size=1, opacity=0.3)

    minor_releases = last_minor_releases(sdk_vals)

    last_chart = alt.Chart(sdk_vals[sdk_vals["version"].isin(minor_releases)])

    last_points = last_chart.encode(
        x="started",
        y="value",
    ).mark_point(size=55, opacity=1.0).encode(
        shape="measurement",
        color="measurement"
    )

    last_text = last_chart.mark_text(
        align='center',
        baseline='line-bottom',
        dy=-10
    ).encode(
        x="started",
        y="value",
        text='version'
    )

    line = (alt.Chart(pd.DataFrame({'y': [8000000]})).
            mark_rule(size=1, strokeDash=[4, 4], color="red", opacity=0.5).
            encode(y='y'))

    warn_text = alt.Chart(pd.DataFrame({'y': [8000000]})).mark_text(text="too much", align="center", opacity=1, baseline="line-bottom", dx=-350, fontSize=14).encode(y="y")

    return alt.layer(
        all_dots,
        trend_line,
        line,
        warn_text,
        last_points,
        last_text,
    ).properties(
        width=850,
        height=400
    ).interactive()


def latest_releases():
    text = """
    # Latest Releases
    
This page compares the current release with the previous and with
the previous minor and previous major releases.
    """

    performance = get_performance_data()


    return dp.Page(title="Latest Releases", blocks=[
        text,
    ])





if __name__ == '__main__':
    main()
