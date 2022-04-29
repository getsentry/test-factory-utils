import React from "react";

import ky from "ky"
import * as R from "rambda"
import ReactJson from "react-json-view";
import { Outlet, useMatch, useMatches, useNavigate } from "@tanstack/react-location";

import { Box, Divider, Link, Stack, Switch, SxProps, Theme, Typography } from "@mui/material";

import { getValue, toUtcDate } from "./utils";
import { Header, MainContent } from "./LayoutComponents";

export function getReport(reportName: string): Promise<any> {
    return ky.get(`/api/report/${reportName}`).json()
}

const PROP_GRID: SxProps = { p: 1, display: "grid", gridTemplateColumns: "16em 1fr", rowGap: "0.5em" }

const PROP_VALUE_STYLE = {
    fontFamily: "monospace",
}

export function Detail() {

    const navigate = useNavigate()
    const matches = useMatches()

    let isParsedView = true
    if (matches.length === 2) {
        const lastMatch = matches[1]
        if (getValue("route.meta.view", lastMatch) === "raw") {
            isParsedView = false
        }
    }

    const handleChange = (_event: React.ChangeEvent<HTMLInputElement>) => {
        if (isParsedView) {
            navigate({ to: `./raw`, replace: true })
        } else {
            navigate({ to: `.`, replace: true })
        }
    };

    return (
        <>
            <Header>
                <Stack direction="row" spacing={1} sx={{ pl: 2 }} alignItems="center">
                    <Typography>
                        <Link href="/">
                            &lsaquo;&lsaquo; All reports
                        </Link>
                    </Typography>
                    &nbsp;&nbsp;
                    <Typography>Display:</Typography>
                    <Typography sx={{ color: isParsedView ? "text.primary" : "text.disabled" }}>Parsed</Typography>
                    <Switch
                        checked={!isParsedView}
                        onChange={handleChange}
                        inputProps={{ "aria-label": "controlled" }}
                    />
                    <Typography sx={{ color: isParsedView ? "text.disabled" : "text.primary" }}>Raw</Typography>
                </Stack>
            </Header>
            <MainContent>
                <Outlet />
            </MainContent>
        </>
    )
}

export function RawDetail() {
    const match = useMatch()
    return (
        <>
            <ReactJson src={match.data.report as object} collapsed={2} />
        </>
    )
}

export function ParsedDetail() {

    const match = useMatch()
    const report = match.data.report as object
    const reportName = match.data.reportName as string

    const parameters = getValue("context.parameters", report, [])
    const exportParameters = getValue("context.argo.exports.parameters", report, [])
    const resultsMeasurements: MeasurementsData = getValue("results.measurements", report) ?? {}

    const labels = getValue("metadata.labels", report)

    return (<Box sx={{ p: 1 }}>
        <Typography variant="h3">{reportName}</Typography>
        <br></br>
        <WorkflowInfo report={report} />
        <Labels labels={labels} name="Labels"></Labels>
        <Params parameters={parameters} name="Parameters" />
        <Params parameters={exportParameters} name="Computed Values" />
        <Artifacts artifacts={getValue("context.argo.exports.artifacts", report)} reportName={reportName} />
        <Measurements measurements={resultsMeasurements} />

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
        <Box sx={{ p: 2 }}>
            <h1>Artifacts</h1>
            {R.map(a => <Artifact key={a.name} artifactName={a.name} reportName={props.reportName} />, props.artifacts)}
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
        <Box sx={{ p: 1 }} key={props.artifactName}>
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
        <Box sx={{ px: 2 }}>
            <h1>{name}</h1>
            <Box sx={PROP_GRID}>
                {R.map((param) => <Param key={param.name} {...param} />, parameters)}
            </Box>
        </Box>
    )
}

type LabelsProps = {
    name?: string
    labels: { name: string, value: string }[]
}


function Labels(props: LabelsProps) {
    const name = props.name ?? "Labels"
    const labels = props.labels

    if (!labels) {
        return null
    }

    return (
        <Box sx={{ px: 2 }}>
            <h1>{name}</h1>
            <Box sx={PROP_GRID}>
                {
                    labels.map(l => <Param key={l.name} name={l.name} value={l.value} />)
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
            R.map(([k, v]: [string, number]) => <MeasurementValue key={k} name={k} value={v} />)
        )(values)
    }
    return (
        <Box sx={{ px: 1 }}>
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
            R.map(([k, v]: [string, { [_x: string]: number }]) => <Measurement key={k} name={k} values={v} />)
        )(measurements)
    }

    return <Box sx={{ px: 1 }}>
        <h1>Measurements</h1>
        {toMeasurement(params.measurements)}
    </Box>
}

export function WorkflowInfo(params: { report: any }) {
    const url = getValue("context.argo.workflowUrl", params.report)
    const workflowCreationTimestamp = toUtcDate(getValue("context.argo.creationTimestamp", params.report))
    const workflowStartTimestamp = toUtcDate(getValue("context.argo.startTimestamp", params.report))
    const runStartTimestampStr = getValue("context.run.stageStartTimestamp", params.report)
    const runEndTimestampStr = getValue("context.run.stageEndTimestamp", params.report)

    return url && (
        <Box sx={PROP_GRID}>
            <Box>Workflow URL</Box>
            <Box>
                <Link href={url} underline="hover" target="_blank" rel="noopener noreferrer">
                    {url}
                </Link>
            </Box>
            <Box>Workflow created</Box>
            <Box>{workflowCreationTimestamp} (UTC)</Box>
            <Box>Workflow started</Box>
            <Box>{workflowStartTimestamp} (UTC)</Box>

            {runStartTimestampStr &&
                <>
                    <Box>Run started</Box>
                    <Box>{toUtcDate(runStartTimestampStr)} (UTC)</Box>
                </>
            }
            {runEndTimestampStr &&
                <>
                    <Box>Run finished</Box>
                    <Box>{toUtcDate(runEndTimestampStr)} (UTC)</Box>
                </>
            }
        </Box>
    )
}
