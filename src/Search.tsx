import {useSearch, useNavigate, useMatch} from "@tanstack/react-location";
import Box from "@mui/material/Box";
import TextField, {TextFieldClasses} from "@mui/material/TextField"
import Grid from "@mui/material/Grid"
import AdapterDateFns from '@mui/lab/AdapterDateFns';
import LocalizationProvider from '@mui/lab/LocalizationProvider';
import DateTimePicker from '@mui/lab/DateTimePicker';


import React, {FocusEventHandler, KeyboardEventHandler, useState} from "react"
import {ResultBrowserLocation, SearchParams} from "./location";

type SearchActionType = "setLabel" | "setField"

type SearchAction = {
    type: SearchActionType
    fieldName: string
}


interface ControlledTextBoxProps {
    fieldName: string
    label: string
    value: string | null
    setValue: (val: string | null) => void
}

export function ControlledTextBox(props: ControlledTextBoxProps) {
    const [value, setValue] = useState<string | null>(props.value);

    function handleChange(event: React.ChangeEvent<HTMLInputElement>): void {
        console.log(event)
        let val = event.target.value
        setValue(val)
    }

    function onKeyDown(e: React.KeyboardEvent<HTMLDivElement>): void {
        if (e.key === "Enter") {
            props.setValue(value)
        }
    }

    return (<TextField
        id={props.fieldName}
        label={props.label}
        value={value}
        onChange={handleChange}
        onKeyDown={onKeyDown}
        onBlur={(e) => props.setValue(value)}
        variant="standard"
    />)
}

interface ControlledRangePickerProps {
    toDate: Date | null;
    fromDate: Date | null;
    setToDate: (val: Date | null) => void;
    setFromDate: (val: Date | null) => void;

}

function ControlledRangePicker(props: ControlledRangePickerProps) {
    return (<Box sx={{p: 2}}>
        <LocalizationProvider dateAdapter={AdapterDateFns}>
            <Grid container columnSpacing={3}>
                <Grid item>
                    <Box sx={{p: 1}}>
                        <DateTimePicker
                            renderInput={(props: any) => <TextField {...props}/>}
                            label="from"
                            value={props.fromDate}
                            onChange={props.setFromDate}
                        />
                    </Box>

                </Grid>
                <Grid item>
                    <Box sx={{p: 1}}>
                        <DateTimePicker
                            renderInput={(props: any) => <TextField {...props}/>}
                            label="to"
                            value={props.toDate}
                            onChange={props.setToDate}
                        />
                    </Box>

                </Grid>
            </Grid>
        </LocalizationProvider>
    </Box>)

}

export function Search() {
    const search = useSearch<ResultBrowserLocation>()
    const navigate = useNavigate()

    const updateLabel = (label: string) => (value: string | null): void => {
        navigate({
            search: (old: SearchParams | null | undefined) => {
                let labels = old?.labels ?? {}
                if (value) {
                    labels[label] = value
                } else{
                    delete labels[label]
                }
                return {...old, labels}
            }
            ,
            replace: true
        })
    }

    const initialVal = (name: string): string => search?.labels?.[name] ?? ""
    const toDate = search?.to ?? null
    const fromDate = search?.from ?? null
    const setToDate = (val: Date | null) => navigate({
        search: (old: SearchParams | null | undefined) => ({...old, to: val??undefined}) ,
        replace: true
    })
    const setFromDate = (val: Date | null) => navigate({
        search: (old: SearchParams | null | undefined) => ({...old, from: val??undefined}),
        replace: true
    })
    return (
        <>
            <Box sx={{p: 2}}>
                <ControlledTextBox fieldName="p11" label="P11 field" value={initialVal("p11")}
                                   setValue={updateLabel("p11")}/>
            </Box>
            <Box sx={{p: 2}}>
                <ControlledTextBox fieldName="p12" label="P12 field" value={initialVal("p12")}
                                   setValue={updateLabel("p12")}/>
            </Box>
            <Box sx={{p: 2}}>
                <ControlledTextBox fieldName="p13" label="P13 field" value={initialVal("p13")}
                                   setValue={updateLabel("p13")}/>
            </Box>
            <Box>
                <ControlledRangePicker {...{toDate, fromDate, setToDate, setFromDate}}/>
            </Box>
            <Box>
                <pre>
                    {JSON.stringify(search, null, 2)}
                </pre>
            </Box>
        </>
    )
}

export function SearchOld() {
    const search = useSearch<ResultBrowserLocation>()
    const m = useMatch<ResultBrowserLocation>()


    const [value, setValue] = useState<{ [key: string]: string }>(search?.labels ?? {});
    const navigate = useNavigate()
    const [fromDate, setFromDate] = React.useState<Date | null>(null);
    const [toDate, settoDate] = React.useState<Date | null>(null);

    const handleChange = (label: string) => (event: React.ChangeEvent<HTMLInputElement>) => {
        console.log(event)
        let val = event.target.value
        setValue((old) => ({...old, [label]: val}))
    };

    const onKeyDown: (label: string) => KeyboardEventHandler<HTMLDivElement> = (label: string) => (e) => {
        if (e.key === "Enter") {
            console.log("fromDate on key down", e, value)

            navigate({
                search: (old: SearchParams | null | undefined) => {
                    let labels = old?.labels ?? {}
                    labels[label] = value[label]
                    return {...old, labels}
                }
                ,
                replace: true
            })
        }
    }

    const update: (label: string) => FocusEventHandler<HTMLInputElement> = (label: string) => (e) => {
        navigate({
            search: (old: SearchParams | null | undefined) => {
                let labels = old?.labels ?? {}
                labels[label] = value[label]
                return {...old, labels}
            }
            ,
            replace: true
        })

    }

    return (<div>
        <Box>This is the search page</Box>

        <Box>The search params:</Box>
        <Box sx={{p: 2}}>
            <TextField
                id="p1"
                label="p1"
                value={value.p1 ?? ""}
                onChange={handleChange("p1")}
                onKeyDown={onKeyDown("p1")}
                onBlur={update("p1")}
                variant="standard"
            />
        </Box>
        <Box sx={{p: 2}}>
            <TextField
                id="p2"
                label="p2"
                value={value.p2 ?? ""}
                onChange={handleChange("p2")}
                onKeyDown={onKeyDown("p2")}
                onBlur={update("p2")}
                variant="standard"
            />
        </Box>
        <RangePickerOld {...{toDate, fromDate, settoDate, setFromDate}}/>
        <pre>
            {JSON.stringify(search, null, 2)}
        </pre>

    </div>)
}


type SetStateOld = React.Dispatch<React.SetStateAction<Date | null>>


interface RangePickerPropsOld {
    toDate: Date | null;
    fromDate: Date | null;
    settoDate: SetStateOld;
    setFromDate: SetStateOld;
}

function RangePickerOld(props: RangePickerPropsOld) {

    return (<Box sx={{p: 2}}>
        <LocalizationProvider dateAdapter={AdapterDateFns}>
            <Grid container columnSpacing={3}>
                <Grid item>
                    <Box sx={{p: 1}}>
                        <DateTimePicker
                            renderInput={(props: any) => <TextField {...props}/>}
                            label="fromDate"
                            value={props.fromDate}
                            onChange={props.setFromDate}
                        />
                    </Box>

                </Grid>
                <Grid item>
                    <Box sx={{p: 1}}>
                        <DateTimePicker
                            renderInput={(props: any) => <TextField {...props}/>}
                            label="toDate"
                            value={props.toDate}
                            onChange={props.settoDate}
                        />
                    </Box>

                </Grid>
            </Grid>
        </LocalizationProvider>
    </Box>)

}
