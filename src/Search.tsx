import {useSearch, useNavigate} from "@tanstack/react-location";
import Box from "@mui/material/Box";
import TextField, {TextFieldClasses} from "@mui/material/TextField"

import React, {KeyboardEventHandler, useState} from "react"
import {ResultBrowserLocation, SearchParams} from "./location";


export function Search() {
    const search = useSearch<ResultBrowserLocation>()

    console.log("Search is", search)

    const [value, setValue] = useState<{ [key: string]: string }>(search?.labels??{});
    const navigate = useNavigate()

    const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        console.log(event)
        let val = event.target.value
        setValue({p1: val})

    };

    const onKeyDown: (label: string) => KeyboardEventHandler<HTMLDivElement> = (label: string) => (e) => {
        if (e.key === "Enter") {
            console.log("From on key down", e, value)

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

    return (<div>
        <Box>This is the search page</Box>
        <Box>The search params:</Box>
        <TextField
            id="p1"
            label="p1"
            value={value.p1 ?? ""}
            onChange={handleChange}
            onKeyDown={onKeyDown("p1")}
            variant="standard"
        />

        <pre>
            {JSON.stringify(search, null, 2)}
        </pre>

    </div>)
}
