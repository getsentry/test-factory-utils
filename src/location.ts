import {MakeGenerics} from "@tanstack/react-location";

export type RunId = string
export type Labels = { [key:string]: string}

// SearchParams contains all keys used in searches.
// If another search param is needed just add it here, prefer flatter structures (ideally scalar types directly
// added inside the type, they serialize better than deep structures)
export type SearchParams = {
    page?: number,
    pageSize?: number,
    from?: Date,
    to?: Date
    testRuns?: RunId[],
    labels?: Labels
}


// LoaderData contains data loaded by react-location on navigation
export type LoaderData = {
}


// This is the location type, it contains the search structure, the Params and also the loaded
// data managed by react-router
export type  ResultBrowserLocation = MakeGenerics<{
    Params?: {
        testRun?: RunId
    },
    Search: SearchParams,
    LoaderData: LoaderData
}>
