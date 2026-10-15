FeatureScript 3095;
import(path : "onshape/std/common.fs", version : "3095.0");

// Concept layout only. Coordinates are centimetres: X left-to-right, Y rear-to-cab, Z up.
// No measured body, wheel arches, doors, joinery, access hardware or bed extension support is implied.
export enum NV200Layout
{
    annotation { "Name" : "Daytime" }
    DAY,
    annotation { "Name" : "Nighttime" }
    NIGHT
}

const DEFAULTS = {
    "layout" : NV200Layout.DAY,
    "showCushions" : true,
    "cargoWidth" : 150 * centimeter,
    "cargoLength" : 186 * centimeter,
    "bedWidth" : 107 * centimeter,
    "seatWidth" : 57 * centimeter,
    "seatLength" : 128 * centimeter,
    "bedHeight" : 55 * centimeter,
    "foamThickness" : 10 * centimeter,
    "cabinetOuterLength" : 119 * centimeter,
    "cabinetInnerLength" : 94 * centimeter,
    "cabinetHeight" : 1300 * millimeter,
    "toiletWidth" : 37 * centimeter,
    "toiletDepth" : 42 * centimeter,
    "useZoneWidth" : 40 * centimeter,
    "useZoneDepth" : 70 * centimeter
};

// Preserve a filled rectangular bed and the continuous left-wall backrest.
// These dependencies are intentional, not independent measurements.
function layoutDimensions(d is map) returns map
{
    const p = {
        "baseHeight" : d.bedHeight - d.foamThickness,
        "infillWidth" : (d.bedWidth - d.seatWidth) / 2,
        "dLength" : d.cargoLength - d.seatLength,
        "c2Length" : d.cargoLength - d.seatLength,
        "c1Length" : 2 * d.seatLength - d.cargoLength,
        "cabinetDepth" : d.cargoWidth - d.bedWidth,
        "aisleWidth" : d.bedWidth - d.seatWidth,
        "innerGap" : d.seatLength - d.cabinetInnerLength,
        "outerGap" : d.seatLength - d.cabinetOuterLength,
        "frontUnbacked" : d.bedWidth - d.foamThickness - (2 * d.seatLength - d.cargoLength)
    };
    if (p.baseHeight <= 0 * centimeter)
        throw regenError("Bed surface height must exceed foam thickness.", ["bedHeight", "foamThickness"]);
    if (d.bedWidth <= d.seatWidth || d.cargoWidth <= d.bedWidth)
        throw regenError("Require cargo width > bed width > A seat width.",
            ["cargoWidth", "bedWidth", "seatWidth"]);
    if (d.foamThickness >= d.seatWidth || d.foamThickness >= p.dLength)
        throw regenError("Upright foam must fit on both seat cushions.", ["foamThickness"]);
    if (p.c1Length <= 0 * centimeter || p.c2Length <= 0 * centimeter)
        throw regenError("A length must exceed half the cargo length and remain shorter than it.",
            ["seatLength", "cargoLength"]);
    if (p.frontUnbacked < 0 * centimeter)
        throw regenError("C1 is too long for the cab-facing edge of D with this foam thickness.",
            ["seatLength", "cargoLength", "bedWidth", "foamThickness"]);
    if (d.cabinetInnerLength > d.cabinetOuterLength || p.outerGap < 0 * centimeter)
        throw regenError("Require cabinet inner length <= outer length <= A length.",
            ["cabinetInnerLength", "cabinetOuterLength", "seatLength"]);
    return p;
}

function nameAndColor(context is Context, bodies is Query, name is string, appearance is Color)
{
    setProperty(context, { "entities" : bodies, "propertyType" : PropertyType.NAME, "value" : name });
    setProperty(context, { "entities" : bodies, "propertyType" : PropertyType.APPEARANCE, "value" : appearance });
}

function makeBlock(context is Context, id is Id, name is string, lo is Vector, hi is Vector, appearance is Color)
{
    fCuboid(context, id, { "corner1" : lo, "corner2" : hi });
    nameAndColor(context, qCreatedBy(id, EntityType.BODY), name, appearance);
}

function footprintSketch(context is Context, id is Id, points is array)
{
    const sketch = newSketchOnPlane(context, id, {
        "sketchPlane" : plane(vector(0, 0, 0) * centimeter, vector(0, 0, 1), vector(1, 0, 0))
    });
    skPolyline(sketch, "outline", { "points" : points });
    skSolve(sketch);
}

annotation {
    "Feature Type Name" : "NV200Interior",
    "Feature Type Description" : "Editable concept layout. Select Daytime or Nighttime. Bed height is the foam top. " ~
        "D depth and C cushion lengths derive from the envelope and A length. Infill width/backrest height derives " ~
        "from bed width minus A width, divided by two. Cabinet depth is cargo width minus bed width. " ~
        "Cabinet height is editable; construction, extension support, toilet placement and vehicle fit are unresolved."
}
export const nv200Interior = defineFeature(function(context is Context, id is Id, definition is map)
    precondition
    {
        annotation { "Name" : "Layout", "Default" : NV200Layout.DAY }
        definition.layout is NV200Layout;
        annotation { "Name" : "Show cushions", "Default" : true,
            "Description" : "Include all seat and backrest cushions in the selected layout. Turn off to work on the structure." }
        definition.showCushions is boolean;
        annotation { "Name" : "Bed surface height", "Description" : "Height of the foam top above floor; bases = this minus foam." }
        isLength(definition.bedHeight, { (centimeter) : [0.1, 55, 1000] } as LengthBoundSpec);
        annotation { "Name" : "Foam thickness - all cushions" }
        isLength(definition.foamThickness, { (centimeter) : [0.1, 10, 1000] } as LengthBoundSpec);
        annotation { "Name" : "Bed width / D width", "Description" : "B and C infill width = (this - A width) / 2." }
        isLength(definition.bedWidth, { (centimeter) : [0.1, 107, 1000] } as LengthBoundSpec);
        annotation { "Name" : "A seat width" }
        isLength(definition.seatWidth, { (centimeter) : [0.1, 57, 1000] } as LengthBoundSpec);
        annotation { "Name" : "A seat length", "Description" : "D depth = cargo length - this; C2 = D depth; C1 = this - C2." }
        isLength(definition.seatLength, { (centimeter) : [0.1, 128, 1000] } as LengthBoundSpec);
        annotation { "Name" : "Simplified cargo width", "Description" : "Layout boundary only; not a measured body model." }
        isLength(definition.cargoWidth, { (centimeter) : [0.1, 150, 1000] } as LengthBoundSpec);
        annotation { "Name" : "Simplified cargo length" }
        isLength(definition.cargoLength, { (centimeter) : [0.1, 186, 1000] } as LengthBoundSpec);
        annotation { "Name" : "Cabinet height", "Description" : "Height above floor; solid envelope only, construction undecided." }
        isLength(definition.cabinetHeight, {
            (meter) : [0.001, 1.3, 10],
            (millimeter) : 1300,
            (centimeter) : 130
        } as LengthBoundSpec);
        annotation { "Name" : "Cabinet outer length", "Description" : "Outer length of the angled cabinet envelope." }
        isLength(definition.cabinetOuterLength, { (centimeter) : [0.1, 119, 1000] } as LengthBoundSpec);
        annotation { "Name" : "Cabinet inner length" }
        isLength(definition.cabinetInnerLength, { (centimeter) : [0.1, 94, 1000] } as LengthBoundSpec);
        annotation { "Group Name" : "Toilet references - UNPLACED, fit unresolved", "Collapsed By Default" : true }
        {
            annotation { "Name" : "Assumed toilet width", "Description" : "Reference only: no location, orientation or height assigned." }
            isLength(definition.toiletWidth, { (centimeter) : [0.1, 37, 1000] } as LengthBoundSpec);
            annotation { "Name" : "Assumed toilet depth" }
            isLength(definition.toiletDepth, { (centimeter) : [0.1, 42, 1000] } as LengthBoundSpec);
            annotation { "Name" : "Provisional use-zone width" }
            isLength(definition.useZoneWidth, { (centimeter) : [0.1, 40, 1000] } as LengthBoundSpec);
            annotation { "Name" : "Provisional use-zone depth" }
            isLength(definition.useZoneDepth, { (centimeter) : [0.1, 70, 1000] } as LengthBoundSpec);
        }
    }
    {
        const d = definition;
        const p = layoutDimensions(d);
        const zero = 0 * centimeter;
        const w = d.seatWidth;
        const l = d.seatLength;
        const bw = d.bedWidth;
        const end = d.cargoLength;
        const h = d.bedHeight;
        const t = d.foamThickness;
        const z = p.baseHeight;
        const backTop = h + p.infillWidth;
        const baseColor = color(0.62, 0.55, 0.43);

        makeBlock(context, id + "baseA", "A - storage envelope (construction undecided)",
            vector(zero, zero, zero), vector(w, l, z), baseColor);
        makeBlock(context, id + "baseD", "D - storage envelope (construction undecided)",
            vector(zero, l, zero), vector(bw, end, z), baseColor);
        if (d.showCushions)
        {
            makeBlock(context, id + "cushionA", "A - seat cushion",
                vector(zero, zero, z), vector(w, l, h), color(0.19, 0.47, 0.63));
            makeBlock(context, id + "cushionD", "D - seat cushion",
                vector(zero, l, z), vector(bw, end, h), color(0.26, 0.57, 0.70));

            if (d.layout == NV200Layout.DAY)
            {
                makeBlock(context, id + "cushionB", "B - movable backrest / infill",
                    vector(zero, zero, h), vector(t, l, backTop), color(0.83, 0.52, 0.22));
                makeBlock(context, id + "cushionC1", "C1 - movable backrest / infill",
                    vector(t, end - t, h), vector(t + p.c1Length, end, backTop), color(0.46, 0.61, 0.35));
                makeBlock(context, id + "cushionC2", "C2 - movable backrest / infill",
                    vector(zero, l, h), vector(t, end, backTop), color(0.64, 0.43, 0.66));
            }
            else
            {
                const split = w + p.infillWidth;
                makeBlock(context, id + "cushionB", "B - movable backrest / infill",
                    vector(w, zero, z), vector(split, l, h), color(0.83, 0.52, 0.22));
                makeBlock(context, id + "cushionC1", "C1 - movable backrest / infill",
                    vector(split, zero, z), vector(bw, p.c1Length, h), color(0.46, 0.61, 0.35));
                makeBlock(context, id + "cushionC2", "C2 - movable backrest / infill",
                    vector(split, p.c1Length, z), vector(bw, l, h), color(0.64, 0.43, 0.66));
            }
        }

        footprintSketch(context, id + "cabinetSketch", [
            vector(bw, zero), vector(d.cargoWidth, zero),
            vector(d.cargoWidth, d.cabinetOuterLength), vector(bw, d.cabinetInnerLength), vector(bw, zero)
        ]);
        opExtrude(context, id + "cabinet", {
            "entities" : qSketchRegion(id + "cabinetSketch"),
            "direction" : vector(0, 0, 1),
            "endBound" : BoundingType.BLIND,
            "endDepth" : d.cabinetHeight
        });
        nameAndColor(context, qCreatedBy(id + "cabinet", EntityType.BODY),
            "Cabinet envelope - construction undecided", color(0.84, 0.73, 0.46));
        opDeleteBodies(context, id + "removeCabinetSketch", { "entities" : qCreatedBy(id + "cabinetSketch", EntityType.BODY) });

        footprintSketch(context, id + "cargoBoundary", [
            vector(zero, zero), vector(d.cargoWidth, zero), vector(d.cargoWidth, end),
            vector(zero, end), vector(zero, zero)
        ]);

        // Named values remain available to downstream features via #nv200_* expressions.
        for (var key, value in p)
            setVariable(context, "nv200_" ~ key, value);
        setVariable(context, "nv200_bedHeight", h);
        setVariable(context, "nv200_foamThickness", t);
        setVariable(context, "nv200_bedWidth", bw);
        setVariable(context, "nv200_cargoLength", end);
        setVariable(context, "nv200_cabinetHeight", d.cabinetHeight);
        setVariable(context, "nv200_toiletWidth_UNPLACED", d.toiletWidth);
        setVariable(context, "nv200_toiletDepth_UNPLACED", d.toiletDepth);
        setVariable(context, "nv200_useZoneWidth_UNPLACED", d.useZoneWidth);
        setVariable(context, "nv200_useZoneDepth_UNPLACED", d.useZoneDepth);
    }, DEFAULTS);

