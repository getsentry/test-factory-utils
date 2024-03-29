import React from "react"

import * as R from "rambda"
import ky from "ky"
import {useSearch, useNavigate} from "@tanstack/react-location"
import { useQuery} from "react-query";

import {Box, CircularProgress, Alert,Snackbar} from "@mui/material"

import {getValue, setValue} from "./utils"
import {ResultBrowserLocation, SearchParams} from "./location"
import {FilterDef, SearchFiltersDef} from "./searchData";
import {FilterList} from "./FilterSelector"
import {ControlledBooleanChoice, ControlledTextBox, ControlledRangePicker} from "./SearchComponents"

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


export function SearchOld() {
    const search = useSearch<ResultBrowserLocation>()
    const navigate = useNavigate()
    const {
        data: filters,
        error,
        isError,
        isSuccess,
        isLoading
    } = useQuery<SearchFiltersDef>(["search-config"], getSearchConfig, {retry: false})

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
        <Box sx={{p:2}}>
            <OneTimeError isError={isError} message={"Error loading filters"}/>
            <FilterList {...filters } selectedIds={[]} />
            <Box>
                {filters !== undefined && isSuccess && <Filters filters={filters.filters} getValue={getFromSearch} setValue={updatePath}/>}
                {isError && <div>Error configuring the UI</div>}
                {isLoading && <Box sx={{display: 'flex'}}>
                    <CircularProgress/>
                </Box>}
            </Box>
            <Box sx={{p:4}}>
                <pre>
                    {JSON.stringify(search, null, 2)}
                </pre>
            </Box>
        </Box>
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
                return <ControlledBooleanChoice key={filter.id} id={filter.fieldPath} label={filter.fieldName}
                                                value={props.getValue(filter.fieldPath)}
                                                setValue={(val) => props.setValue(filter.fieldPath, val)}
                />
            case "String":
                return <ControlledTextBox  key={filter.id} id={filter.fieldPath} label={filter.fieldName} value={props.getValue(filter.fieldPath)||""}
                                          setValue={(val) => props.setValue(filter.fieldPath, val)}/>
            case "DateRange":
                return <ControlledRangePicker  key={filter.id} label={filter.fieldName} toDate={props.getValue(filter.toPath)} fromDate={props.getValue(filter.fromPath)}
                                              setToDate={(val) => props.setValue(filter.toPath,val)}
                                              setFromDate={(val) => props.setValue(filter.fromPath,val)}/>
            default:
                return <Box key="unsupported">Unuspported filter type</Box>
        }
    }
    const wrapped = (filter: FilterDef) => <Box key={filter.id}>{toFilter(filter)}</Box>
    return (
        <>
            {R.map(wrapped, props.filters)}
        </>
    )

}
