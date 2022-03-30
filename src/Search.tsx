import {useSearch, useNavigate} from "@tanstack/react-location";
import Box from "@mui/material/Box";
import TextField, {TextFieldClasses} from "@mui/material/TextField"

import React, {KeyboardEventHandler, useState} from "react"
import {ResultBrowserLocation, SearchParams} from "./location";


export function Search() {
    const search = useSearch<ResultBrowserLocation>()

    console.log("Search is", search)
    let initial_p1 = search?.labels?.p1??""
    const [value, setValue] = useState<{p1?:string}>({p1:initial_p1});
    const navigate = useNavigate()

    const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        console.log(event)
        let val = event.target.value
        setValue({p1: val})

    };

    const onKeyDown: KeyboardEventHandler<HTMLDivElement> = (e)=>{
        if ( e.key === "Enter"){
            console.log("From on key down", e,  value)
            navigate({
                search: (old:SearchParams|null|undefined) => ({
                   ...old,labels:{p1: value.p1??""}
                })
                ,
                replace: true
            })
        }
    }

    return (<div>
        <Box>This is the search page</Box>
        <Box>The search params:</Box>
        <TextField
        label="p1"
        value={value.p1??""}
        onChange={handleChange}
        onKeyDown={onKeyDown}
        variant="standard"
        />

        <pre>
            {JSON.stringify(search, null, 2)}
        </pre>

    </div>)
}
