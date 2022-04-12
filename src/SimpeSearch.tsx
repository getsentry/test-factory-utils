import React, {FunctionComponent} from "react"
import {Box} from "@mui/material";
import {ControlledRangePicker} from "./SearchComponents";
import {useNavigate, useSearch} from "@tanstack/react-location";
import {ResultBrowserLocation, SearchParams} from "./location";
import * as R from "rambda";
import {getValue, setValue} from "./utils";



const Header: FunctionComponent<{}> = (props)=>(
    <Box sx={{
        flex: "0 0 auto",
        p:0,
        borderBottom: 1,
        borderWidth: 1,
        borderColor: 'grey.200'
    }}>
        {props.children}
    </Box>
)

const MainContent: FunctionComponent<{}> = (props)=>(
    <Box sx={{
        flex: "1 1 auto",
        overflow: "auto",
    }}>
        {props.children}
    </Box>
)


export function SimpleSearch(){
    const search = useSearch<ResultBrowserLocation>()
    const navigate = useNavigate()

    const getFromSearch = (path: R.Path):any => getValue(path, search)
    const updatePath = (path: R.Path, val:any):void => {
        console.log("Update path called with ", val)
        navigate({
            search: (old: any) => {
                return setValue(path, val, old ?? {})
            },
            replace: true
        })
    }
    return (
        <>
            <Header>
                <ControlledRangePicker
                    label="Start run"
                    toDate={getFromSearch("to")}
                    fromDate={getFromSearch("from")}
                    setToDate={ (val)=>updatePath("to", val)}
                    setFromDate={(val)=>updatePath("from", val)}
                />
            </Header>
            <MainContent>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>x</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
                <div>a</div>
            </MainContent>
        </>
    )
}