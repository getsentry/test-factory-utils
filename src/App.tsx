import './App.css';
import Button from "@mui/material/Button"
import {useQuery} from "react-query";
import ky from "ky"
import {Route, Outlet, ReactLocation, Router, useSearch, useMatch, MakeGenerics} from "@tanstack/react-location"
import {Box} from "@mui/material";
import {Search} from "./Search";
import {ResultBrowserLocation} from "./location";

function getT1(): Promise<any> {
    return ky.get("/mock/t1.json").json()
}


const location = new ReactLocation<ResultBrowserLocation>()


function App() {
    const {isLoading, isError, data, error} = useQuery('t1', getT1)

    const routes: Route[] = [
        {
            //The search root
            path: "/search",
            element: <Search/>,
            loader: ()=>(
                {
                    x: 22,
                    y: 44,
                }
            )
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
    console.log(data)
    return (
        <Router location={location} routes={routes}>
            <div className="App">
                <header className="App-header">
                    <div>
                        <Button variant="contained">Hello Button</Button>
                        <pre>
                            {
                                JSON.stringify(data, null, 2)
                            }
                    </pre>

                    </div>
                    <Outlet/>
                </header>
            </div>
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