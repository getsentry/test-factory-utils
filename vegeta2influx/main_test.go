package main

import (
	"context"
	"strings"
	"testing"
	"time"

	"github.com/google/go-cmp/cmp"
	influxdb2 "github.com/influxdata/influxdb-client-go/v2"
	"github.com/influxdata/influxdb-client-go/v2/api/write"
)

type fakeWriteApiBlocking struct {
	points []write.Point
}

func (api *fakeWriteApiBlocking) WriteRecord(_ context.Context, _ ...string) error {
	return nil
}

func (api *fakeWriteApiBlocking) WritePoint(_ context.Context, points ...*write.Point) error {
	for _, point := range points {
		if point != nil {
			api.points = append(api.points, *point)
		}
	}
	return nil
}

func TestPushData(t *testing.T) {
	input := `
{"attack":"at1","seq":1,"code":200,"timestamp":"2022-07-04T01:02:03Z","latency":7000,"bytes_out":70,"bytes_in":7,"error":"","body":null}
{"attack":"at1","seq":2,"code":400,"timestamp":"2022-07-04T04:05:06Z","latency":8000,"bytes_out":80,"bytes_in":8,"error":"","body":null}
`
	reader := strings.NewReader(input)
	ctx := context.Background()
	writeApi := fakeWriteApiBlocking{}

	extra := map[string]string{"k1": "v1", "k2": "v2"}

	pushDataInternal(ctx, &writeApi, reader, "m1", extra)

	points := writeApi.points

	if len(points) != 2 {
		t.Errorf("expected 2 points found %d", len(points))
	}

	p1 := influxdb2.NewPoint(
		"m1",
		map[string]string{
			"attack": "at1",
			"status": "200",
			"k1":     "v1",
			"k2":     "v2",
		},
		map[string]any{
			"value":    7000,
			"bytesIn":  7,
			"bytesOut": 70,
		},
		time.Date(2022, 7, 4, 1, 2, 3, 0, time.UTC),
	)

	p2 := influxdb2.NewPoint(
		"m1",
		map[string]string{
			"attack": "at1",
			"status": "400",
			"k1":     "v1",
			"k2":     "v2",
		},
		map[string]any{
			"value":    8000,
			"bytesIn":  8,
			"bytesOut": 80,
		},
		time.Date(2022, 7, 4, 4, 5, 6, 0, time.UTC),
	)

	expectedPoints := []*write.Point{p1, p2}
	for idx := 0; idx < 2; idx++ {
		diff := comparePoint(expectedPoints[idx], &points[idx])
		if diff != "" {
			t.Errorf("Failed to generate correct Point (-expect +actual)\n %s", diff)
		}
	}
}

func comparePoint(p1 *write.Point, p2 *write.Point) string {
	if p1 == nil && p2 == nil {
		return ""
	}
	if p1 == nil || p2 == nil {
		return "comparing nil Point with non nil Point"
	}

	return cmp.Diff(pointToDict(p1), pointToDict(p2))
}

func pointToDict(p *write.Point) map[string]any {
	if p == nil {
		return nil
	}
	retVal := make(map[string]any)

	tagsDict := make(map[string]string)
	for _, v := range p.TagList() {
		tagsDict[v.Key] = v.Value
	}

	valDict := make(map[string]any)
	for _, v := range p.FieldList() {
		valDict[v.Key] = v.Value
	}

	retVal["tags"] = tagsDict
	retVal["values"] = valDict
	retVal["timestamp"] = p.Time()

	return retVal
}
