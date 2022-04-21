import React from "react";

import ky from "ky"
import * as R from "rambda"
import {useMatch} from "@tanstack/react-location";

import {Box} from "@mui/material";
import {useQuery} from "react-query";

import {getValue} from "./utils";

function getReport(reportName:string): Promise<any>{
    return ky.get(`/api/report/${reportName}`).json()
}

type ParamProps ={
    name: string
    value: string
}

function Param(props: ParamProps){
    return (<>
        <Box sx={{p:1}}>{props.name}</Box>
        <Box sx={{p:1}}>{props.value}</Box>
    </>)
}

type ParamsProps = {
    report: any
}
function Params(props: ParamsProps){
    const parameters = getValue<ParamProps[]>("context.parameters", props.report, [])

    if (!parameters || parameters.length === 0){
        return null
    }

    return (
        <Box sx={{p:2}}>
            <h1>Parameters</h1>
            <Box sx={{p:1, display:"grid", gridTemplateColumns:"20em 1fr"}}>
                {R.map((param) => Param(param), parameters)}
            </Box>
        </Box>
    )
}

export function Detail() {

    const match = useMatch()
    const routeId = match.route.id
    const params = match.params

    const {
        data: report,
        error,
        isError,
        isSuccess,
        isLoading
    } = useQuery<any>(["search-config"], ()=>getReport(params.name), {retry: false})

    const parameters = getValue("context.parameters", report, [])


    return (<div>

        <Params report = {report}/>
        <pre>
                   {
                       JSON.stringify(params, null, 2)
                   }
        </pre>
        <pre>
                   {
                       JSON.stringify(report, null, 2)
                   }
        </pre>
    </div>)
}
