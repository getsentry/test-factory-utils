import * as R from "rambda"

export function cleanEmpty(val: any): any {
    if (val === false) {
        return val //R.isEmpty(false) returns true (strangely)
    }
    if (val instanceof Date) {
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

export function clearInvalidPaths(validPaths: string[], val: any): any {
    let paths = new Set<string>()
    const addPaths = (path: string):void =>
    {
        let current = ""
        for (const elm of R.split(".", path)) {
            if (current.length > 0) {
                current = `${current}.${elm}`
            } else {
                current = elm
            }
            paths.add(current)
        }
    }
    R.forEach(addPaths, validPaths)
    clearInvalidPathsInternal("", paths, val)
    return val
}

function clearInvalidPathsInternal(currentPath: string, validPaths: Set<string>, val: any): any {
    for (const key in val) {
        const path = currentPath === "" ? key : `${currentPath}.${key}`
        if (!validPaths.has(path)) {
            delete val[key]
        }
        const child = val[key]
        const childType = R.type(child)
        if (childType === "Object") {
            clearInvalidPathsInternal(path, validPaths, child)
        }
    }
}

// Just a pass through to R.path (so we have a symmetric API with getBoolValue)
export function getValue(path: R.Path, obj: any): any {
    return R.path(path, obj)
}

export function setValue<T extends object>(path: R.Path, val: any, obj: T): T {
    return cleanEmpty(R.assocPath(path, val, obj))
}