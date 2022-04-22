import React from "react";

import ky from "ky"
import * as R from "rambda"
import {useMatch} from "@tanstack/react-location";

import {Box, Link} from "@mui/material";
import {useQuery} from "react-query";

import {getValue, toUtcDate} from "./utils";

function getReport(reportName: string): Promise<any> {
    return ky.get(`/api/report/${reportName}`).json()
}

const PROP_GRID = {p: 1, display: "grid", gridTemplateColumns: "20em 1fr", rowGap: "0.5em"}

type ParamProps = {
    name: string
    value: string
}

function Param(props: ParamProps) {
    return (<>
        <Box>{props.name}</Box>
        <Box>{props.value}</Box>
    </>)
}

type ParamsProps = {
    name?: string
    parameters?: ParamProps[] | null
}

function Params(props: ParamsProps) {
    //const parameters = getValue<ParamProps[]>("context.parameters", props.report, [])

    const parameters = props.parameters
    const name = props.name ?? "Parameters"

    if (!parameters || parameters.length === 0) {
        return null
    }

    return (
        <Box sx={{px: 2}}>
            <h1>{name}</h1>
            <Box sx={PROP_GRID}>
                {R.map((param) => Param(param), parameters)}
            </Box>
        </Box>
    )
}

type MeasurementValueProps = {
    name: string,
    value: number
}

function MeasurementValue(props: MeasurementValueProps) {
    return (
        <>
            <Box>{props.name}</Box>
            <Box>{props.value}</Box>
        </>
    )
}

type ValueDict = { [valName: string]: number }

type MeasurementProps = {
    name: string
    values: ValueDict
}

function Measurement(params: MeasurementProps) {
    const toMeasurementValue = (values: ValueDict) => {
        return R.pipe(
            R.toPairs,
            R.map(([k, v]: [string, number]) => <MeasurementValue name={k} value={v}/>)
        )(values)
    }
    return (
        <Box sx={{px: 1}}>
            <h2>{params.name}</h2>
            <Box sx={PROP_GRID}>
                {toMeasurementValue(params.values)}
            </Box>
        </Box>
    )
}

type MeasurementsData = {
    [metric: string]: { [measurement: string]: number }
}

type MeasurementsProps = {
    measurements: MeasurementsData
}


function Measurements(params: MeasurementsProps) {

    const toMeasurement = (measurements: MeasurementsData) => {
        return R.pipe(
            R.toPairs,
            R.map(([k, v]: [string, { [x: string]: number }]) => <Measurement key={k} name={k} values={v}/>)
        )(measurements)
    }

    return <Box sx={{px: 1}}>
        <h1>Measurements</h1>
        {toMeasurement(params.measurements)}
    </Box>
}

export function WorkflowUrl(params: { report: any }) {
    const url = getValue("context.argo.workflowUrl", params.report)
    return url && (
        <Box sx={{p: 1}}>
            <h1>Workflow Url</h1>
            <Link href={url} underline="hover" target="_blank" rel="noopener noreferrer">
                {url}
            </Link>
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
    } = useQuery<any>(["search-config"], () => getReport(params.name), {retry: false})

    const parameters = getValue("context.parameters", report, [])
    const exportParameters = getValue("context.argo.exports.parameters", report, [])
    const resultsData = getValue("results.data", report)
    const resultsMeasurements: MeasurementsData = getValue("results.measurements", report) ?? {}

    return (<Box sx={{p: 1}}>
        <WorkflowUrl report={report}/>
        <h1>Dates</h1>
        <Box sx={{p: 2}}>
            <Box sx={PROP_GRID}>
                <Box>Creation</Box>
                <Box>{toUtcDate(getValue("context.argo.creationTimestamp",report))} (UTC)</Box>
                <Box>Start</Box>
                <Box>{toUtcDate(getValue("context.argo.startTimestamp",report))} (UTC)</Box>
            </Box>

        </Box>
        <h2>(TODO) context.argo.exports.artifacts</h2>
        <h2>(TODO) metadata.labels (raw.metadata.labels)</h2>
        <Params parameters={parameters} name="Parameters"/>
        <Params parameters={exportParameters} name="Export Parameters"/>
        <Measurements measurements={resultsMeasurements}/>
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
    </Box>)
}
