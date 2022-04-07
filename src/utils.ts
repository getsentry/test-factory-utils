import * as R from "rambda"

export function cleanEmpty(val: any): any {
    if (R.isNil(val) || R.isEmpty(val)) {
        return null
    }
    if (Array.isArray(val) || typeof val === 'object') {
        let retVal = R.map(cleanEmpty, val)
        retVal = R.filter( (v:any) => v !== null, retVal)
        if (R.isEmpty(retVal)) {
            return null
        }
        return retVal
    }

    return val
}



