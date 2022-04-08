import {useSearch, useNavigate, useMatch} from "@tanstack/react-location"
import Box from "@mui/material/Box"
import * as R from "rambda"

import React from "react"
import {ResultBrowserLocation, SearchParams} from "./location"
import {MultipleSelectChip} from "./FilterSelector"
import {getValue, setValue} from "./utils"
import {ControlledBooleanChoice, ControlledTextBox, ControlledRangePicker} from "./SearchComponents"
import {FilterDef} from "./searchData";


export function Search() {
    const search = useSearch<ResultBrowserLocation>()
    const navigate = useNavigate()

    const updatePath = (path: R.Path) => (value: any): void => {
        navigate({
            search: (old: SearchParams | null | undefined) => {
                return setValue(path, value, old ?? {})
            },
            replace: true
        })
    }

    const myFilters: FiltersProps = {
        filters: [
            {
                kind: "Boolean",
                fieldPath: "a.b.c",
                fieldName: "abc",
            },
            {
                kind: "String",
                fieldPath: "x.y",
                fieldName: "xy",
            },
            {
                kind: "String",
                fieldPath: "x.y.sdfs",
                fieldName: "xxssy",
            },
            {
                kind: "String",
                fieldPath: "x.y.s",
                fieldName: "Hello",
            },
            {
                kind: "String",
                fieldPath: "x.ysfd",
                fieldName: "xyz",
            }
        ]
    }

    return (
        <>
            <MultipleSelectChip/>
            <Box sx={{p: 2}}>
                <ControlledTextBox id="p11" label="P11 field" value={getValue("labels.p11", search)}
                                   setValue={updatePath("labels.p11")}/>
            </Box>
            <Box sx={{p: 2}}>
                <ControlledTextBox id="p12" label="P12 field" value={getValue("labels.p12", search)}
                                   setValue={updatePath("labels.p12")}/>
            </Box>
            <Box sx={{p: 2}}>
                <ControlledTextBox id="p13" label="P13 field" value={getValue("labels.p13", search)}
                                   setValue={updatePath("labels.p13")}/>
            </Box>
            <Box>
                <ControlledRangePicker {...{
                    label: "date range",
                    toDate: getValue("to", search),
                    fromDate: getValue("from", search),
                    setToDate: updatePath("to"),
                    setFromDate: updatePath("from")
                }}/>
            </Box>
            <Box>
                <ControlledBooleanChoice id="theBool" label="The boolean"
                                         value={getValue("labels.theBool", search)}
                                         setValue={updatePath("labels.theBool")}/>
            </Box>
            <Box>
                <pre>
                    {JSON.stringify(search, null, 2)}
                </pre>
            </Box>
            <Box>
                <Filters {...myFilters}/>
            </Box>
        </>
    )
}

export interface FiltersProps {
    filters: FilterDef[]
}

function Filters(props: FiltersProps) {
    const toFilter = (filter: FilterDef) => {
        switch (filter.kind) {
            case "Boolean":
                return <ControlledBooleanChoice id={filter.fieldPath} label={filter.fieldName} value={false}
                                                setValue={() => {
                                                }}/>
            case "String":
                return <ControlledTextBox id={filter.fieldPath} label={filter.fieldName} value={""} setValue={() => {
                }}/>
            case "DateRange":
                return <ControlledRangePicker label={filter.fieldName} toDate={null} fromDate={null} setToDate={() => {
                }} setFromDate={() => {
                }}/>
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