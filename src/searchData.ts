// TODO RaduW 8.April.2022 find a better name for the module or move all types somewhere else

export type FilterType = "Boolean"|"String"|"DateRange"

export type SingleFieldFilterDef = {
    id: string
    kind: "Boolean"|"String"
    fieldPath: string
    fieldName: string
}

export type DateRangeFilterDef = {
    id: string
    kind: "DateRange"
    fieldName: string
    fromPath: string
    toPath: string
}

export type FilterDef = SingleFieldFilterDef | DateRangeFilterDef

// SearchFiltersDef defines the structure
export type SearchFiltersDef = {
    filters: FilterDef[]
}