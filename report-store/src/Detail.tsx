import React from "react";

import {useMatch} from "@tanstack/react-location";

import {Box} from "@mui/material";

export function Detail() {

    const match = useMatch()
    const routeId = match.route.id
    const params = match.params

    return (<div>
        <Box>This is the details page</Box>
        <Box>The match object</Box>
        <pre>
                   {
                       JSON.stringify(params, null, 2)
                   }
        </pre>
    </div>)
}
