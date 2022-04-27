import React, { FunctionComponent } from "react"

import * as R from "rambda"
import ky from "ky"
import { useNavigate, useSearch } from "@tanstack/react-location"
import { useQuery } from "react-query"

import { Box, Switch, Stack, Typography } from "@mui/material"
import { DataGrid } from "@mui/x-data-grid"

import TestColumns from "./testColumnDefs"
import { ResultBrowserLocation } from "./location"
import { getValue, setValue } from "./utils"
import { Header, MainContent } from "./LayoutComponents";


function getReports(): Promise<any> {
    return ky.get("/api/reports").json()
}


export function Browse() {
    const search = useSearch<ResultBrowserLocation>()
    const navigate = useNavigate()
    const [compareOn, setCompareOn] = React.useState(false);

    const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        setCompareOn(event.target.checked)
    };
    const getFromSearch = (path: R.Path): any => getValue(path, search)
    const updatePath = (path: R.Path, val: any): void => {
        navigate({
            search: (old: any) => {
                return setValue(path, val, old ?? {})
            },
            replace: true
        })
    }

    const {
        data: reports,
        error,
        isError,
        isSuccess,
        isLoading
    } = useQuery<any>(["reports"], getReports, { retry: false })


    return (
        <>
            <Header>
                <Stack direction="row" spacing={1} sx={{ pl: 2 }} alignItems="center">
                    <Typography>Compare</Typography>
                    <Typography sx={{ color: compareOn ? "text.disabled" : "text.primary" }}>Off</Typography>
                    <Switch
                        checked={compareOn}
                        onChange={handleChange}
                        inputProps={{ "aria-label": "controlled" }}
                    />
                    <Typography sx={{ color: compareOn ? "text.primary" : "text.disabled" }}>On</Typography>
                </Stack>

            </Header>
            <MainContent>
                <DataGrid
                    checkboxSelection={compareOn}
                    columns={TestColumns}
                    getRowId={(row) => getValue("name", row)!}
                    rows={isSuccess ? reports : []}
                    initialState={{
                        pagination: {
                            pageSize: 25,
                        },
                    }}
                />
            </MainContent>
        </>
    )
}
