import React from "react"
import {Link} from "@tanstack/react-location"

import {GridRenderCellParams} from "@mui/x-data-grid"


export function linkRenderer(params: GridRenderCellParams<string>) {
    const name = params.value ?? ""
    const url = `./detail/${name}`
    return <Link to={url}> {name} </Link>
}

