import pandas as pd
import datapane as dp


def main():
    df = pd.read_csv('https://covid.ourworldindata.org/data/vaccinations/vaccinations-by-manufacturer.csv', parse_dates=['date'])
    df = df.groupby(['vaccine', 'date'])['total_vaccinations'].sum().tail(1000).reset_index()
    report = dp.Report(
        dp.Table(df)
    )
    report.save(path='report.html', open=True)



if __name__ == '__main__':
    main()
