import * as R from "rambda"

export function cleanEmpty(val: any): any {
    if (val === false) {
        return val //R.isEmpty(false) returns true (strangely)
    }
    if (val instanceof  Date) {
        return val // Dates are objects
    }
    if (R.isNil(val) || R.isEmpty(val)) {
        return null
    }
    if (Array.isArray(val) || typeof val === 'object') {
        let retVal = R.map(cleanEmpty, val)
        retVal = R.filter((v: any) => v !== null, retVal)
        if (R.isEmpty(retVal)) {
            return null
        }
        return retVal
    }
    return val
}

// Just a pass through to R.path (so we have a symmetric API with getBoolValue)
export function getValue(path: R.Path, obj: any): any {
    return R.path(path, obj)
}

export function setValue<T extends object>(path: R.Path, val: any, obj: T): T {
    return cleanEmpty(R.assocPath(path,val,obj))
}