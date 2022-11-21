from typing import Optional, Mapping, Any

import altair as alt
import datapane as dp
import pandas as pd
from mongo_data import to_data_frame
from report_spec import DataFrameSpec


def trend_plot(data_frame, x, y, time_series, split_by, title):
    test_selection = alt.binding_select(
        options=data_frame[split_by].unique(), name=split_by
    )
    selection = alt.selection_single(fields=[split_by], bind=test_selection)

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
        .transform_filter(selection)
        .add_selection(selection)
        .properties(
            width=850,
            height=400,
            title=title,
        )
        .interactive()
    )


def get_data_frame(docs, spec: DataFrameSpec, grouping: Optional[str] = None) -> pd.DataFrame:
    ret_val = to_data_frame(docs, spec)

    if spec.unique_columns is not None and len(spec.unique_columns) > 0 and grouping in {"latest", "min", "max", "mean"}:
        if grouping == "latest":
            ret_val.drop_duplicates(subset=spec.unique_columns, inplace=True, keep="last")
        else:
            # in one of ("max", "min", "mean") (do a group by the unique columns)
            group = ret_val.groupby(spec.unique_columns)
            # do value aggregation
            if grouping == "max":
                ret_val = group.max()
            elif grouping == "min":
                ret_val = group.min()
            elif grouping == "mean":
                ret_val = group.mean()
            # now all the grouping columns are part of the index,
            # reset the index to turn them back into normal columns
            ret_val = ret_val.reset_index()
    return ret_val


def _format_change_value(change: float) -> str:
    sign = ""
    if change < 0:
        sign = "-"
        change *= -1
    if change > 1 :
        # we need only 1 floating point precision if we are over 1%
        return f"{sign}{change:.1f}%"
    if change > 0.001:
        return f"{sign}{change:.3}%"
    else:
        # give up and use scientific notation
        return f"{sign}{change:.{2}}%"


def big_number(heading, current, previous, bigger_is_better):
    if previous is not None and current is not None:
        if previous != 0:
            change = (current - previous) / previous * 100
            change_str = _format_change_value(change)
        else:
            change = current
            change_str = f"{change:.{2}}"

        if (bigger_is_better and change >= 0) or (not bigger_is_better and change <= 0):
            positive_intent = True
        else:
            positive_intent = False

        upward_change = current >= previous

        current = f"{current:.{4}}"
        previous = f"{previous:.{4}}"

        return dp.BigNumber(
            heading=heading,
            value=current,
            change=change_str,
            prev_value=previous,
            is_positive_intent=positive_intent,
            is_upward_change=upward_change,
        )
    else:
        return dp.BigNumber(
            heading=heading,
            value=f"{current:.{4}}" if current is not None else "No Value",
            prev_value=f"{previous:.{4}}" if previous is not None else "No Value",
        )


def filter_data_frame(df: pd.DataFrame, conditions: Mapping[str, Any]):
    selection_condition = None
    for key, value in conditions.items():
        if selection_condition is None:
            selection_condition = df[key] == value
        else:
            selection_condition &= (df[key] == value)
    return df[selection_condition]
