import {QueryClient, QueryClientProvider} from "react-query";
import {Route, Outlet, ReactLocation, Router, useSearch, useMatch} from "@tanstack/react-location"

import {Box} from "@mui/material";

import './App.css';
import {Search} from "./Search";
import {SimpleSearch} from "./SimpeSearch";
import {ResultBrowserLocation} from "./location";
import React from "react";


const queryClient = new QueryClient();
const location = new ReactLocation<ResultBrowserLocation>()


function App() {
    const routes: Route[] = [
        {
            //The search root
            path: "/",
            element: <SimpleSearch/>,
        },
        {
            //The search root
            path: "/search",
            element: <Search/>,
        },
        {
            path: "detail/:runId",
            element: <Details/>
        },
        {
            path: "compare",
            element: <Compare/>
        }
    ]
    return (
        <Router location={location} routes={routes}>
            <QueryClientProvider client={queryClient}>
                <Box sx={{
                    display: "flex",
                    flexDirection: "column",
                    height: "100vh",
                    width: "100vw",
                    boxSizing: "bored-box",
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


function Details() {

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

function Compare() {

    const search = useSearch()
    return (<div>
        <div>This is the compare page</div>
        <Box>The search params:</Box>
        <pre>
            {JSON.stringify(search, null, 2)}
        </pre>

    </div>)
}
