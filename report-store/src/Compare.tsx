import React from "react";

import {useSearch} from "@tanstack/react-location";

import {Box} from "@mui/material";

export function Compare() {

    const search = useSearch()
    return (<div>
        <div>This is the compare page</div>
        <Box>The search params:</Box>
        <pre>
            {JSON.stringify(search, null, 2)}
        </pre>

    </div>)
}
