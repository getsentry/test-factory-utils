import datapane as dp

from sdk_performance_datasets import get_cpu_usage, get_ram_usage
from sdk_performance_graphs import trend_plot


def main():
    cpu_usage = get_cpu_usage()
    ram_usage = get_ram_usage()

    report = dp.Report(
        trends_page(cpu_usage, ram_usage)
    )

    report.save("sdk_performance.html", open=True, formatting=dp.ReportFormatting(width=dp.ReportWidth.FULL))


def trends_page(cpu_usage, ram_usage):
    text = """
# SKD Trends
SDK evolution.
        """

    cpu_usage_plot = trend_plot(cpu_usage, x="commit_date", y="value", time_series="measurement", title="cpu usage")
    ram_usage_plot = trend_plot(ram_usage, x="commit_date", y="value", time_series="measurement", title="mem_usage")

    return dp.Page(
        title="Trends",
        blocks=[
            text,
            dp.Plot(cpu_usage_plot),
            dp.DataTable(cpu_usage),
            dp.Plot(ram_usage_plot),
            dp.DataTable(ram_usage)
        ]
    )


if __name__ == '__main__':
    main()
