import {GridColDef, GridValueGetterParams} from "@mui/x-data-grid";
import {getValue} from "./utils";

const  getFromRow = (path:string)=>(params: GridValueGetterParams<any,any>)=> getValue(`row.${path}`, params)
const  getDateFromRow = (path:string)=>(params: GridValueGetterParams<any,any>)=> {
    const dateAsStr = getValue(`row.${path}`, params)
    if (dateAsStr){
        return new Date(dateAsStr)
    } else{
        return null
    }
}

 const  TestColumns : GridColDef[] = [
    {
        field: 'Name',
        width: 300,
        hide: false,
        valueGetter: getFromRow("name"),
        type: "string",
    },
     {
         field: "Start Date",
         width: 300,
         hide: false,
         valueGetter: getDateFromRow("metadata.timeCreated.$date"),
         type: "date",
     }
]



export default TestColumns
