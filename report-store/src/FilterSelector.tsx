import * as React from 'react';

import {Theme, useTheme} from '@mui/material/styles';
import {
    Box, OutlinedInput, InputLabel, MenuItem,
    FormControl, Select, SelectChangeEvent, Chip
} from '@mui/material';

import {FilterDef, SearchFiltersDef} from "./searchData";

const ITEM_HEIGHT = 48;
const ITEM_PADDING_TOP = 8;
const MenuProps = {
    PaperProps: {
        style: {
            maxHeight: ITEM_HEIGHT * 4.5 + ITEM_PADDING_TOP,
            width: 250,
        },
    },
};


function getStyles(id: string, selectedIds: readonly string[], theme: Theme) {
    return {
        fontWeight:
            selectedIds.indexOf(id) === -1
                ? theme.typography.fontWeightRegular
                : theme.typography.fontWeightBold,
    };
}

export type FilterListProps = {
    selectedIds: string[]
} & Partial<SearchFiltersDef>

export function FilterList(props: FilterListProps) {
    const theme = useTheme();
    const [filters, setFilters] = React.useState<string[]>([]);

    const handleChange = (event: SelectChangeEvent<string[]>) => {
        const {
            target: {value},
        } = event;
        console.log(value)
        setFilters(
            // On autofill we get a string field value.
            typeof value === 'string' ? value.split(',') : value,
        );
    };

    return (
        <div>
            <FormControl sx={{m: 1, width: 300}}>
                <InputLabel id="filters-list-label">Filters</InputLabel>
                <Select
                    labelId="filters-list-label"
                    id="filters-list"
                    multiple
                    value={filters}
                    onChange={handleChange}
                    input={<OutlinedInput id="select-filters-list" label="Chipo"/>}
                    renderValue={(selected) => (
                        <Box sx={{display: 'flex', flexWrap: 'wrap', gap: 0.5}}>
                            {selected.map((value) => (
                                <Chip key={value} label={value}/>
                            ))}
                        </Box>
                    )}
                    MenuProps={MenuProps}
                >
                    {props.filters && props.filters.map((filter: FilterDef) => (
                        <MenuItem
                            key={filter.fieldName}
                            value={filter.id}
                            style={getStyles(filter.id, filters, theme)}
                        >
                            {filter.fieldName}
                        </MenuItem>
                    ))}
                </Select>
            </FormControl>
        </div>
    );
}
