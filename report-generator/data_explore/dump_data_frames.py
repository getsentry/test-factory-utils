from typing import Mapping, List, Tuple
from datetime import datetime

import datapane as dp

from google.cloud import storage
import click

from mongo_data import get_db, get_docs

from sdk_performance_datasets import get_cpu_usage, get_ram_usage


@click.command()
@click.option("--mongo-db", "-m", "mongo_url", envvar='MONGO_DB', required=True, help="url of mongo db (something like: 'mongodb://mongo-server/27017')")
@click.option("--filters", "-f", multiple=True, type=(str, str))
@click.option("--git-sha", "-s", envvar="REFERENCE_SHA", required=True, help="the git sha of the version of interest")
def main(mongo_url, filters, git_sha, ):
    print("Dumping data frames to csv files")
    db = get_db(mongo_url)

    trend_filters = [*filters, ("is_default_branch", "1")]
    current_filters = [*filters, ("commit_sha", git_sha)]

    trend_docs = get_docs(db, trend_filters)
    current_docs = get_docs(db, current_filters)

    # we only need the last doc
    current_docs = current_docs[-1:]

    cpu_usage_trend = get_cpu_usage(trend_docs)
    cpu_usage_current = get_cpu_usage(current_docs)

    ram_usage_trend = get_ram_usage(trend_docs)
    ram_usage_current = get_ram_usage(current_docs)

    data_frames = [
        (cpu_usage_trend, "cpu"),
        (cpu_usage_current, "cpu_latest"),
        (ram_usage_trend, "ram"),
        (ram_usage_current, "ram_latest")
    ]

    for frame, name in data_frames:
        frame.to_csv(f"{name}.csv")


if __name__ == '__main__':
    main()
