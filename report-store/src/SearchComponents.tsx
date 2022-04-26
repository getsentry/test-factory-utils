import React, {useState} from "react"

import {Box, TextField, Grid, FormControlLabel, Radio, RadioGroup, FormLabel, FormControl} from "@mui/material"

import AdapterDateFns from '@mui/lab/AdapterDateFns'
import LocalizationProvider from '@mui/lab/LocalizationProvider'
import DateTimePicker from '@mui/lab/DateTimePicker'

export interface ControlledBooleanChoiceProps {
    id: string
    label: string
    value?: boolean | string | undefined | null
    setValue: (val: boolean | null | undefined) => void
}

export function ControlledBooleanChoice(props: ControlledBooleanChoiceProps) {
    const toVal = (val: boolean | string | null | undefined) => {
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
            aria-labelledby={`${props.id}`}
            name={`${props.id}`}
            value={toVal(props.value)}
            onChange={setVal}
        >
            <Grid container sx={{"alignItems": "center"}}>
                <Grid item>
                    <FormLabel sx={{p: 2}} id={`${props.id}`}>{props.label}</FormLabel>
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

export interface ControlledTextBoxProps {
    id: string
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
        id={props.id}
        label={props.label}
        value={value}
        onChange={handleChange}
        onKeyDown={onKeyDown}
        onBlur={(e) => props.setValue(value)}
        variant="standard"
    />)
}

export interface ControlledRangePickerProps {
    label: string | null
    toDate: string | null
    fromDate: string | null
    setToDate: (val: string | null) => void
    setFromDate: (val: string | null) => void
}

export function ControlledRangePicker(props: ControlledRangePickerProps) {
    //override undefined (otherwise DateTimePicker sets it to now)
    const [fromDate, setLocalFromDate] = useState<string | null>(props.fromDate ?? null)
    const [toDate, setLocalToDate] = useState<string | null>(props.toDate ?? null)

    const updateFromDate = () => {
        if (fromDate !== props.fromDate) {
            props.setFromDate(fromDate)
        }
    }
    const updateToDate = () => {
        if (
            (toDate !== props.toDate)) {
            props.setToDate(toDate)
        }
    }
    const onBlur = (update: () => void) => (e: any) => update()
    const onKeyDown = (update: () => void) => (e: React.KeyboardEvent<HTMLDivElement>) => {
        if (e.key === "Enter") {
            update()
        }
    }

    return (<Box sx={{p: 2}}>
        <LocalizationProvider dateAdapter={AdapterDateFns}>
            <Grid container sx={{"alignItems": "center", "justifyContent": "center", "columnSpacing": 3}}>
                <Grid item>
                    <FormLabel>{props.label}</FormLabel>
                </Grid>
                <Grid item>
                    <Box sx={{p: 1}}>
                        <DateTimePicker
                            renderInput={(inputProps: any) => <TextField
                                {...inputProps}
                                onBlur={onBlur(updateFromDate)}
                                onKeyDown={onKeyDown(updateFromDate)}
                            />}
                            label="from"
                            value={fromDate}
                            onAccept={props.setFromDate}

                            onChange={(val) => {
                                const vAsString = val !== null ? (val as unknown as Date).toJSON() : null
                                setLocalFromDate(vAsString)
                            }}
                        />
                    </Box>
                </Grid>
                <Grid item>
                    <Box sx={{p: 1}}>
                        <DateTimePicker
                            renderInput={(inputProps: any) => <TextField
                                {...inputProps}
                                onBlur={onBlur(updateToDate)}
                                onKeyDown={onKeyDown(updateToDate)}
                            />}
                            label="to"
                            value={toDate}
                            onAccept={props.setToDate}

                            onChange={(val) => {
                                const vAsString = val !== null ? (val as unknown as Date).toJSON() : null
                                setLocalToDate(vAsString)
                            }}
                        />
                    </Box>
                </Grid>
            </Grid>
        </LocalizationProvider>
    </Box>)
}
