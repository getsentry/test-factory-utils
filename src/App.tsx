import ky from "ky"
import {QueryClient, QueryClientProvider, useQuery} from "react-query";
import {Route, Outlet, ReactLocation, Router, useSearch, useMatch, MakeGenerics} from "@tanstack/react-location"

import Button from "@mui/material/Button"
import {Box} from "@mui/material";

import './App.css';
import {Search} from "./Search";
import {ResultBrowserLocation} from "./location";
import React from "react";

const queryClient = new QueryClient();
const location = new ReactLocation<ResultBrowserLocation>()

function getT1(): Promise<any> {
    return ky.get("/mock/t1.json").json()
}

function App() {
    const routes: Route[] = [
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
                <div className="App">
                    <header className="App-header">
                        <Outlet/>
                    </header>
                </div>
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