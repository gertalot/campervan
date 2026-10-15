// Test harness: insert after the production file's imports, before its exported feature.
// The MCP test_feature tool executes the first exported feature it finds.
annotation { "Feature Type Name" : "NV200Validation" }
export const nv200Validation = defineFeature(function(context is Context, id is Id, definition is map)
    precondition {}
    {
        const cases = [
            { "name" : "day55", "layout" : NV200Layout.DAY, "height" : 55, "width" : 107, "length" : 128, "foam" : 10 },
            { "name" : "night55", "layout" : NV200Layout.NIGHT, "height" : 55, "width" : 107, "length" : 128, "foam" : 10 },
            { "name" : "day65", "layout" : NV200Layout.DAY, "height" : 65, "width" : 107, "length" : 128, "foam" : 10 },
            { "name" : "night65", "layout" : NV200Layout.NIGHT, "height" : 65, "width" : 107, "length" : 128, "foam" : 10 },
            { "name" : "nightWider", "layout" : NV200Layout.NIGHT, "height" : 55, "width" : 117, "length" : 128, "foam" : 10 },
            { "name" : "dayLongerA", "layout" : NV200Layout.DAY, "height" : 55, "width" : 107, "length" : 130, "foam" : 10 },
            { "name" : "dayThickerFoam", "layout" : NV200Layout.DAY, "height" : 55, "width" : 107, "length" : 128, "foam" : 12 }
        ];
        for (var c in cases)
        {
            const partId = id + c.name;
            var d = DEFAULTS;
            d.layout = c.layout;
            d.bedHeight = c.height * centimeter;
            d.bedWidth = c.width * centimeter;
            d.seatLength = c.length * centimeter;
            d.foamThickness = c.foam * centimeter;
            nv200Interior(context, partId, d);
            const bodies = qCreatedBy(partId, EntityType.BODY);
            check(size(evaluateQuery(context, qBodyType(bodies, BodyType.SOLID))) == 8,
                c.name ~ ": expected eight separate solids including cabinet");
            check(size(evaluateQuery(context, qBodyType(qSketchFilter(bodies, SketchObject.NO), BodyType.SHEET))) == 0,
                c.name ~ ": cabinet must be solid");
            const h = c.height;
            const t = c.foam;
            const base = h - t;
            const infill = (c.width - 57) / 2;
            const c1 = 2 * c.length - 186;
            checkBlock(context, partId + "baseA", [0, 0, 0], [57, c.length, base]);
            checkBlock(context, partId + "baseD", [0, c.length, 0], [c.width, 186, base]);
            checkBlock(context, partId + "cushionA", [0, 0, base], [57, c.length, h]);
            checkBlock(context, partId + "cushionD", [0, c.length, base], [c.width, 186, h]);
            if (c.layout == NV200Layout.DAY)
            {
                checkBlock(context, partId + "cushionB", [0, 0, h], [t, c.length, h + infill]);
                checkBlock(context, partId + "cushionC1", [t, 186 - t, h], [t + c1, 186, h + infill]);
                checkBlock(context, partId + "cushionC2", [0, c.length, h], [t, 186, h + infill]);
            }
            else
            {
                checkBlock(context, partId + "cushionB", [57, 0, base], [57 + infill, c.length, h]);
                checkBlock(context, partId + "cushionC1", [57 + infill, 0, base], [c.width, c1, h]);
                checkBlock(context, partId + "cushionC2", [57 + infill, c1, base], [c.width, c.length, h]);
                const cushionBodies = qUnion([
                    qCreatedBy(partId + "cushionA", EntityType.BODY), qCreatedBy(partId + "cushionD", EntityType.BODY),
                    qCreatedBy(partId + "cushionB", EntityType.BODY), qCreatedBy(partId + "cushionC1", EntityType.BODY),
                    qCreatedBy(partId + "cushionC2", EntityType.BODY)
                ]);
                const volume = evVolume(context, { "entities" : cushionBodies }) / centimeter ^ 3;
                check(abs(volume - c.width * 186 * t) < 0.001, c.name ~ ": bed volume must fill rectangle");
            }
            const cabinet = qCreatedBy(partId + "cabinet", EntityType.BODY);
            check(abs(evVolume(context, { "entities" : cabinet }) / centimeter ^ 3 -
                (150 - c.width) * (119 + 94) / 2 * 130) < 0.001, c.name ~ ": cabinet volume");
            const cabinetBounds = evBox3d(context, { "topology" : cabinet, "tight" : true });
            check(abs(cabinetBounds.minCorner[2] / millimeter) < 0.001 &&
                abs(cabinetBounds.maxCorner[2] / millimeter - 1300) < 0.001, c.name ~ ": cabinet height");
            const expectedVertices = [vector(c.width, 0, 0), vector(150, 0, 0),
                vector(150, 119, 0), vector(c.width, 94, 0)];
            const vertices = evaluateQuery(context, qOwnedByBody(cabinet, EntityType.VERTEX));
            check(size(vertices) == 8, c.name ~ ": extruded cabinet must have eight vertices");
            for (var expected in expectedVertices)
            {
                var found = false;
                for (var vertex in vertices)
                    if (norm(evVertexPoint(context, { "vertex" : vertex }) / centimeter - expected) < 0.0001)
                        found = true;
                check(found, c.name ~ ": missing cabinet vertex " ~ expected);
            }
            println("PASS " ~ c.name ~ ": 8 solids, exact part bounds/volumes and 1300 mm cabinet");
            opDeleteBodies(context, partId + "cleanup", { "entities" : bodies });
        }
        for (var layout in [NV200Layout.DAY, NV200Layout.NIGHT])
        {
            for (var mode in ["on", "off", "missing"])
            {
                const partId = id + ("cushions" ~ layout ~ mode);
                var d = DEFAULTS;
                d.layout = layout;
                d.showCushions = mode == "missing" ? undefined : mode == "on";
                d.bedHeight = 60 * centimeter;
                d.cabinetHeight = 1200 * millimeter;
                nv200Interior(context, partId, d);
                const expectedCushions = mode == "off" ? 0 : 5;
                const bodies = qCreatedBy(partId, EntityType.BODY);
                check(size(evaluateQuery(context, qBodyType(bodies, BodyType.SOLID))) == 3 + expectedCushions,
                    "Cushion toggle changed the wrong number of parts");
                for (var suffix in ["cushionA", "cushionD", "cushionB", "cushionC1", "cushionC2"])
                    check(size(evaluateQuery(context, qCreatedBy(partId + suffix, EntityType.BODY))) ==
                        (mode == "off" ? 0 : 1), "Cushion toggle failed for " ~ suffix);
                checkBlock(context, partId + "baseA", [0, 0, 0], [57, 128, 50]);
                checkBlock(context, partId + "baseD", [0, 128, 0], [107, 186, 50]);
                const cabinet = qCreatedBy(partId + "cabinet", EntityType.BODY);
                const bounds = evBox3d(context, { "topology" : cabinet, "tight" : true });
                check(norm(bounds.minCorner / millimeter - vector(1070, 0, 0)) < 0.001 &&
                    norm(bounds.maxCorner / millimeter - vector(1500, 1190, 1200)) < 0.001,
                    "Cushion toggle changed cabinet dimensions");
                if (mode != "off")
                {
                    if (layout == NV200Layout.DAY)
                        checkBlock(context, partId + "cushionB", [0, 0, 60], [10, 128, 85]);
                    else
                        checkBlock(context, partId + "cushionB", [57, 0, 50], [82, 128, 60]);
                }
                println("PASS " ~ layout ~ " cushions " ~ mode ~ ": correct parts, layout and edited dimensions");
                opDeleteBodies(context, partId + "cleanup", { "entities" : bodies });
            }
        }
        const p = layoutDimensions(DEFAULTS);
        check(abs(p.aisleWidth / centimeter - 50) < 0.0001, "day aisle must be 50");
        check(abs(p.innerGap / centimeter - 34) < 0.0001, "inner gap must be 34");
        check(abs(p.outerGap / centimeter - 9) < 0.0001, "outer gap must be 9");
        check(abs(p.frontUnbacked / centimeter - 27) < 0.0001, "D front unbacked edge must be 27");
        for (var change in [
            { "key" : "bedHeight", "value" : 10 },
            { "key" : "bedWidth", "value" : 57 },
            { "key" : "cargoWidth", "value" : 100 },
            { "key" : "seatLength", "value" : 90 },
            { "key" : "seatLength", "value" : 150 },
            { "key" : "cabinetOuterLength", "value" : 140 },
            { "key" : "cabinetInnerLength", "value" : 120 }
        ])
        {
            var invalid = DEFAULTS;
            invalid[change.key] = change.value * centimeter;
            check(try silent(layoutDimensions(invalid)) == undefined, "invalid " ~ change.key ~ " was accepted");
        }
        println("PASS clearances and 7 invalid-input cases; all NV200 regression checks passed");
    }, {});

function check(condition is boolean, message is string)
{
    if (!condition)
        throw regenError(message);
}

function checkBlock(context is Context, id is Id, expectedMin is array, expectedMax is array)
{
    const body = qCreatedBy(id, EntityType.BODY);
    check(size(evaluateQuery(context, body)) == 1, "expected one body for " ~ id);
    const bounds = evBox3d(context, { "topology" : body, "tight" : true });
    var expectedVolume = 1;
    for (var axis = 0; axis < 3; axis += 1)
    {
        check(abs(bounds.minCorner[axis] / centimeter - expectedMin[axis]) < 0.0001,
            "min bound mismatch " ~ id ~ " axis " ~ axis);
        check(abs(bounds.maxCorner[axis] / centimeter - expectedMax[axis]) < 0.0001,
            "max bound mismatch " ~ id ~ " axis " ~ axis);
        expectedVolume *= expectedMax[axis] - expectedMin[axis];
    }
    check(abs(evVolume(context, { "entities" : body }) / centimeter ^ 3 - expectedVolume) < 0.001,
        "volume mismatch " ~ id);
}
