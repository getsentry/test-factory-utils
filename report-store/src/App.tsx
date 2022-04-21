import React from "react";

import {QueryClient, QueryClientProvider} from "react-query";
import {Route, Outlet, ReactLocation, Router} from "@tanstack/react-location"

import {Box} from "@mui/material";

import './App.css';
import {Browse} from "./Browse";
import {ResultBrowserLocation} from "./location";
import {Detail} from "./Detail";
import {Compare} from "./Compare";


const queryClient = new QueryClient();
const location = new ReactLocation<ResultBrowserLocation>()


function App() {
    const routes: Route[] = [
        {
            //The search root
            path: "/",
            element: <Browse/>,
        },
        {
            path: "detail/:name",
            element: <Detail/>
        },
        {
            path: "compare",
            element: <Compare/>
        },
    ]
    return (
        <Router location={location} routes={routes} basepath='ui'>
            <QueryClientProvider client={queryClient}>
                <Box sx={{
                    display: "flex",
                    flexDirection: "column",
                    height: "100vh",
                    width: "100vw",
                    boxSizing: "border-box",
                    m:0,
                    p:0,
                }}>
                        <Outlet/>
                </Box>
            </QueryClientProvider>
        </Router>
    )
}

export default App;

