import {useSearch, useNavigate, useMatch} from "@tanstack/react-location"
import Box from "@mui/material/Box"
import * as R from "rambda"
import ky from "ky"

import React from "react"
import {ResultBrowserLocation, SearchParams} from "./location"
import {FilterList} from "./FilterSelector"
import {getValue, setValue} from "./utils"
import {ControlledBooleanChoice, ControlledTextBox, ControlledRangePicker} from "./SearchComponents"
import {FilterDef, SearchFiltersDef} from "./searchData";
import {useQuery} from "react-query";
import Alert from "@mui/material/Alert";
import Snackbar from '@mui/material/Snackbar';
import CircularProgress from '@mui/material/CircularProgress'

function getSearchConfig(): Promise<SearchFiltersDef> {
    return ky.get("/mock/searchFiltersDef.json").json()
}

type OneTimeErrorProps = {
    isError: boolean,
    message: string,
}

function OneTimeError(props: OneTimeErrorProps) {
    const [errorAck, setErrorAck] = React.useState(false)
    const [open, setOpen] = React.useState(props.isError);

    if (props.isError && !errorAck) {
        setErrorAck(true)
        setOpen(true)
    }
    const closeLoadError = (
        event?: React.SyntheticEvent | Event,
        reason?: string
    ) => {
        if (reason === "clickaway") {
            return
        }

        setOpen(false)
    }

    return (
        <Snackbar open={open} autoHideDuration={6000} onClose={closeLoadError}>
            <Alert onClose={closeLoadError} severity="error" sx={{width: "100%"}}>
                {props.message}
            </Alert>
        </Snackbar>)

}


export function Search() {
    const search = useSearch<ResultBrowserLocation>()
    const navigate = useNavigate()
    const {
        data: filters,
        error,
        isError,
        isSuccess,
        isLoading
    } = useQuery<SearchFiltersDef>(["search-config"], getSearchConfig, {retry: false})
    const [open, setOpen] = React.useState(isError);
    const [errorAck, setErrorAck] = React.useState(false)

    const updatePathOld = (path: R.Path) => (value: any): void => {
        navigate({
            search: (old: SearchParams | null | undefined) => {
                return setValue(path, value, old ?? {})
            },
            replace: true
        })
    }

    const getFromSearch = (path: R.Path):any => getValue(path, search)
    const updatePath = (path: R.Path, val:any):void => {
        navigate({
            search: (old: SearchParams | null | undefined) => {
                return setValue(path, val, old ?? {})
            },
            replace: true
        })
    }

    return (
        <>
            <OneTimeError isError={isError} message={"Error loading filters"}/>
            <FilterList />
            <Box>
                {filters !== undefined && isSuccess && <Filters filters={filters.filters} getValue={getFromSearch} setValue={updatePath}/>}
                {isError && <div>Error configuring the UI</div>}
                {isLoading && <Box sx={{display: 'flex'}}>
                    <CircularProgress/>
                </Box>}
            </Box>
            <Box>
                <pre>
                    {JSON.stringify(search, null, 2)}
                </pre>
            </Box>
        </>
    )
}

export interface FiltersProps {
    filters: FilterDef[]
    getValue: (path: string) => any
    setValue: (path: string, val: any) => void
}

function Filters(props: FiltersProps) {
    const toFilter = (filter: FilterDef) => {
        switch (filter.kind) {
            case "Boolean":
                return <ControlledBooleanChoice id={filter.fieldPath} label={filter.fieldName}
                                                value={props.getValue(filter.fieldPath)}
                                                setValue={(val) => props.setValue(filter.fieldPath, val)}
                />
            case "String":
                return <ControlledTextBox id={filter.fieldPath} label={filter.fieldName} value={props.getValue(filter.fieldPath)}
                                          setValue={(val) => props.setValue(filter.fieldPath, val)}/>
            case "DateRange":
                return <ControlledRangePicker label={filter.fieldName} toDate={props.getValue(filter.toPath)} fromDate={props.getValue(filter.fromPath)}
                                              setToDate={(val) => props.setValue(filter.toPath,val)}
                                              setFromDate={(val) => props.setValue(filter.fromPath,val)}/>
            default:
                return <Box>Unuspported filter type</Box>
        }
    }
    const wrapped = (filter: FilterDef) => <Box>{toFilter(filter)}</Box>
    return (
        <>
            <Box>

            </Box>
            {R.map(wrapped, props.filters)}
        </>
    )

}