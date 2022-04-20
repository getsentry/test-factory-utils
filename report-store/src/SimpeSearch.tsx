import React, {FunctionComponent} from "react"
import {Box} from "@mui/material";
import {ControlledRangePicker} from "./SearchComponents";
import {useNavigate, useSearch} from "@tanstack/react-location";
import {ResultBrowserLocation} from "./location";
import Switch from '@mui/material/Switch';
import * as R from "rambda";
import {getValue, setValue} from "./utils";
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
//import Button from '@mui/material/Button';
import {DataGrid, GridColDef} from '@mui/x-data-grid';
//TODO remove the generator once we have data
import {useDemoData} from '@mui/x-data-grid-generator';
import ky from "ky";
import {useQuery} from "react-query";
import {SearchFiltersDef} from "./searchData";
import TestColumns from "./testColumnDefs";


const Header: FunctionComponent<{}> = (props) => (
    <Box sx={{
        flex: "0 0 auto",
        p: 0,
        borderBottom: 1,
        borderWidth: 1,
        borderColor: 'grey.200'
    }}>
        {props.children}
    </Box>
)

const MainContent: FunctionComponent<{}> = (props) => (
    <Box sx={{
        flex: "1 1 auto",
        overflow: "auto",
    }}>
        {props.children}
    </Box>
)

function getReports(): Promise<any> {
    return ky.get("/api/reports").json()
}


export function SimpleSearch() {
    const search = useSearch<ResultBrowserLocation>()
    const navigate = useNavigate()
    const [compareOn, setCompareOn] = React.useState(false);

    const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        setCompareOn(event.target.checked);
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
    } = useQuery<any>(["search-config"], getReports, {retry: false})


    // const {data} = useDemoData({
    //     dataSet: 'Commodity',
    //     rowLength: 150,
    //     maxColumns: 20,
    //     editable: true,
    // });

    const columns: GridColDef[] =[
        {
            field: 'name',
            width: 300,
           // hide: false,
            valueGetter: (params)=>getValue("row.name", params)
        }
    ]

    return (
        <>

            {/*<Header>*/}
            {/*    <ControlledRangePicker*/}
            {/*        label="Start run"*/}
            {/*        toDate={getFromSearch("to")}*/}
            {/*        fromDate={getFromSearch("from")}*/}
            {/*        setToDate={(val) => updatePath("to", val)}*/}
            {/*        setFromDate={(val) => updatePath("from", val)}*/}
            {/*    />*/}
            {/*</Header>*/}
            <MainContent>
                <Box style={{width: '100%', display: 'flex', height: "100%", flexDirection: 'column'}}>
                    <Box sx={{flex: "0 0 auto"}}>

                        <Stack direction="row" spacing={1}  sx={{pl:2}} alignItems="center">
                            <Typography>Compare</Typography>
                            <Typography sx={{color: compareOn ? "text.disabled": "text.primary"}}  >Off</Typography>
                            <Switch
                                checked={compareOn}
                                onChange={handleChange}
                                inputProps={{ 'aria-label': 'controlled' }}
                            />
                            <Typography sx={{color: compareOn ? "text.primary": "text.disabled"}}>On</Typography>
                        </Stack>
                    </Box>
                    <Box sx={{flex: "1 1 auto"}}>
                        <DataGrid checkboxSelection={compareOn} columns={TestColumns} getRowId={(row)=>getValue("name", row)} rows={isSuccess? reports: []} />
                    </Box>
                </Box>
            </MainContent>
        </>
    )
}
