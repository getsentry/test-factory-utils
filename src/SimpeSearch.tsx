import React, {FunctionComponent} from "react"
import {Box} from "@mui/material";
import {ControlledRangePicker} from "./SearchComponents";
import {useNavigate, useSearch} from "@tanstack/react-location";
import {ResultBrowserLocation} from "./location";
import * as R from "rambda";
import {getValue, setValue} from "./utils";

import Button from '@mui/material/Button';
import {DataGrid} from '@mui/x-data-grid';
import {useDemoData} from '@mui/x-data-grid-generator';


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


export function SimpleSearch() {
    const [checkboxSelection, setCheckboxSelection] = React.useState(true);
    const search = useSearch<ResultBrowserLocation>()
    const navigate = useNavigate()

    const getFromSearch = (path: R.Path): any => getValue(path, search)
    const updatePath = (path: R.Path, val: any): void => {
        console.log("Update path called with ", val)
        navigate({
            search: (old: any) => {
                return setValue(path, val, old ?? {})
            },
            replace: true
        })
    }


    const {data} = useDemoData({
        dataSet: 'Commodity',
        rowLength: 150,
        maxColumns: 7,
    });

    return (
        <>
            <Header>
                <ControlledRangePicker
                    label="Start run"
                    toDate={getFromSearch("to")}
                    fromDate={getFromSearch("from")}
                    setToDate={(val) => updatePath("to", val)}
                    setFromDate={(val) => updatePath("from", val)}
                />
            </Header>
            <MainContent>
                <Box style={{width: '100%', display: 'flex', height: "100%", flexDirection:'column'}}>
                    <Box sx={{flex:"0 0 auto"}}>
                        <Button
                            sx={{mb: 2}}
                            onClick={() => setCheckboxSelection(!checkboxSelection)}
                        >
                            Toggle checkbox selection
                        </Button>
                    </Box>
                    <Box sx={{flex:"1 1 auto"}}>
                        <DataGrid checkboxSelection={checkboxSelection} {...data} />
                    </Box>
                </Box>
            </MainContent>
        </>
    )
}