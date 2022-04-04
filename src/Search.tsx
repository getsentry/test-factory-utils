import {useSearch, useNavigate, useMatch} from "@tanstack/react-location";
import Box from "@mui/material/Box";
import TextField, {TextFieldClasses} from "@mui/material/TextField"
import Grid from "@mui/material/Grid"
import AdapterDateFns from '@mui/lab/AdapterDateFns';
import LocalizationProvider from '@mui/lab/LocalizationProvider';
import DateTimePicker from '@mui/lab/DateTimePicker';


import React, {FocusEventHandler, KeyboardEventHandler, useState} from "react"
import {ResultBrowserLocation, SearchParams} from "./location";
import {MultipleSelectChip} from "./FilterSelector"

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
            <MultipleSelectChip/>
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
