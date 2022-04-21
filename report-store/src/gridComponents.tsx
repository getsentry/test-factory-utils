import {GridRenderCellParams} from "@mui/x-data-grid"
import {Link} from "@tanstack/react-location"

export function linkRenderer(params: GridRenderCellParams<string>) {
    const name = params.value ?? ""
    const url = `./details/${name}`
    return (
        <strong>
            {/*<MuiLink href={url}>{name}</MuiLink>*/}
            <Link to ={url}> {name} </Link>
        </strong>)
}

