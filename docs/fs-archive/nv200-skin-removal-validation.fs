function(context, queries) {

// X left-to-right, Y rear-to-cab, Z up. Existing layout lengths and new construction lengths carry explicit units.
// Fixed plywood carcasses are detailed. Sliding slats, hatch doors, joints and vehicle fit remain unresolved.
// Cushion shapes retain the previous layout until the sliding platform and cushion arrangements are designed.


const DEFAULTS = {
    "layout" : "DAY",
    "showCushions" : true,
    "cargoWidth" : 150 * centimeter,
    "cargoLength" : 186 * centimeter,
    "bedWidth" : 107 * centimeter,
    "seatWidth" : 57 * centimeter,
    "seatLength" : 128 * centimeter,
    "platformHeight" : 400 * millimeter,
    "wallThickness" : 7 * millimeter,
    "frameThickness" : 18 * millimeter,
    "memberWidth" : 60 * millimeter,
    "insideRadius" : 25 * millimeter,
    "slatThickness" : 18 * millimeter,
    "crossExtension" : 200 * millimeter,
    "archRearOffset" : 216 * millimeter,
    "archLength" : 750 * millimeter,
    "archHeight" : 280 * millimeter,
    "archRadius" : 200 * millimeter,
    "archGap" : 1220 * millimeter,
    "archClearance" : 50 * millimeter,
    "rearCornerRadius" : 100 * millimeter,
    "rearCornerAllowance" : 20 * millimeter,
    "showRearCorners" : true,
    "showWheelArches" : true,
    "showDoors" : true,
    "showLeftDoor" : true,
    "showRightDoor" : true,
    "rearDoorWidth" : 1262 * millimeter,
    "rearDoorHeight" : 1228 * millimeter,
    "rearDoorY" : 0 * millimeter,
    "rearDoorSill" : 0 * millimeter,
    "sideDoorWidth" : 693 * millimeter,
    "sideDoorHeight" : 1171 * millimeter,
    "sideDoorFrontGap" : 0 * millimeter,
    "sideDoorSill" : 0 * millimeter,
    "foamThickness" : 10 * centimeter,
    "cabinetOuterLength" : 119 * centimeter,
    "cabinetHeight" : 1300 * millimeter,
    "toiletWidth" : 37 * centimeter,
    "toiletDepth" : 42 * centimeter,
    "useZoneWidth" : 40 * centimeter,
    "useZoneDepth" : 70 * centimeter
};

// Preserve a filled rectangular bed and the continuous left-wall backrest.
// These dependencies are intentional, not independent measurements.
const layoutDimensions = function(d is map) returns map
{
    const p = {
        "baseHeight" : d.platformHeight,
        "infillWidth" : (d.bedWidth - d.seatWidth) / 2,
        "dLength" : d.cargoLength - d.seatLength,
        "c2Length" : d.cargoLength - d.seatLength,
        "c1Length" : 2 * d.seatLength - d.cargoLength,
        "cabinetDepth" : d.cargoWidth - d.bedWidth,
        "aisleWidth" : d.bedWidth - d.seatWidth,
        "innerGap" : d.seatLength - d.cabinetOuterLength,
        "outerGap" : d.seatLength - d.cabinetOuterLength,
        "frontUnbacked" : d.bedWidth - d.foamThickness - (2 * d.seatLength - d.cargoLength)
    };
    if (p.baseHeight <= 0 * centimeter)
        throw regenError("Platform height must be positive.", ["platformHeight"]);
    if (d.bedWidth <= d.seatWidth || d.cargoWidth <= d.bedWidth)
        throw regenError("Require cargo width > bed width > long bench width.",
            ["cargoWidth", "bedWidth", "seatWidth"]);
    if (d.foamThickness >= d.seatWidth || d.foamThickness >= p.dLength)
        throw regenError("Upright foam must fit on both seat cushions.", ["foamThickness"]);
    if (p.c1Length <= 0 * centimeter || p.c2Length <= 0 * centimeter)
        throw regenError("Long bench length must exceed half the cargo length and remain shorter than it.",
            ["seatLength", "cargoLength"]);
    if (p.frontUnbacked < 0 * centimeter)
        throw regenError("The reference cab-facing cushion is too long for this bed width and foam thickness.",
            ["seatLength", "cargoLength", "bedWidth", "foamThickness"]);
    if (p.outerGap < 0 * centimeter)
        throw regenError("Cabinet length must not exceed the long bench length.",
            ["cabinetOuterLength", "seatLength"]);
    return p;
};

const nameAndColor = function(context is Context, bodies is Query, name is string, appearance is Color)
{
    setProperty(context, { "entities" : bodies, "propertyType" : PropertyType.NAME, "value" : name });
    setProperty(context, { "entities" : bodies, "propertyType" : PropertyType.APPEARANCE, "value" : appearance });
};

const makeBlock = function(context is Context, id is Id, name is string, lo is Vector, hi is Vector, appearance is Color)
{
    fCuboid(context, id, { "corner1" : lo, "corner2" : hi });
    nameAndColor(context, qCreatedBy(id, EntityType.BODY), name, appearance);
};

const footprintSketch = function(context is Context, id is Id, points is array)
{
    const sketch = newSketchOnPlane(context, id, {
        "sketchPlane" : plane(vector(0, 0, 0) * centimeter, vector(0, 0, 1), vector(1, 0, 0))
    });
    skPolyline(sketch, "outline", { "points" : points });
    skSolve(sketch);
};

/** Rounded opening cutter in the vertical plane of a plywood panel. */
const openingTool = function(context is Context, id is Id, origin is Vector, along is Vector,
    normal is Vector, x0, x1, bottom, top, radius, depth)
{
    const sketch = newSketchOnPlane(context, id + "sketch", {
        "sketchPlane" : plane(origin, normal, along)
    });
    const r = radius;
    const k = 1 - 1 / sqrt(2);
    skLineSegment(sketch, "bottom", { "start" : vector(x0+r,bottom), "end" : vector(x1-r,bottom) });
    skArc(sketch, "br", { "start" : vector(x1-r,bottom),
        "mid" : vector(x1-k*r,bottom+k*r), "end" : vector(x1,bottom+r) });
    skLineSegment(sketch, "right", { "start" : vector(x1,bottom+r), "end" : vector(x1,top-r) });
    skArc(sketch, "tr", { "start" : vector(x1,top-r),
        "mid" : vector(x1-k*r,top-k*r), "end" : vector(x1-r,top) });
    skLineSegment(sketch, "top", { "start" : vector(x1-r,top), "end" : vector(x0+r,top) });
    skArc(sketch, "tl", { "start" : vector(x0+r,top),
        "mid" : vector(x0+k*r,top-k*r), "end" : vector(x0,top-r) });
    skLineSegment(sketch, "left", { "start" : vector(x0,top-r), "end" : vector(x0,bottom+r) });
    skArc(sketch, "bl", { "start" : vector(x0,bottom+r),
        "mid" : vector(x0+k*r,bottom+k*r), "end" : vector(x0+r,bottom) });
    skSolve(sketch);
    opExtrude(context, id + "solid", { "entities" : qSketchRegion(id + "sketch"),
        "direction" : normal, "endBound" : BoundingType.BLIND, "endDepth" : depth });
    opDeleteBodies(context, id + "cleanup", { "entities" : qCreatedBy(id + "sketch", EntityType.BODY) });
};

/** Access faces use an open-bottom frame only; closed faces also retain a solid outer skin. */
const benchWall = function(context is Context, id is Id, name is string, origin is Vector,
    along is Vector, normal is Vector, length, height, bays is number, access is boolean, d is map, parameterIds is array)
{
    const w = d.memberWidth;
    const r = d.insideRadius;
    const bay = (length - (bays + 1) * w) / bays;
    if (bay <= 2*r || height <= 2*w + 2*r)
        throw regenError("Panel is too small for its bands, posts and corner radii.",
            parameterIds);
    const up = vector(0,0,1);
    for (var layer = access ? 1 : 0; layer < 2; layer += 1)
    {
        const layerId = id + ("layer" ~ layer);
        const offset = layer == 0 ? 0*millimeter : d.wallThickness;
        const thickness = layer == 0 ? d.wallThickness : d.frameThickness;
        const start = origin + normal*offset;
        fCuboid(context, layerId + "plate", {
            "corner1" : start,
            "corner2" : start + along*length + normal*thickness + up*height
        });
        const plate = qCreatedBy(layerId + "plate", EntityType.BODY);
        if (layer == 1)
        {
            for (var i = 0; i < bays; i += 1)
            {
                const cutId = layerId + ("opening" ~ i);
                const left = w + i*(bay+w);
                // All frame openings reach the floor; no cut-out outer skins are generated.
                const bottom = -2*r;
                openingTool(context, cutId, start - normal*millimeter, along, normal,
                    left, left+bay, bottom, height-w, r, thickness+2*millimeter);
                opBoolean(context, cutId + "subtract", {
                    "tools" : qCreatedBy(cutId + "solid", EntityType.BODY),
                    "targets" : plate, "operationType" : BooleanOperationType.SUBTRACTION
                });
            }
        }
        nameAndColor(context, plate, name ~ (layer == 0 ? " - outer wall" : " - inner frame"),
            layer == 0 ? color(0.75,0.66,0.49) : color(0.88,0.61,0.25));
    }
};




/** Door reference outlines only; rectangles do not imply body contours, door leaves or travel paths. */
const doorOutline = function(context is Context, id is Id, name is string, origin is Vector,
    normal is Vector, along is Vector, width, height)
{
    const zero = 0*millimeter;
    const sketch = newSketchOnPlane(context,id,{"sketchPlane":plane(origin,normal,along)});
    const corners = [vector(zero,zero),vector(width,zero),vector(width,height),vector(zero,height)];
    for (var i = 0; i < 4; i += 1)
        skLineSegment(sketch,"edge" ~ i,{"start":corners[i],"end":corners[(i+1)%4],"construction":true});
    skSolve(sketch);
    setProperty(context,{"entities":qCreatedBy(id,EntityType.BODY),"propertyType":PropertyType.NAME,"value":name});
};

/** Rounded upper ends only: editable visual approximation, with the full base footprint retained. */
const wheelArchReference = function(context is Context, id is Id, name is string, x, depth, d is map)
{
    const r = d.archRadius;
    const length = d.archLength;
    const height = d.archHeight;
    if (r <= 0*millimeter || 2*r >= length || r >= height)
        throw regenError("Arch rounding radius must be positive, below its height and below half its length.",
            ["archRadius", "archLength", "archHeight"]);
    const zero = 0*millimeter;
    const k = 1-1/sqrt(2);
    const sketch = newSketchOnPlane(context,id+"profile",{
        "sketchPlane":plane(vector(x,d.archRearOffset,zero),vector(1,0,0),vector(0,1,0))
    });
    skLineSegment(sketch,"base",{"start":vector(zero,zero),"end":vector(length,zero)});
    skLineSegment(sketch,"front",{"start":vector(length,zero),"end":vector(length,height-r)});
    skArc(sketch,"frontRound",{"start":vector(length,height-r),
        "mid":vector(length-k*r,height-k*r),"end":vector(length-r,height)});
    skLineSegment(sketch,"top",{"start":vector(length-r,height),"end":vector(r,height)});
    skArc(sketch,"rearRound",{"start":vector(r,height),
        "mid":vector(k*r,height-k*r),"end":vector(zero,height-r)});
    skLineSegment(sketch,"rear",{"start":vector(zero,height-r),"end":vector(zero,zero)});
    skSolve(sketch);
    opExtrude(context,id+"body",{"entities":qSketchRegion(id+"profile"),"direction":vector(1,0,0),
        "endBound":BoundingType.BLIND,"endDepth":depth});
    opDeleteBodies(context,id+"cleanup",{"entities":qCreatedBy(id+"profile",EntityType.BODY)});
    nameAndColor(context,qCreatedBy(id+"body",EntityType.BODY),name,color(0.45,0.49,0.52));
};


/** Concave rear body corner surface. Radius is provisional; height follows the rear opening reference. */
const rearCornerReference = function(context is Context, id is Id, right is boolean, d is map)
{
    const r = d.rearCornerRadius;
    const k = 1-1/sqrt(2);
    const zero = 0*millimeter;
    const x = right ? d.cargoWidth : zero;
    const sign = right ? -1 : 1;
    const sketch = newSketchOnPlane(context,id+"profile",{
        "sketchPlane":plane(vector(zero,zero,zero),vector(0,0,1),vector(1,0,0))
    });
    skArc(sketch,"corner",{"start":vector(x+sign*r,zero),
        "mid":vector(x+sign*k*r,k*r),"end":vector(x,r)});
    skSolve(sketch);
    opExtrude(context,id+"surface",{"entities":qCreatedBy(id+"profile",EntityType.EDGE),
        "direction":vector(0,0,1),"endBound":BoundingType.BLIND,
        "endDepth":d.rearDoorSill+d.rearDoorHeight});
    opDeleteBodies(context,id+"cleanup",{"entities":qCreatedBy(id+"profile",EntityType.BODY)});
    nameAndColor(context,qCreatedBy(id+"surface",EntityType.BODY),
        (right ? "Right" : "Left") ~ " rear body corner - approximate surface",color(0.55,0.58,0.61));
};

/** Frame only along the long bench wall: broad rear end, one post after the arch, front end. */
const wheelArchFrame = function(context is Context, id is Id, name is string, variablePrefix is string,
    frameX, y, length, height, d is map)
{
    const w = d.memberWidth;
    const parameterIds = variablePrefix == "nv200_cabinet" ?
        ["cabinetHeight", "cabinetOuterLength", "memberWidth", "insideRadius",
         "archRearOffset", "archLength", "archHeight", "archClearance", "rearCornerRadius", "rearCornerAllowance"] :
        ["platformHeight", "slatThickness", "seatLength", "memberWidth", "insideRadius",
         "archRearOffset", "archLength", "archHeight", "archClearance", "rearCornerRadius", "rearCornerAllowance"];
    const setback = d.rearCornerRadius+d.rearCornerAllowance;
    const rearSupportEnd = max(d.archRearOffset-d.archClearance,setback+w);
    const rearClearance = d.archRearOffset-rearSupportEnd;
    if (rearClearance <= 0*millimeter)
        throw regenError("Rear corner setback and post reach the wheel arch. Check measured dimensions.", parameterIds);
    const postStart = d.archRearOffset+d.archLength+d.archClearance;
    const postEnd = postStart+w;
    if (rearSupportEnd < w || postEnd > length-w)
        throw regenError("Wheel arch and clearances leave insufficient room for the wall-side supports.", parameterIds);
    if (d.archHeight > height-w)
        throw regenError("Wheel arch reaches above the underside of the wall-side top band.", parameterIds);
    const origin = vector(frameX,y+setback,0*millimeter);
    // Retain the inner-frame plane so it meets the existing end panels.
    fCuboid(context, id+"plate", {
        "corner1" : origin,
        "corner2" : origin+vector(d.frameThickness,length-setback,height)
    });
    const frame = qCreatedBy(id+"plate",EntityType.BODY);
    const openings = [[rearSupportEnd,postStart],[postEnd,length-w]];
    for (var i = 0; i < size(openings); i += 1)
    {
        const bounds = openings[i];
        const gap = bounds[1]-bounds[0];
        if (gap > 0*millimeter)
        {
            const radius = d.insideRadius;
            if (gap <= 2*radius || height-w <= 2*radius)
                throw regenError("Wall-side opening is too small for the specified corner radius.", parameterIds);
            const endClearance = min(rearClearance,d.archClearance);
            if (i == 0 && endClearance < radius)
            {
                const cornerHeight = height-w-radius+
                    sqrt(radius^2-(radius-endClearance)^2);
                if (d.archHeight > cornerHeight)
                    throw regenError("Wheel arch intersects the rounded opening corners.", parameterIds);
            }
            const cutId = id+("opening" ~ i);
            openingTool(context,cutId,origin-vector(1,0,0)*millimeter,
                vector(0,1,0),vector(1,0,0),bounds[0]-setback,bounds[1]-setback,-2*radius,height-w,
                radius,d.frameThickness+2*millimeter);
            opBoolean(context,cutId+"subtract",{
                "tools":qCreatedBy(cutId+"solid",EntityType.BODY),
                "targets":frame,"operationType":BooleanOperationType.SUBTRACTION
            });
        }
    }
    nameAndColor(context,frame,name ~ " wall-side frame - wheel-arch opening",color(0.88,0.61,0.25));
    setVariable(context,variablePrefix ~ "_rearWallSupportWidth",rearSupportEnd-setback);
    setVariable(context,variablePrefix ~ "_rearWallSupportStart",y+setback);
    setVariable(context,variablePrefix ~ "_rearWallSupportEnd",y+rearSupportEnd);
    setVariable(context,variablePrefix ~ "_rearArchClearance",rearClearance);
    setVariable(context,variablePrefix ~ "_rearCornerSetback",setback);
    setVariable(context,variablePrefix ~ "_wallPostStart",y+postStart);
    setVariable(context,variablePrefix ~ "_wallPostEnd",y+postEnd);
};

/** Opposite long walls run full length; the end walls fit between the combined wall/frame thicknesses. */
const benchCarcass = function(context is Context, id is Id, name is string, x, y, width, length,
    height, longBays is number, rightAccess is boolean, archSide is string, d is map)
{
    const zero = 0*millimeter;
    const parameterIds = archSide == "RIGHT" ?
        ["wallThickness", "frameThickness", "memberWidth", "insideRadius", "cabinetHeight",
         "cabinetOuterLength", "cargoWidth", "bedWidth", "rearCornerRadius", "rearCornerAllowance"] :
        ["wallThickness", "frameThickness", "memberWidth", "insideRadius", "platformHeight",
         "slatThickness", "seatWidth", "seatLength", "cargoLength", "crossExtension"];
    const total = d.wallThickness+d.frameThickness;
    if (width <= 2*total || length <= 2*total)
        throw regenError("Bench width and depth must exceed twice the combined wall and frame thickness.",
            parameterIds);
    const variablePrefix = archSide == "RIGHT" ? "nv200_cabinet" : "nv200";
    if (archSide == "LEFT")
        wheelArchFrame(context,id+"left",name,variablePrefix,x+d.wallThickness,y,length,height,d);
    else
        benchWall(context, id+"left", name ~ (archSide == "RIGHT" ? " aisle side" : " wall side"),
            vector(x,y,zero),vector(0,1,0),vector(1,0,0),length,height,longBays,
            archSide == "RIGHT" && rightAccess,d,parameterIds);
    if (archSide == "RIGHT")
        wheelArchFrame(context,id+"right",name,variablePrefix,x+width-total,y,length,height,d);
    else
        benchWall(context, id+"right", name ~ " aisle side", vector(x+width,y+length,zero),
            vector(0,-1,0), vector(-1,0,0), length,height,longBays,rightAccess,d,parameterIds);
    const setback = max(total,d.rearCornerRadius+d.rearCornerAllowance);
    const rearLeft = archSide == "LEFT" ? setback : total;
    const rearRight = archSide == "RIGHT" ? setback : total;
    benchWall(context, id+"rear", name ~ " rear end", vector(x+width-rearRight,y,zero),
        vector(-1,0,0), vector(0,1,0), width-rearLeft-rearRight,height,1,false,d,parameterIds);
    benchWall(context, id+"front", name ~ " cab end", vector(x+total,y+length,zero),
        vector(1,0,0), vector(0,-1,0), width-2*total,height,1,false,d,parameterIds);
};

const nv200Interior = defineFeature(function(context is Context, id is Id, definition is map)
    precondition
    {
        annotation { "Name" : "Layout", "Default" : "DAY" }
        definition.layout is string;
        annotation { "Name" : "Show cushions", "Default" : true,
            "Description" : "Include all seat and backrest cushions in the selected layout. Turn off to work on the structure." }
        definition.showCushions is boolean;
        annotation { "Name" : "Platform height", "Description" : "Floor to top of slats; foam sits above this." }
        isLength(definition.platformHeight, { (meter) : [0.1, 0.4, 2], (millimeter) : 400 } as LengthBoundSpec);
        annotation { "Group Name" : "Plywood bench construction", "Collapsed By Default" : false }
        {
            annotation { "Name" : "Outer wall thickness" }
            isLength(definition.wallThickness, { (meter) : [0.001, 0.007, 0.05], (millimeter) : 7 } as LengthBoundSpec);
            annotation { "Name" : "Inner frame thickness" }
            isLength(definition.frameThickness, { (meter) : [0.001, 0.018, 0.1], (millimeter) : 18 } as LengthBoundSpec);
            annotation { "Name" : "Beam and post width" }
            isLength(definition.memberWidth, { (meter) : [0.01, 0.06, 0.3], (millimeter) : 60 } as LengthBoundSpec);
            annotation { "Name" : "Inside corner radius" }
            isLength(definition.insideRadius, { (meter) : [0.001, 0.025, 0.2], (millimeter) : 25 } as LengthBoundSpec);
            annotation { "Name" : "Slat thickness", "Description" : "Reserved above the carcass; sliding slats are the next design step." }
            isLength(definition.slatThickness, { (meter) : [0.001, 0.018, 0.1], (millimeter) : 18 } as LengthBoundSpec);
            annotation { "Name" : "Cross bench extension", "Description" : "Fixed cross bench width = bed width minus extension." }
            isLength(definition.crossExtension, { (meter) : [0.001, 0.2, 0.7], (millimeter) : 200 } as LengthBoundSpec);
        }
        annotation { "Group Name" : "Wheel arches - provisional drawing dimensions", "Collapsed By Default" : false }
        {
            annotation { "Name" : "Show wheel-arch reference envelopes", "Default" : true }
            definition.showWheelArches is boolean;
            annotation { "Name" : "Rear floor edge to arch", "Description" : "Approximate drawing reference; measure on your van." }
            isLength(definition.archRearOffset, { (meter) : [0.001, 0.216, 2], (millimeter) : 216 } as LengthBoundSpec);
            annotation { "Name" : "Wheel-arch length" }
            isLength(definition.archLength, { (meter) : [0.01, 0.75, 2], (millimeter) : 750 } as LengthBoundSpec);
            annotation { "Name" : "Wheel-arch height above floor" }
            isLength(definition.archHeight, { (meter) : [0.001, 0.28, 1], (millimeter) : 280 } as LengthBoundSpec);
            annotation { "Name" : "Wheel-arch rounding radius",
                "Description" : "Approximate upper-end rounding only, not a measured vehicle contour. Base footprint stays unchanged." }
            isLength(definition.archRadius, { (meter) : [0.001, 0.2, 1], (millimeter) : 200 } as LengthBoundSpec);
            annotation { "Name" : "Clear width between wheel arches", "Description" : "Centred in simplified cargo width. Does not measure actual wall curvature." }
            isLength(definition.archGap, { (meter) : [0.01, 1.22, 3], (millimeter) : 1220 } as LengthBoundSpec);
            annotation { "Name" : "Preferred post clearance around arch", "Description" : "Rear gap may reduce to preserve the full post width after the rear corner setback. Arch position stays fixed." }
            isLength(definition.archClearance, { (meter) : [0.001, 0.05, 0.5], (millimeter) : 50 } as LengthBoundSpec);
        }
        annotation { "Group Name" : "Rear body corners and bench clearance", "Collapsed By Default" : false }
        {
            annotation { "Name" : "Show rear body corner references", "Default" : true }
            definition.showRearCorners is boolean;
            annotation { "Name" : "Rear body inside corner radius", "Description" : "Approximate vehicle radius; rear corner reference height follows rear door opening height." }
            isLength(definition.rearCornerRadius, { (meter) : [0.001,0.1,0.5], (millimeter) : 100 } as LengthBoundSpec);
            annotation { "Name" : "Rear corner allowance", "Description" : "Bench setback = body radius + allowance. Keeps a full-width post; actual rear arch gap is derived." }
            isLength(definition.rearCornerAllowance, { (meter) : [0,0.02,0.3], (millimeter) : 20 } as LengthBoundSpec);
        }
        annotation { "Group Name" : "Door opening references - provisional positions", "Collapsed By Default" : true }
        {
            annotation { "Name" : "Show door opening outlines", "Default" : true }
            definition.showDoors is boolean;
            annotation { "Name" : "Show left sliding-door opening", "Default" : true }
            definition.showLeftDoor is boolean;
            annotation { "Name" : "Show right sliding-door opening", "Default" : true }
            definition.showRightDoor is boolean;
            annotation { "Name" : "Rear opening width", "Description" : "Published nominal opening; verify on this van." }
            isLength(definition.rearDoorWidth, { (meter) : [0.001, 1.262, 3], (millimeter) : 1262 } as LengthBoundSpec);
            annotation { "Name" : "Rear opening height", "Description" : "Published nominal opening; verify on this van." }
            isLength(definition.rearDoorHeight, { (meter) : [0.001, 1.228, 3], (millimeter) : 1228 } as LengthBoundSpec);
            annotation { "Name" : "Rear opening offset from rear floor edge", "Description" : "Position placeholder, not a measured door plane." }
            isLength(definition.rearDoorY, { (meter) : [0, 0, 3], (millimeter) : 0 } as LengthBoundSpec);
            annotation { "Name" : "Rear opening bottom above floor", "Description" : "Zero assumes opening bottom at our floor datum." }
            isLength(definition.rearDoorSill, { (meter) : [0, 0, 3], (millimeter) : 0 } as LengthBoundSpec);
            annotation { "Name" : "Side opening width along van", "Description" : "Published nominal opening; verify on this van." }
            isLength(definition.sideDoorWidth, { (meter) : [0.001, 0.693, 3], (millimeter) : 693 } as LengthBoundSpec);
            annotation { "Name" : "Side opening height", "Description" : "Published nominal opening; verify on this van." }
            isLength(definition.sideDoorHeight, { (meter) : [0.001, 1.171, 3], (millimeter) : 1171 } as LengthBoundSpec);
            annotation { "Name" : "Side opening front gap to cab end", "Description" : "Zero provisionally aligns front edge with simplified cargo end." }
            isLength(definition.sideDoorFrontGap, { (meter) : [0, 0, 3], (millimeter) : 0 } as LengthBoundSpec);
            annotation { "Name" : "Side opening bottom above floor", "Description" : "Zero assumes opening bottom at our floor datum." }
            isLength(definition.sideDoorSill, { (meter) : [0, 0, 3], (millimeter) : 0 } as LengthBoundSpec);
        }
        annotation { "Name" : "Foam thickness - all cushions" }
        isLength(definition.foamThickness, { (centimeter) : [0.1, 10, 1000] } as LengthBoundSpec);
        annotation { "Name" : "Full bed width", "Description" : "Reference cushion infill width = (bed width - long bench width) / 2." }
        isLength(definition.bedWidth, { (centimeter) : [0.1, 107, 1000] } as LengthBoundSpec);
        annotation { "Name" : "Long bench width" }
        isLength(definition.seatWidth, { (centimeter) : [0.1, 57, 1000] } as LengthBoundSpec);
        annotation { "Name" : "Long bench length", "Description" : "Cross bench depth = cargo length minus long bench length." }
        isLength(definition.seatLength, { (centimeter) : [0.1, 128, 1000] } as LengthBoundSpec);
        annotation { "Name" : "Simplified cargo width", "Description" : "Layout boundary only; not a measured body model." }
        isLength(definition.cargoWidth, { (centimeter) : [0.1, 150, 1000] } as LengthBoundSpec);
        annotation { "Name" : "Simplified cargo length" }
        isLength(definition.cargoLength, { (centimeter) : [0.1, 186, 1000] } as LengthBoundSpec);
        annotation { "Name" : "Cabinet frame height", "Description" : "Floor to top of cabinet walls and frames. Top, shelves and doors are not yet modelled." }
        isLength(definition.cabinetHeight, {
            (meter) : [0.001, 1.3, 10],
            (millimeter) : 1300,
            (centimeter) : 130
        } as LengthBoundSpec);
        annotation { "Name" : "Cabinet length", "Description" : "Rectangular cabinet length on both edges; retains the previous outer-length value." }
        isLength(definition.cabinetOuterLength, { (centimeter) : [0.1, 119, 1000] } as LengthBoundSpec);
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
        const h = d.platformHeight + d.foamThickness;
        const t = d.foamThickness;
        const z = p.baseHeight;
        const backTop = h + p.infillWidth;
        
        const panelHeight = z-d.slatThickness;
        const crossWidth = bw-d.crossExtension;
        if (crossWidth <= w || d.crossExtension >= bw)
            throw regenError("Cross bench fixed width must exceed the long bench width.", ["crossExtension", "bedWidth"]);
        benchCarcass(context, id+"longBench", "Long bench", zero,zero,w,l,panelHeight,2,true,"LEFT",d);
        benchCarcass(context, id+"crossBench", "Cross bench", zero,l,crossWidth,p.dLength,panelHeight,1,true,"NONE",d);
        setVariable(context, "nv200_panelHeight", panelHeight);
        setVariable(context, "nv200_crossBenchFixedWidth", crossWidth);
        setVariable(context, "nv200_longHatchWidth", (l-3*d.memberWidth)/2);
        setVariable(context, "nv200_hatchHeight", panelHeight-d.memberWidth);
        setVariable(context, "nv200_wallThickness", d.wallThickness);
        setVariable(context, "nv200_frameThickness", d.frameThickness);
        setVariable(context, "nv200_memberWidth", d.memberWidth);
        if (d.showCushions)
        {
            makeBlock(context, id + "cushionA", "Long seat cushion - layout reference",
                vector(zero, zero, z), vector(w, l, h), color(0.19, 0.47, 0.63));
            makeBlock(context, id + "cushionD", "Cross seat cushion - original full-width reference",
                vector(zero, l, z), vector(bw, end, h), color(0.26, 0.57, 0.70));

            if (d.layout == "DAY")
            {
                makeBlock(context, id + "cushionB", "Long backrest / infill - layout reference",
                    vector(zero, zero, h), vector(t, l, backTop), color(0.83, 0.52, 0.22));
                makeBlock(context, id + "cushionC1", "Cab-facing backrest / infill - layout reference",
                    vector(t, end - t, h), vector(t + p.c1Length, end, backTop), color(0.46, 0.61, 0.35));
                makeBlock(context, id + "cushionC2", "Short side backrest / infill - layout reference",
                    vector(zero, l, h), vector(t, end, backTop), color(0.64, 0.43, 0.66));
            }
            else
            {
                const split = w + p.infillWidth;
                makeBlock(context, id + "cushionB", "Long backrest / infill - layout reference",
                    vector(w, zero, z), vector(split, l, h), color(0.83, 0.52, 0.22));
                makeBlock(context, id + "cushionC1", "Cab-facing backrest / infill - layout reference",
                    vector(split, zero, z), vector(bw, p.c1Length, h), color(0.46, 0.61, 0.35));
                makeBlock(context, id + "cushionC2", "Short side backrest / infill - layout reference",
                    vector(split, p.c1Length, z), vector(bw, l, h), color(0.64, 0.43, 0.66));
            }
        }

        benchCarcass(context,id+"cabinet","Cabinet",bw,zero,p.cabinetDepth,d.cabinetOuterLength,
            d.cabinetHeight,2,true,"RIGHT",d);

        footprintSketch(context, id + "cargoBoundary", [
            vector(zero, zero), vector(d.cargoWidth, zero), vector(d.cargoWidth, end),
            vector(zero, end), vector(zero, zero)
        ]);


        if (d.archGap >= d.cargoWidth || d.archRearOffset+d.archLength > end)
            throw regenError("Wheel-arch reference dimensions exceed the cargo envelope.",
                ["archGap", "cargoWidth", "archRearOffset", "archLength", "cargoLength"]);
        const intrusion = (d.cargoWidth-d.archGap)/2;
        if (d.showWheelArches)
        {
            wheelArchReference(context,id+"leftArch","Left wheel arch - rounded approximation",
                zero,intrusion,d);
            wheelArchReference(context,id+"rightArch","Right wheel arch - rounded approximation",
                d.cargoWidth-intrusion,intrusion,d);
        }

        if (d.showRearCorners)
        {
            rearCornerReference(context,id+"leftRearCorner",false,d);
            rearCornerReference(context,id+"rightRearCorner",true,d);
        }
        if (d.showDoors)
        {
            if (d.rearDoorWidth > d.cargoWidth || d.rearDoorY > d.cargoLength ||
                d.sideDoorWidth+d.sideDoorFrontGap > d.cargoLength)
                throw regenError("Door opening reference does not fit the simplified cargo dimensions.",
                    ["rearDoorWidth", "rearDoorY", "sideDoorWidth", "sideDoorFrontGap", "cargoWidth", "cargoLength"]);
            doorOutline(context,id+"rearDoor","Rear door opening - provisional position",
                vector((d.cargoWidth-d.rearDoorWidth)/2,d.rearDoorY,d.rearDoorSill),
                vector(0,-1,0),vector(1,0,0),d.rearDoorWidth,d.rearDoorHeight);
            const sideStart = d.cargoLength-d.sideDoorFrontGap-d.sideDoorWidth;
            if (d.showLeftDoor)
                doorOutline(context,id+"leftDoor","Left sliding-door opening - provisional position",
                    vector(zero,sideStart,d.sideDoorSill),vector(1,0,0),vector(0,1,0),
                    d.sideDoorWidth,d.sideDoorHeight);
            if (d.showRightDoor)
                doorOutline(context,id+"rightDoor","Right sliding-door opening - provisional position",
                    vector(d.cargoWidth,sideStart,d.sideDoorSill),vector(1,0,0),vector(0,1,0),
                    d.sideDoorWidth,d.sideDoorHeight);
        }

        setVariable(context,"nv200_archRearOffset",d.archRearOffset);
        setVariable(context,"nv200_archLength",d.archLength);
        setVariable(context,"nv200_archHeight",d.archHeight);
        setVariable(context,"nv200_archGap",d.archGap);

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


    const check = function(ok is boolean, message is string) { if (!ok) throw regenError(message); };
    var results = [];
    for (var c = 0; c < 3; c += 1) {
        var d = DEFAULTS;
        d.showCushions = c == 1; d.layout = c == 1 ? "NIGHT" : "DAY";
        if (c != 1) d.cabinetHeight = 400*millimeter;
        if (c == 2) { d.wallThickness = 9*millimeter; d.frameThickness = 21*millimeter;
            d.memberWidth = 55*millimeter; d.insideRadius = 20*millimeter; }
        const id = makeId("skinRemoval" ~ c);
        nv200Interior(context,id,d);
        check(size(evaluateQuery(context,qBodyType(qCreatedBy(id,EntityType.BODY),BodyType.SOLID)))==
            (c == 1 ? 26 : 21),"Exactly three solids removed");
        const H = d.platformHeight-d.slatThickness;
        for (var item in [
            {"part":"longBench","side":"right","length":d.seatLength,"height":H,"bays":2},
            {"part":"crossBench","side":"right","length":d.cargoLength-d.seatLength,"height":H,"bays":1},
            {"part":"cabinet","side":"left","length":d.cabinetOuterLength,"height":d.cabinetHeight,"bays":2}
        ]) {
            const base = id+item.part+item.side;
            check(size(evaluateQuery(context,qCreatedBy(base+"layer0"+"plate",EntityType.BODY)))==0,"No cutout skin");
            const frame = qCreatedBy(base+"layer1"+"plate",EntityType.BODY);
            check(size(evaluateQuery(context,frame))==1,"Retained separate inner frame");
            const bay = (item.length-(item.bays+1)*d.memberWidth)/item.bays;
            const area = item.length*item.height-item.bays*
                (bay*(item.height-d.memberWidth)-(2-PI/2)*d.insideRadius^2);
            check(abs((evVolume(context,{"entities":frame})-area*d.frameThickness)/millimeter^3)<0.1,
                "Frame retains open-floor cutouts and original volume");
            const b = evBox3d(context,{"topology":frame,"tight":true});
            const expectedX = item.part == "cabinet" ? d.bedWidth+d.wallThickness :
                (item.part == "longBench" ? d.seatWidth : d.bedWidth-d.crossExtension)-d.wallThickness-d.frameThickness;
            check(abs((b.minCorner[0]-expectedX)/millimeter)<0.001,"Frame plane unchanged");
        }
        for (var part in ["longBench","crossBench","cabinet"]) {
            for (var end in ["rear","front"]) {
                const skin = qCreatedBy(id+part+end+"layer0"+"plate",EntityType.BODY);
                check(size(evaluateQuery(context,skin))==1,"Solid end skin retained");
                const b = evBox3d(context,{"topology":skin,"tight":true});
                const fullVolume = (b.maxCorner[0]-b.minCorner[0])*(b.maxCorner[1]-b.minCorner[1])*
                    (b.maxCorner[2]-b.minCorner[2]);
                check(abs((evVolume(context,{"entities":skin})-fullVolume)/millimeter^3)<0.1,
                    "End skin remains solid");
            }
        }
        check(size(evaluateQuery(context,qCreatedBy(id+"crossBench"+"left"+"layer0"+"plate",EntityType.BODY)))==1,
            "Closed cross-bench wall skin retained");
        check(abs((getVariable(context,"nv200_hatchHeight")-(H-d.memberWidth))/millimeter)<0.001,
            "Derived opening height now reaches floor");
        results = append(results,"PASS skin removal scenario " ~ c);
        opDeleteBodies(context,makeId("skinCleanup" ~ c),{"entities":qCreatedBy(id,EntityType.BODY)});
    }
    return results;
}
