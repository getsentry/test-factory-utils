import {GridRenderCellParams} from "@mui/x-data-grid";
import Link  from "@mui/material/Link";


export function linkRenderer(params: GridRenderCellParams<Date>) {
    return (
        <strong>
            <Link href='#'>{params.value}</Link>
        </strong>)
}

