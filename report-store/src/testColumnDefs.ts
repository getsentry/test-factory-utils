import * as R from "rambda"
import {DateTime} from "luxon"

import {GridColDef, GridValueFormatterParams, GridValueGetterParams} from "@mui/x-data-grid";

import {getValue} from "./utils";
import {linkRenderer} from "./gridComponents";

const DateFormatOptions: Intl.DateTimeFormatOptions = {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
}

const getFromRow = (path: string) => (params: GridValueGetterParams<any, any>) => getValue(`row.${path}`, params)
const getDateFromRow = (path: string) => (params: GridValueGetterParams<any, any>) => {
    const dateAsStr = getValue(`row.${path}`, params)
    if (dateAsStr) {
        return new Date(dateAsStr)
    } else {
        return null
    }
}

function dateFormater(params: GridValueFormatterParams<Date>): string | Date {
    if (!params.value) {
        return "-"
    }
    if (!(params.value instanceof Date)) {
        return "invalid"
    }

    const dt = DateTime.fromJSDate(params.value, {zone: "utc"})
    return dt.toLocaleString(DateFormatOptions)
}

function getCommentFromRow(params: GridValueGetterParams) {
    const val = R.pipe(
        getFromRow("context.parameters"),
        R.find((x: any) => x.name === "comment"),
        R.path("value"),
        (v: any) => v ? v : "-",
    )(params)
    return val

}

const TestColumns: GridColDef[] = [
    {
        field: 'Name',
        width: 300,
        hide: false,
        valueGetter: getFromRow("name"),
        renderCell: linkRenderer,
        type: "string",
    },
    {
        field: "Start Date (UTC)",
        width: 200,
        hide: false,
        valueGetter: getDateFromRow("metadata.timeCreated.$date"),
        valueFormatter: dateFormater,
        type: "dateTime",
    },

    {
        field: "Comment",
        flex: 1,
        minWidth: 200,
        hide: false,
        valueGetter: getCommentFromRow,
        type: "string",
    },
]


export default TestColumns
