import altair as alt


def trend_plot(data_frame, x, y, time_series, title):

    chart = alt.Chart(data_frame).encode(
        x=x,
        y=y,
        color=time_series,
        shape=time_series,
    )

    dots = chart.mark_point()
    line = chart.mark_line()

    return (
        alt.layer(dots, line)
        .properties(
            width=850,
            height=400,
            title=title,
        )
        .interactive()
    )
