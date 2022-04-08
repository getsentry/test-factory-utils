import {useSearch, useNavigate, useMatch} from "@tanstack/react-location";
import Box from "@mui/material/Box";
import TextField, {TextFieldClasses} from "@mui/material/TextField"
import Grid from "@mui/material/Grid"
import AdapterDateFns from '@mui/lab/AdapterDateFns';
import LocalizationProvider from '@mui/lab/LocalizationProvider';
import DateTimePicker from '@mui/lab/DateTimePicker';
import FormControlLabel from '@mui/material/FormControlLabel';
import FormControl from '@mui/material/FormControl';
import Radio from '@mui/material/Radio';
import RadioGroup from '@mui/material/RadioGroup';
import FormLabel from '@mui/material/FormLabel';
import * as R from "rambda"

import React, {FocusEventHandler, KeyboardEventHandler, useState} from "react"
import {ResultBrowserLocation, SearchParams} from "./location";
import {MultipleSelectChip} from "./FilterSelector"
import {getValue, setValue} from "./utils";

type SearchActionType = "setLabel" | "setField"

type SearchAction = {
    type: SearchActionType
    fieldName: string
}

interface ControlledBooleanChoiceProps {
    fieldName: string
    label: string
    value?: boolean | string | undefined | null
    setValue: (val: boolean | null | undefined) => void
}

export function ControlledBooleanChoice(props: ControlledBooleanChoiceProps) {
    const toVal = (val: boolean | string | null | undefined) => {
        //val === true ? "yes" : val === false ? "no" : "any"
        switch (val) {
            case "true":
            case "yes":
            case true:
                return "yes"
            case "false":
            case "no":
            case false:
                return "no"
            default:
                return "any"
        }
    }

    const setVal = (event: React.ChangeEvent<HTMLInputElement>) => {
        switch (event.target.value) {
            case "yes":
                props.setValue(true)
                break
            case "no":
                props.setValue(false)
                break
            default:
                props.setValue(null)
        }
    }
    return <FormControl>
        <RadioGroup
            aria-labelledby={`${props.fieldName}`}
            name={`${props.fieldName}`}
            value={toVal(props.value)}
            onChange={setVal}
        >
            <Grid container>
                <Grid item>
                    <FormLabel sx={{p: 2}} id={`${props.fieldName}`}>{props.label}</FormLabel>
                </Grid>
                <Grid item>
                    <FormControlLabel value="yes" control={<Radio/>} label="Yes"/>
                </Grid>
                <Grid item>
                    <FormControlLabel value="no" control={<Radio/>} label="No"/>
                </Grid>
                <Grid item>
                    <FormControlLabel value="any" control={<Radio/>} label="Any"/>
                </Grid>
            </Grid>
        </RadioGroup>
    </FormControl>
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
    toDate: Date | null
    fromDate: Date | null
    setToDate: (val: Date | null) => void
    setFromDate: (val: Date | null) => void

}

function ControlledRangePicker(props: ControlledRangePickerProps) {
    //override undefined (otherwise DateTimePicker sets it to now)
    const fromDate = props.fromDate === undefined ? null : props.fromDate
    const toDate = props.toDate === undefined ? null : props.toDate

    return (<Box sx={{p: 2}}>
        <LocalizationProvider dateAdapter={AdapterDateFns}>
            <Grid container columnSpacing={3}>
                <Grid item>
                    <Box sx={{p: 1}}>
                        <DateTimePicker
                            renderInput={(props: any) => <TextField {...props}/>}
                            label="from"
                            value={fromDate}
                            onChange={props.setFromDate}
                        />
                    </Box>

                </Grid>
                <Grid item>
                    <Box sx={{p: 1}}>
                        <DateTimePicker
                            renderInput={(props: any) => <TextField {...props}/>}
                            label="to"
                            value={toDate}
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

    const updatePath = (path: R.Path) => (value: any): void => {
        navigate({
            search: (old: SearchParams | null | undefined) => {
                return setValue(path, value, old ?? {})
            },
            replace: true
        })
    }
    return (
        <>
            <MultipleSelectChip/>
            <Box sx={{p: 2}}>
                <ControlledTextBox fieldName="p11" label="P11 field" value={getValue("labels.p11", search)}
                                   setValue={updatePath("labels.p11")}/>
            </Box>
            <Box sx={{p: 2}}>
                <ControlledTextBox fieldName="p12" label="P12 field" value={getValue("labels.p12", search)}
                                   setValue={updatePath("labels.p12")}/>
            </Box>
            <Box sx={{p: 2}}>
                <ControlledTextBox fieldName="p13" label="P13 field" value={getValue("labels.p13", search)}
                                   setValue={updatePath("labels.p13")}/>
            </Box>
            <Box>
                <ControlledRangePicker {...{
                    toDate: getValue("to", search),
                    fromDate: getValue("from", search),
                    setToDate: updatePath("to"),
                    setFromDate: updatePath("from")
                }}/>
            </Box>
            <Box>
                <ControlledBooleanChoice fieldName="theBool" label="The boolean"
                                         value={getValue("labels.theBool", search)}
                                         setValue={updatePath("labels.theBool")}/>
            </Box>
            <Box>
                <pre>
                    {JSON.stringify(search, null, 2)}
                </pre>
            </Box>
        </>
    )
}
