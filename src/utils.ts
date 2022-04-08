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


// Just a pass through to R.path (so we have a symmetric API with getBoolValue)
export function getValue(path:R.Path, val: any):any{
    return R.path(path, val)
}

export function getBoolValue(path:R.Path, val:any):boolean|null{
    const v = R.path(path,val)
    switch (v) {
        case "true":
        case true:
            return true
        case "false":
        case false:
            return false
        default:
            return null
    }

}