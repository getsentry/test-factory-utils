import {cleanEmpty} from "./utils"

describe("util tests", () => {
    describe("cleanEmpty", () => {
        describe.each([
            {name: "array with null", val: [null, null]},
            {name: "array with undefined", val: [undefined, undefined]},
            {name: "object with null", val: {x: null, y: null}},
            {name: "object with undefined", val: {x: undefined, y: undefined}},
            {name: "empty string", val: ""},
            {name: "null", val: null},
            {name: "undefined", val: undefined},
            {name: "array of empty things", val: [[], [], "", {}]},
            {name: "object with empty things", val: {a: null, b: undefined, c: {}, d: [], e: ""}},
            {name: "complex array", val: [[[]], [{}], [""], [null, undefined]]},
            {name: "complex object", val: {a: {b: {c: {}}}, e: {f: [], g: "", h: undefined}}},
            {name: "complex", val: {a: {x: [null, "", {b: [null, {}, ""]}]}}}
        ])("empty results", (t) => {
            test(`${t.name}`, () => {
                expect(cleanEmpty(t.val)).toBe(null)
            })
        })
    })
    describe("cleans structures with empty results", () => {
        describe.each([
            {name: "array with empty values", val: [1, null, 2, undefined, 3, "", [], {}], expected: [1, 2, 3]},
            {
                name: "object with empty values",
                val: {a: 1, b: null, c: 2, e: undefined, f: 3, g: "", h: [], i: {}},
                expected: {a: 1, c: 2, f: 3}
            },
            {
                name: "complex",
                val: {
                    a: [1, null, [null, [""], "", undefined], 2, 3],
                    aa: {x: {}, y: "", z: [[]]},
                    b: {x: 1, y: 2, z: [1, {d: 4, e: ""}, [5, 6, [], [null, ""]]]},
                    c: "hello"
                },
                expected: {a: [1, 2, 3], b: {x: 1, y: 2, z: [1, {d: 4}, [5, 6]]}, c: "hello"}
            }
        ])("mixed results", (t) => {
            test("is clean", () => {
                expect(cleanEmpty(t.val)).toStrictEqual(t.expected)
            })
        })
    })
    describe.each([
        "a",
        1,
        [1],
        ["hello"],
        {x: 22},
    ])("does not touch non empty data", (val) => {
        test("is unchanged", () => {
            expect(cleanEmpty(val)).toStrictEqual(val)
        })
    })
})
