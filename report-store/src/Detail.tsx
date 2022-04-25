import React from "react";

import ky from "ky"
import * as R from "rambda"
import {Outlet, useMatch, useMatches, useMatchRoute, useNavigate} from "@tanstack/react-location";

import {Box, Link, Stack, Switch, SxProps, Theme, Typography} from "@mui/material";
import {useQuery, UseQueryResult} from "react-query";

import {getValue, toUtcDate} from "./utils";
import {Header, MainContent} from "./LayoutComponents";
import ReactJson from "react-json-view";

function getReport(reportName: string): Promise<any> {
    return ky.get(`/api/report/${reportName}`).json()
}

const PROP_GRID:SxProps = {p: 1, display: "grid", gridTemplateColumns: "20em 1fr", rowGap: "0.5em"}

const PROP_VALUE_STYLE = {
    fontFamily: "monospace",
    fontSize: (theme:Theme)=> theme.typography.fontSize * 1.4,
}

export function Detail() {
    const match = useMatch()
    const navigate = useNavigate()
    const matches = useMatches()


    let isParsedView = true
    let name: string | null
    if (matches.length === 2) {
        const lastMatch = matches[1]
        name = getValue("params.name", lastMatch)
        if (getValue("route.meta.view", lastMatch) === "raw") {
            isParsedView = false
        }
    }

    const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        if (isParsedView) {
            navigate({to: `./raw/${name}`, replace: true})
        } else {
            navigate({to: `./${name}`, replace: true})
        }
    };

    return (
        <>
            <Header>
                <Stack direction="row" spacing={1} sx={{pl: 2}} alignItems="center">
                    <Typography>Show</Typography>
                    <Typography sx={{color: isParsedView ? "text.primary" : "text.disabled"}}>Parsed</Typography>
                    <Switch
                        checked={!isParsedView}
                        onChange={handleChange}
                        inputProps={{"aria-label": "controlled"}}
                    />
                    <Typography sx={{color: isParsedView ? "text.disabled" : "text.primary"}}>Raw</Typography>
                </Stack>
            </Header>
            <MainContent>
                <Outlet/>
            </MainContent>
        </>
    )
}

export function RawDetail() {
    const {
        data: report,
        reportName
    } = useReportWithName()


    return (
        <>
            <ReactJson src={report} collapsed={2}/>
        </>
    )
}

export function ParsedDetail() {
    const {
        data: report,
        reportName,
        //error, isError, isSuccess, isLoading
    } = useReportWithName()

    const parameters = getValue("context.parameters", report, [])
    const exportParameters = getValue("context.argo.exports.parameters", report, [])
    const resultsData = getValue("results.data", report)
    const resultsMeasurements: MeasurementsData = getValue("results.measurements", report) ?? {}

    const labels = getValue("raw.metadata.labels", report)

    return (<Box sx={{p: 1}}>
        <WorkflowUrl report={report}/>
        <h1>Dates</h1>
        <Box sx={{p: 2}}>
            <Box sx={PROP_GRID}>
                <Box>Creation</Box>
                <Box>{toUtcDate(getValue("context.argo.creationTimestamp", report))} (UTC)</Box>
                <Box>Start</Box>
                <Box>{toUtcDate(getValue("context.argo.startTimestamp", report))} (UTC)</Box>
            </Box>

        </Box>
        <Artifacts artifacts={getValue("context.argo.exports.artifacts", report)} reportName={reportName}/>
        <Labels labels={labels} name="Labels (from raw)"></Labels>
        <Params parameters={parameters} name="Parameters"/>
        <Params parameters={exportParameters} name="Export Parameters"/>
        <Measurements measurements={resultsMeasurements}/>

    </Box>)
}

type ArtifactsProps = {
    reportName: string
    artifacts?: ArtifactDef[] | null
}


function Artifacts(props: ArtifactsProps) {
    if (!props.artifacts || props.artifacts.length === 0) {
        return null
    }
    return (
        <Box sx={{p: 1}}>
            <h1>Artifacts</h1>
            {R.map(a=><Artifact key={a.name} artifactName={a.name} reportName={props.reportName}/>, props.artifacts)}
        </Box>
    )
}

type ArtifactDef = {
    name: string

}

type ArtifactProps = {
    artifactName: string,
    reportName: string,
    key?: string | number

}


function Artifact(props: ArtifactProps) {
    return (
        <Box sx={{p: 1}} key={props.artifactName}>
            <Link href={`/api/artifact/${props.reportName}/${props.artifactName}`} underline="hover" target="_blank" rel="noopener noreferrer">
                {props.artifactName}
            </Link>
        </Box>
    )

}

type ParamProps = {
    name: string
    value: string
    key?: string | number
}

function Param(props: ParamProps) {
    return (<>
        <Box>{props.name}</Box>
        <Box sx={PROP_VALUE_STYLE}>{props.value}</Box>
    </>)
}

type ParamsProps = {
    name?: string
    parameters?: ParamProps[] | null
}

function Params(props: ParamsProps) {
    const parameters = props.parameters
    const name = props.name ?? "Parameters"

    if (!parameters || parameters.length === 0) {
        return null
    }

    return (
        <Box sx={{px: 2}}>
            <h1>{name}</h1>
            <Box sx={PROP_GRID}>
                {R.map((param) => <Param key={param.name} {...param}/>, parameters)}
            </Box>
        </Box>
    )
}

type LabelsProps = {
    name?: string
    labels: { [idx: string]: string }
}


function Labels(props: LabelsProps) {
    const name = props.name ?? "Labels"
    const labels = props.labels

    if (!labels ) {
        return null
    }
    const kvLabels = R.toPairs(labels)

    return (
        <Box sx={{px: 2}}>
            <h1>{name}</h1>
            <Box sx={PROP_GRID}>
                {
                    R.map(([k, v]:[string,string]) => <Param key={k} name={k} value={v}/>)(kvLabels)
                }
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
            <Box sx={PROP_VALUE_STYLE}>{props.value}</Box>
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
            R.map(([k, v]: [string, number]) => <MeasurementValue key={k} name={k} value={v}/>)
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


// hook that retrieves the report with the name take from {params.name} inside a match
function useReportWithName<ReportType = any>(): UseQueryResult<ReportType> &{reportName: string}{
    const match = useMatch()
    return {
        ...useQuery<any>(["search-config"], () => getReport(match.params.name), {retry: false}),
        reportName: match.params.name
    }
}
