import './App.css';
import Button from "@mui/material/Button"
import { useQuery} from "react-query";
import ky from "ky"

function getT1() : Promise<any>{
    return ky.get("mock/t1.json").json()
}


function App() {
    const  { isLoading, isError, data, error }  = useQuery('t1', getT1)

    return (
            <div className="App">
                <header className="App-header">
                    <p>
                        <Button variant="contained">Hello Button</Button>
                        <pre style={{"textAlign":"left"}}>
                            {
                                JSON.stringify(data, null, 2)
                            }
                    </pre>

                    </p>


                </header>
            </div>
    )
}
export default App;
