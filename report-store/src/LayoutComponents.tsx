import React, {FunctionComponent, PropsWithChildren} from "react";
import {Box} from "@mui/material";

export function Header<P={}>(props:PropsWithChildren<P>) {
    return (
        <Box sx={{
            flex: "0 0 auto",
            p: 0,
            borderBottom: 1,
            borderWidth: 1,
            borderColor: "grey.200"
        }}>
            {props.children}
        </Box>
    )
}

export function MainContent<P={}>(props:PropsWithChildren<P>){
    return (
        <Box sx={{
            flex: "1 1 auto",
            overflow: "auto",
        }}>
            {props.children}
        </Box>
    )
}
