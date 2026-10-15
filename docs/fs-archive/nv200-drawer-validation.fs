function(context,queries) {

// X left-to-right, Y rear-to-cab, Z up. Existing layout lengths and new construction lengths carry explicit units.
// Fixed plywood carcasses and longitudinal sliding slats are detailed. Cross top, joints and vehicle fit remain unresolved.
// Each bench has its own seat and infill cushions; long backrests sit front-to-back in daytime.
// longBenchWidth supersedes seatWidth and the faulty benchWidth field (60 mm in the saved instance).
// Explicit millimetre UI defaults and unitful runtime defaults both initialise the approved 600 mm width.


const DEFAULTS = {
    "layout" : "DAY",
    "showCushions" : true,
    "showSlats" : true,
    "drawerExtended" : false,
    "drawerPly" : 12 * millimeter,
    "drawerLength" : 1200 * millimeter,
    "drawerHeight" : 290 * millimeter,
    "drawerSideBand" : 90 * millimeter,
    "drawerFrameHeight" : 300 * millimeter,
    "drawerMountBand" : 100 * millimeter,
    "drawerArchClearance" : 10 * millimeter,
    "drawerFloorClearance" : 10 * millimeter,
    "drawerRearSetback" : 50 * millimeter,
    "slideThickness" : 19 * millimeter,
    "slideHeight" : 53 * millimeter,
    "slideTravel" : 1215 * millimeter,
    "cargoWidth" : 150 * centimeter,
    "cargoLength" : 186 * centimeter,
    "bedWidth" : 107 * centimeter,
    "longBenchWidth" : 600 * millimeter,
    "seatLength" : 128 * centimeter,
    "platformHeight" : 400 * millimeter,
    "wallThickness" : 7 * millimeter,
    "frameThickness" : 18 * millimeter,
    "memberWidth" : 60 * millimeter,
    "insideRadius" : 25 * millimeter,
    "slatThickness" : 18 * millimeter,
    "slatWidth" : 80 * millimeter,
    "slatSideGap" : 5 * millimeter,
    "slidingStripWidth" : 40 * millimeter,
    "ledgeWidth" : 25 * millimeter,
    "stripEndClearance" : 2 * millimeter,
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
    const infillWidth = (d.bedWidth - d.longBenchWidth) / 2;
    const p = {
        "baseHeight" : d.platformHeight,
        "infillWidth" : infillWidth,
        "crossSeatWidth" : d.bedWidth - infillWidth,
        "crossInfillWidth" : infillWidth,
        "dLength" : d.cargoLength - d.seatLength,
        "c2Length" : d.cargoLength - d.seatLength,
        "c1Length" : d.seatLength,
        "cabinetDepth" : d.cargoWidth - d.bedWidth,
        "aisleWidth" : d.bedWidth - d.longBenchWidth - d.frameThickness,
        "innerGap" : d.seatLength - d.cabinetOuterLength,
        "outerGap" : d.seatLength - d.cabinetOuterLength,
        "frontUnbacked" : d.bedWidth - infillWidth - d.foamThickness
    };
    if (p.baseHeight <= 0 * centimeter)
        throw regenError("Platform height must be positive.", ["platformHeight"]);
    if (d.bedWidth <= d.longBenchWidth || d.cargoWidth <= d.bedWidth)
        throw regenError("Require cargo width > bed width > long bench width.",
            ["cargoWidth", "bedWidth", "longBenchWidth"]);
    if (2*d.foamThickness >= d.longBenchWidth || d.foamThickness >= p.crossSeatWidth)
        throw regenError("Both long backrests must fit front-to-back on the long seat, and the short backrest must fit on the cross seat.",
            ["foamThickness","longBenchWidth","bedWidth"]);
    if (d.seatLength <= 0 * millimeter || p.dLength <= 0 * millimeter)
        throw regenError("Long bench length must be positive and remain shorter than the cargo length.",
            ["seatLength", "cargoLength"]);
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
        const offset = layer == 0 || access ? 0*millimeter : d.wallThickness;
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
    frameX, y, length, height, combineFrontPosts is boolean, d is map)
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
    const archFront = d.archRearOffset+d.archLength;
    // Adjacent uprights retain both member widths: 60 + 60 = 120 mm at baseline.
    const postWidth = combineFrontPosts ? 2*w : w;
    const postStart = combineFrontPosts ? length-postWidth : archFront+d.archClearance;
    const postEnd = postStart+postWidth;
    const frontClearance = postStart-archFront;
    if (rearSupportEnd < w || frontClearance < d.archClearance ||
        (!combineFrontPosts && postEnd > length-w))
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
    const openings = combineFrontPosts ? [[rearSupportEnd,postStart]] : [[rearSupportEnd,postStart],[postEnd,length-w]];
    for (var i = 0; i < size(openings); i += 1)
    {
        const bounds = openings[i];
        const gap = bounds[1]-bounds[0];
        if (gap > 0*millimeter)
        {
            const radius = d.insideRadius;
            if (gap <= 2*radius || height-w <= 2*radius)
                throw regenError("Wall-side opening is too small for the specified corner radius.", parameterIds);
            const endClearance = min(rearClearance,frontClearance);
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
    setVariable(context,variablePrefix ~ "_frontArchClearance",frontClearance);
    setVariable(context,variablePrefix ~ "_rearCornerSetback",setback);
    setVariable(context,variablePrefix ~ "_wallPostStart",y+postStart);
    setVariable(context,variablePrefix ~ "_wallPostEnd",y+postEnd);
};


/** Closed-bottom frame with a continuous slide mounting band and two access openings. */
const slideMountFrame = function(context is Context, id is Id, name is string, origin is Vector,
    along is Vector, normal is Vector, length, height, d is map)
{
    const w=d.memberWidth;
    const r=d.insideRadius;
    const bay=(length-3*w)/2;
    if (bay <= 2*r || height-w-d.drawerMountBand <= 2*r)
        throw regenError("Slide frame needs room for its lower band, upper band and rounded openings.",
            ["drawerFrameHeight","drawerMountBand","memberWidth","insideRadius","seatLength"]);
    fCuboid(context,id+"plate",{"corner1":origin,
        "corner2":origin+along*length+normal*d.frameThickness+vector(0,0,1)*height});
    const plate=qCreatedBy(id+"plate",EntityType.BODY);
    for (var i=0; i<2; i+=1)
    {
        const cutId=id+("opening" ~ i);
        const start=w+i*(bay+w);
        openingTool(context,cutId,origin-normal*millimeter,along,normal,
            start,start+bay,d.drawerMountBand,height-w,r,d.frameThickness+2*millimeter);
        opBoolean(context,cutId+"subtract",{"tools":qCreatedBy(cutId+"solid",EntityType.BODY),
            "targets":plate,"operationType":BooleanOperationType.SUBTRACTION});
    }
    nameAndColor(context,plate,name,color(0.88,0.61,0.25));
};

/** Width follows the arch, mounting frame, runners and fixed aisle frame. */
const drawerDimensions = function(d is map) returns map
{
    const f=d.frameThickness;
    const p=d.drawerPly;
    const total=d.wallThickness+f;
    const frameX=(d.cargoWidth-d.archGap)/2+d.drawerArchClearance;
    const left=frameX+f+d.slideThickness;
    const right=d.longBenchWidth-f-d.slideThickness;
    const headerBottom=d.platformHeight-d.slatThickness-d.memberWidth;
    const rearLeft=d.rearCornerRadius+d.rearCornerAllowance;
    const drawerTop=d.drawerFloorClearance+d.drawerHeight;
    const frameEnd=d.seatLength-total;
    const slideBottom=d.drawerFloorClearance+p;
    // Retain the saved runner length/setback inputs; tray rear face is fixed to the bench datum Y=0.
    const trayLength=d.drawerRearSetback+d.drawerLength;
    if (d.memberWidth < f)
        throw regenError("Rear posts must cover the full rear header thickness and offset.",
            ["memberWidth","wallThickness","frameThickness"]);
    const ids=["longBenchWidth","archGap","drawerArchClearance","frameThickness","slideThickness",
        "drawerPly","drawerLength","drawerHeight","drawerRearSetback","drawerFloorClearance"];
    if (right-left <= 2*p || d.drawerLength <= 2*d.memberWidth+2*d.insideRadius ||
        d.drawerHeight <= d.drawerSideBand+d.insideRadius || d.drawerSideBand <= p)
        throw regenError("Drawer dimensions leave insufficient room inside the tray or its U-shaped sides.",ids);
    if (d.drawerRearSetback < total || trayLength >= frameEnd)
        throw regenError("Closed drawer and slides must clear the cab-end frame.",ids);
    if (drawerTop >= headerBottom || d.drawerFrameHeight >= d.platformHeight-d.slatThickness-2*f)
        throw regenError("Drawer or mounting frame reaches the rear header or sliding-bed guide ledges.",
            ["drawerHeight","drawerFloorClearance","drawerFrameHeight","platformHeight","slatThickness","memberWidth"]);
    if (slideBottom+d.slideHeight > min(d.drawerMountBand,d.drawerFloorClearance+d.drawerSideBand))
        throw regenError("Slide profile must fit on both continuous mounting bands.",
            ["slideHeight","drawerMountBand","drawerSideBand","drawerFloorClearance","drawerPly"]);
    if (frameX <= max(total,rearLeft) || frameX+f >= right)
        throw regenError("Internal slide frame must clear the rear corner and leave a drawer opening.",ids);
    if (d.slideTravel < d.drawerLength || d.slideTravel >= 2*d.drawerLength)
        throw regenError("Slide travel must provide full extension while retaining telescoping overlap.",["slideTravel","drawerLength"]);
    if (d.drawerRearSetback < 50*millimeter)
        throw regenError("The selected slide needs 50 mm rear allowance for its release lever.",["drawerRearSetback"]);
    return {"frameX":frameX,"left":left,"right":right,"width":right-left,
        "insideWidth":right-left-2*p,"insideLength":trayLength-2*p,"trayLength":trayLength,
        "frameStart":0*millimeter,"frameEnd":frameEnd,"slideBottom":slideBottom,
        "rearHeaderClearance":headerBottom-drawerTop};
};

/** Rear opening spans the slide gap. Existing aisle post and raised inner-frame post support the header. */
const drawerRearFrame = function(context is Context, id is Id, width, height, d is map)
{
    const p=drawerDimensions(d);
    makeBlock(context,id+"plate","Long bench rear header - clear drawer exit",
        vector(p.frameX+d.frameThickness,p.frameStart,height-d.memberWidth),
        vector(width-d.frameThickness,p.frameStart+d.frameThickness,height),color(0.88,0.61,0.25));
};

/** Five separate plywood tray pieces; bottom is flush with the underside of all four walls. */
const rearDrawer = function(context is Context, id is Id, d is map)
{
    const p=drawerDimensions(d);
    const zero=0*millimeter;
    const ply=d.drawerPly;
    const shift=d.drawerExtended ? d.slideTravel : zero;
    const rear=p.frameStart-shift;
    const front=rear+p.trayLength;
    const bottom=d.drawerFloorClearance;
    const top=bottom+d.drawerHeight;
    const wood=color(0.78,0.65,0.44);
    slideMountFrame(context,id+"mountFrame","Drawer fixed wall-side slide mounting frame",
        vector(p.frameX,p.frameStart,zero),vector(0,1,0),vector(1,0,0),
        p.frameEnd-p.frameStart,d.drawerFrameHeight,d);
    // Raised rear post reaches slat level before the moving tie strip begins at the corner setback.
    const bedFrameTop=d.platformHeight-d.slatThickness;
    const postEnd=d.memberWidth;
    if (postEnd >= d.rearCornerRadius+d.rearCornerAllowance)
        throw regenError("Raised drawer-frame rear post must end before the bed tie strip and guide ledge.",
            ["memberWidth","rearCornerRadius","rearCornerAllowance"]);
    makeBlock(context,id+"raisedPost","Drawer fixed internal frame - raised rear post",
        vector(p.frameX,zero,d.drawerFrameHeight),
        vector(p.frameX+d.frameThickness,postEnd,bedFrameTop),color(0.88,0.61,0.25));
    opBoolean(context,id+"joinPost",{"tools":qUnion([
        qCreatedBy(id+"mountFrame"+"plate",EntityType.BODY),qCreatedBy(id+"raisedPost",EntityType.BODY)]),
        "operationType":BooleanOperationType.UNION});
    nameAndColor(context,qCreatedBy(id+"mountFrame"+"plate",EntityType.BODY),
        "Drawer fixed wall-side slide frame with raised rear post",color(0.88,0.61,0.25));
    makeBlock(context,id+"bottom","Drawer bottom - flush inset",
        vector(p.left+ply,rear+ply,bottom),vector(p.right-ply,front-ply,bottom+ply),wood);
    for (var i=0; i<2; i+=1)
    {
        const x=i==0 ? p.left : p.right-ply;
        const side=id+("side" ~ i);
        makeBlock(context,side+"plate",i==0 ? "Drawer wall-side U panel" : "Drawer aisle-side U panel",
            vector(x,rear,bottom),vector(x+ply,front,top),wood);
        const cut=side+"opening";
        openingTool(context,cut,vector(x-millimeter,rear,bottom),vector(0,1,0),vector(1,0,0),
            d.memberWidth,p.trayLength-d.memberWidth,d.drawerSideBand,d.drawerHeight+2*d.insideRadius,
            d.insideRadius,ply+2*millimeter);
        opBoolean(context,cut+"subtract",{"tools":qCreatedBy(cut+"solid",EntityType.BODY),
            "targets":qCreatedBy(side+"plate",EntityType.BODY),"operationType":BooleanOperationType.SUBTRACTION});
    }
    makeBlock(context,id+"rearEnd","Drawer rear end panel",
        vector(p.left+ply,rear,bottom),vector(p.right-ply,rear+ply,top),wood);
    makeBlock(context,id+"frontEnd","Drawer cab-facing end panel",
        vector(p.left+ply,front-ply,bottom),vector(p.right-ply,front,top),wood);
    // Simple telescoping clearance envelopes only. Three equal thickness zones are visual placeholders.
    // The entire pair occupies the specified 19 mm installation gap on each side.
    for (var side=0; side<2; side+=1)
    {
        const gapStart=side==0 ? p.left-d.slideThickness : p.right;
        for (var stage=0; stage<3; stage+=1)
        {
            const x=gapStart+(side==0 ? stage : 2-stage)*d.slideThickness/3;
            const y=d.drawerRearSetback-shift*stage/2;
            makeBlock(context,id+("slide" ~ side ~ "stage" ~ stage),
                (side==0 ? "Left" : "Right") ~ " drawer slide - clearance envelope stage " ~ stage,
                vector(x,y,p.slideBottom),vector(x+d.slideThickness/3,y+d.drawerLength,p.slideBottom+d.slideHeight),
                color(0.52,0.56,0.60));
        }
    }
    for (var key,value in p) setVariable(context,"nv200_drawer_" ~ key,value);
    setVariable(context,"nv200_drawerPosition",shift);
    setVariable(context,"nv200_drawerInternalHeight",d.drawerHeight-ply);
    setVariable(context,"nv200_drawerFloorTop",bottom+ply);
};

/** End walls fit the actual side build-ups: exposed frames sit at the nominal aisle boundary. */
const benchCarcass = function(context is Context, id is Id, name is string, x, y, width, length,
    height, longBays is number, rightAccess is boolean, archSide is string, d is map)
{
    const zero = 0*millimeter;
    const parameterIds = archSide == "RIGHT" ?
        ["wallThickness", "frameThickness", "memberWidth", "insideRadius", "cabinetHeight",
         "cabinetOuterLength", "cargoWidth", "bedWidth", "rearCornerRadius", "rearCornerAllowance"] :
        ["wallThickness", "frameThickness", "memberWidth", "insideRadius", "platformHeight",
         "slatThickness", "longBenchWidth", "seatLength", "cargoLength", "bedWidth"];
    const total = d.wallThickness+d.frameThickness;
    const leftInset = archSide == "RIGHT" && rightAccess ? d.frameThickness : total;
    const rightInset = archSide != "RIGHT" && rightAccess ? d.frameThickness : total;
    if (width <= leftInset+rightInset || length <= 2*total)
        throw regenError("Carcass width and length must leave room between opposing walls and frames.",
            parameterIds);
    const variablePrefix = archSide == "RIGHT" ? "nv200_cabinet" : "nv200";
    if (archSide == "LEFT")
        wheelArchFrame(context,id+"left",name,variablePrefix,x+d.wallThickness,y,length,height,false,d);
    else
        benchWall(context, id+"left", name ~ (archSide == "RIGHT" ? " aisle side" : " wall side"),
            vector(x,y,zero),vector(0,1,0),vector(1,0,0),length,height,longBays,
            archSide == "RIGHT" && rightAccess,d,parameterIds);
    if (archSide == "RIGHT")
        wheelArchFrame(context,id+"right",name,variablePrefix,x+width-total,y,length,height,true,d);
    else if (archSide == "LEFT")
        slideMountFrame(context,id+"right","Long bench fixed aisle frame - slide mounting band",
            vector(x+width,y+length,zero),vector(0,-1,0),vector(-1,0,0),length,height,d);
    else
        benchWall(context, id+"right", name ~ " aisle side", vector(x+width,y+length,zero),
            vector(0,-1,0), vector(-1,0,0), length,height,longBays,rightAccess,d,parameterIds);
    const setback = max(total,d.rearCornerRadius+d.rearCornerAllowance);
    const rearLeft = archSide == "LEFT" ? setback : leftInset;
    const rearRight = archSide == "RIGHT" ? setback : rightInset;
    if (archSide == "LEFT")
        drawerRearFrame(context,id+"rear",width,height,d);
    else benchWall(context, id+"rear", name ~ " rear end", vector(x+width-rearRight,y,zero),
        vector(-1,0,0), vector(0,1,0), width-rearLeft-rearRight,height,1,false,d,parameterIds);
    benchWall(context, id+"front", name ~ " cab end", vector(x+leftInset,y+length,zero),
        vector(1,0,0), vector(0,-1,0), width-leftInset-rightInset,height,1,false,d,parameterIds);
};

/** Shared dimensions for the sliding comb; invalid travel is rejected rather than resizing parts. */
const longSlatDimensions = function(d is map) returns map
{
    const f = d.frameThickness;
    const wallInner = d.wallThickness+f;
    const fixedInner = d.longBenchWidth-f;
    const closedWidth = d.longBenchWidth+f;
    const travel = d.bedWidth-closedWidth;
    const stripClosed = fixedInner-d.slidingStripWidth-travel;
    const setback = max(wallInner,d.rearCornerRadius+d.rearCornerAllowance);
    const stripRear = setback+d.stripEndClearance;
    const stripFront = d.seatLength-wallInner-d.stripEndClearance;
    const pitch = d.slatWidth+d.slatSideGap;
    var count = floor((d.seatLength-d.slatSideGap)/pitch);
    if (count % 2 == 0) count -= 1;
    const margin = (d.seatLength-(count*d.slatWidth+(count-1)*d.slatSideGap))/2;
    if (travel <= 0*millimeter || stripClosed < wallInner+d.slatSideGap-0.00001*millimeter)
        throw regenError("The inner strip cannot retract between the fixed frames. Reduce bed width or strip width, or increase fixed bench width.",
            ["longBenchWidth","bedWidth","frameThickness","wallThickness","slidingStripWidth","slatSideGap"]);
    if (count < 3 || count > 101)
        throw regenError("Long bench must accommodate between 3 and 101 interleaving slats.",
            ["seatLength","slatWidth","slatSideGap"]);
    if (d.stripEndClearance >= d.ledgeWidth || setback+d.ledgeWidth >= d.seatLength-wallInner-d.ledgeWidth)
        throw regenError("Ledges need positive strip bearing and clear space between them.",
            ["ledgeWidth","stripEndClearance","seatLength","rearCornerRadius","rearCornerAllowance"]);
    for (var i = 0; i < count; i += 2)
    {
        const slatY = margin+i*pitch;
        if (slatY < setback && slatY >= d.memberWidth)
            throw regenError("A shortened rear slat misses the rear end support. Adjust slat width, side clearance or bench length.",
                ["slatWidth","slatSideGap","seatLength","rearCornerRadius","rearCornerAllowance"]);
    }
    const firstMoving = margin+pitch;
    const lastMoving = margin+(count-2)*pitch;
    if (firstMoving+d.slatWidth <= stripRear || lastMoving >= stripFront)
        throw regenError("The end moving slats must overlap the inner strip. Adjust slat spacing or rear corner setback.",
            ["slatWidth","slatSideGap","seatLength","rearCornerRadius","rearCornerAllowance","stripEndClearance"]);
    if (d.frameThickness*2 > d.memberWidth || d.platformHeight-d.slatThickness-2*f <= d.archHeight)
        throw regenError("Strip and ledges need room within the top band and above the wheel arch.",
            ["frameThickness","memberWidth","platformHeight","slatThickness","archHeight"]);
    return {
        "count":count,"margin":margin,"pitch":pitch,"travel":travel,"closedWidth":closedWidth,
        "wallInner":wallInner,"fixedInner":fixedInner,"stripClosed":stripClosed,
        "stripRear":stripRear,"stripFront":stripFront,"rearLedge":setback
    };
};

/** Separate fixed and moving slats, a copied aisle frame, an inner stop strip and two fixed ledges. */
const longitudinalSlats = function(context is Context, id is Id, d is map)
{
    const p = longSlatDimensions(d);
    const zero = 0*millimeter;
    const f = d.frameThickness;
    const h = d.platformHeight-d.slatThickness;
    const shift = d.layout == "NIGHT" ? p.travel : zero;
    const wood = color(0.72,0.52,0.32);
    const movingWood = color(0.87,0.70,0.43);
    for (var i = 0; d.showSlats && i < p.count; i += 1)
    {
        const y = p.margin+i*p.pitch;
        const moving = i % 2 == 1;
        const start = moving ? p.stripClosed+shift :
            (y < p.rearLedge ? drawerDimensions(d).frameX : d.wallThickness);
        const end = moving ? p.closedWidth+shift : d.longBenchWidth;
        makeBlock(context,id+(moving ? "movingSlat" ~ i : "fixedSlat" ~ i),
            (moving ? "Long bench moving slat " : "Long bench fixed slat ") ~ (i+1),
            vector(start,y,h),vector(end,y+d.slatWidth,d.platformHeight),moving ? movingWood : wood);
    }
    benchWall(context,id+"movingFrame","Long bench moving aisle support",
        vector(p.closedWidth+shift,d.seatLength,zero),vector(0,-1,0),vector(-1,0,0),
        d.seatLength,h,2,true,d,
        ["seatLength","platformHeight","slatThickness","memberWidth","insideRadius","frameThickness"]);
    makeBlock(context,id+"innerStrip","Long bench moving inner tie / extension stop",
        vector(p.stripClosed+shift,p.stripRear,h-f),
        vector(p.stripClosed+shift+d.slidingStripWidth,p.stripFront,h),movingWood);
    // Rear ledge is inset to the corner setback, joining the retained wall post and fixed aisle frame.
    makeBlock(context,id+"rearLedge","Long bench fixed rear inset guide ledge",
        vector(p.wallInner,p.rearLedge,h-2*f),
        vector(p.fixedInner,p.rearLedge+d.ledgeWidth,h-f),wood);
    makeBlock(context,id+"frontLedge","Long bench fixed cab-end guide ledge",
        vector(p.wallInner,d.seatLength-p.wallInner-d.ledgeWidth,h-2*f),
        vector(p.fixedInner,d.seatLength-p.wallInner,h-f),wood);
    setVariable(context,"nv200_longSlatCount",p.count);
    setVariable(context,"nv200_longSlideTravel",p.travel);
    setVariable(context,"nv200_longSlidePosition",shift);
    setVariable(context,"nv200_longBenchClosedWidth",p.closedWidth);
    setVariable(context,"nv200_longBenchCurrentWidth",p.closedWidth+shift);
    setVariable(context,"nv200_longStripClosedClearance",p.stripClosed-p.wallInner);
    setVariable(context,"nv200_longSlatGap",d.slatSideGap);
    setVariable(context,"nv200_longFixedSlatGap",d.slatWidth+2*d.slatSideGap);
};

/** Read the actual rear-facing planar boundary, including any applied body transforms. */
const rearFaceY = function(context is Context, bodies is Query, heightBand is array)
{
    var rear=undefined;
    for (var face in evaluateQuery(context,qGeometry(qOwnedByBody(bodies,EntityType.FACE),GeometryType.PLANE)))
    {
        const facePlane=evPlane(context,{"face":face});
        const bounds=evBox3d(context,{"topology":face,"tight":true});
        if (abs(dot(facePlane.normal,vector(0,1,0))) > 1-1e-8 &&
            bounds.minCorner[2] <= heightBand[0]+0.001*millimeter &&
            bounds.maxCorner[2] >= heightBand[1]-0.001*millimeter)
            if (rear == undefined || facePlane.origin[1] < rear) rear=facePlane.origin[1];
    }
    if (rear == undefined) throw regenError("Rear alignment check cannot find a planar rear face.");
    return rear;
};

/** Runs on the real generated bodies, with the current instance's inputs, on every regeneration. */
const verifyRearAlignment = function(context is Context, id is Id, d is map)
{
    const top=d.platformHeight-d.slatThickness;
    const supportBand=[top-d.memberWidth,top];
    const drawerBand=[d.drawerFloorClearance,d.drawerFloorClearance+d.drawerHeight];
    const datum=rearFaceY(context,qCreatedBy(id+"longBench"+"right",EntityType.BODY),supportBand);
    const shift=d.drawerExtended ? d.slideTravel : 0*millimeter;
    const checks=[
        {"name":"drawer rear panel","query":qCreatedBy(id+"drawer"+"rearEnd",EntityType.BODY),"shift":shift,"band":drawerBand},
        {"name":"rear crossbeam","query":qCreatedBy(id+"longBench"+"rear",EntityType.BODY),"shift":0*millimeter,"band":supportBand},
        {"name":"internal rear support","query":qCreatedBy(id+"drawer"+"mountFrame"+"plate",EntityType.BODY),"shift":0*millimeter,"band":supportBand},
        {"name":"moving bed rear support","query":qCreatedBy(id+"longSlats"+"movingFrame",EntityType.BODY),"shift":0*millimeter,"band":supportBand}
    ];
    for (var item in checks)
    {
        const offset=rearFaceY(context,item.query,item.band)+item.shift-datum;
        if (abs(offset) > 0.001*millimeter)
            throw regenError("Rear alignment failed: " ~ item.name ~ " is offset " ~
                (offset/millimeter) ~ " mm from the aisle support rear face.");
    }
};

annotation {
    "Feature Type Name" : "NV200Interior",
    "Feature Type Description" : "Plywood bench carcasses with editable wall, frame and member dimensions. " ~
        "Platform height is the top of the slats, below the foam. Long bench has two vertical access openings. " ~
        "Layout moves the longitudinal bed and cushions. Rear drawer extension is independent. Cross top, joints and toilet deployment remain undetailed."
}
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
            annotation { "Name" : "Slat thickness", "Description" : "Timber slat thickness; top remains at platform height." }
            isLength(definition.slatThickness, { (meter) : [0.001, 0.018, 0.1], (millimeter) : 18 } as LengthBoundSpec);
        }
        annotation { "Group Name" : "Long bench sliding slats", "Collapsed By Default" : false }
        {
            annotation { "Name" : "Show slats", "Default" : true,
                "Description" : "Show fixed and moving timber slats. Turn off to see the support frames, guides and drawer." }
            definition.showSlats is boolean;
            annotation { "Name" : "Slat width" }
            isLength(definition.slatWidth, { (meter) : [0.01,0.08,0.3], (millimeter) : 80 } as LengthBoundSpec);
            annotation { "Name" : "Clearance each side of moving slat",
                "Description" : "Fixed-slat clear gap = slat width + twice this clearance (90 mm at baseline)." }
            isLength(definition.slatSideGap, { (meter) : [0.0001,0.005,0.03], (millimeter) : 5 } as LengthBoundSpec);
            annotation { "Name" : "Flat inner strip width", "Description" : "Thickness follows inner frame plywood; stops against fixed aisle frame when extended." }
            isLength(definition.slidingStripWidth, { (meter) : [0.005,0.04,0.2], (millimeter) : 40 } as LengthBoundSpec);
            annotation { "Name" : "Guide ledge width", "Description" : "18 mm plywood at baseline. Rear ledge inset to clear the rear corner." }
            isLength(definition.ledgeWidth, { (meter) : [0.005,0.025,0.1], (millimeter) : 25 } as LengthBoundSpec);
            annotation { "Name" : "Strip end clearance" }
            isLength(definition.stripEndClearance, { (meter) : [0.0001,0.002,0.02], (millimeter) : 2 } as LengthBoundSpec);
        }
        annotation { "Group Name" : "Rear storage drawer", "Collapsed By Default" : false }
        {
            annotation { "Name" : "Extend rear drawer", "Default" : false,
                "Description" : "Independent of the daytime/nighttime bed setting." }
            definition.drawerExtended is boolean;
            annotation { "Name" : "Drawer plywood thickness" }
            isLength(definition.drawerPly, { (meter) : [0.001, 0.012, 3], (millimeter) : 12 } as LengthBoundSpec);
            annotation { "Name" : "Slide closed length", "Description" : "Tray length = slide length + slide rear setback; drawer rear is flush with the bench." }
            isLength(definition.drawerLength, { (meter) : [0.001, 1.2, 3], (millimeter) : 1200 } as LengthBoundSpec);
            annotation { "Name" : "Drawer overall height" }
            isLength(definition.drawerHeight, { (meter) : [0.001, 0.29, 3], (millimeter) : 290 } as LengthBoundSpec);
            annotation { "Name" : "Drawer side lower band" }
            isLength(definition.drawerSideBand, { (meter) : [0.001, 0.09, 3], (millimeter) : 90 } as LengthBoundSpec);
            annotation { "Name" : "Internal slide frame height" }
            isLength(definition.drawerFrameHeight, { (meter) : [0.001, 0.3, 3], (millimeter) : 300 } as LengthBoundSpec);
            annotation { "Name" : "Fixed slide mounting band height" }
            isLength(definition.drawerMountBand, { (meter) : [0.001, 0.1, 3], (millimeter) : 100 } as LengthBoundSpec);
            annotation { "Name" : "Slide frame clearance from wheel arch" }
            isLength(definition.drawerArchClearance, { (meter) : [0.001, 0.01, 3], (millimeter) : 10 } as LengthBoundSpec);
            annotation { "Name" : "Drawer clearance above floor" }
            isLength(definition.drawerFloorClearance, { (meter) : [0.001, 0.01, 3], (millimeter) : 10 } as LengthBoundSpec);
            annotation { "Name" : "Slide rear setback", "Description" : "Release-lever allowance behind the flush drawer face; moves the slides, not the drawer face." }
            isLength(definition.drawerRearSetback, { (meter) : [0.001, 0.05, 3], (millimeter) : 50 } as LengthBoundSpec);
            annotation { "Name" : "Slide side clearance" }
            isLength(definition.slideThickness, { (meter) : [0.001, 0.019, 3], (millimeter) : 19 } as LengthBoundSpec);
            annotation { "Name" : "Slide profile height" }
            isLength(definition.slideHeight, { (meter) : [0.001, 0.053, 3], (millimeter) : 53 } as LengthBoundSpec);
            annotation { "Name" : "Drawer full extension travel" }
            isLength(definition.slideTravel, { (meter) : [0.001, 1.215, 3], (millimeter) : 1215 } as LengthBoundSpec);
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
        annotation { "Name" : "Long bench fixed width", "Description" : "Moving frame adds its thickness to the closed width; nighttime outer edge follows full bed width." }
        isLength(definition.longBenchWidth, {
            (millimeter) : [100, 600, 10000], (meter) : 0.6, (centimeter) : 60
        } as LengthBoundSpec);
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
        const w = d.longBenchWidth;
        const l = d.seatLength;
        const bw = d.bedWidth;
        const end = d.cargoLength;
        const h = d.platformHeight + d.foamThickness;
        const t = d.foamThickness;
        const z = p.baseHeight;
        const backTop = h + p.infillWidth;
        
        const panelHeight = z-d.slatThickness;
        const crossWidth = p.crossSeatWidth;
        if (crossWidth <= w)
            throw regenError("Cross bench fixed width must exceed the long bench width.", ["longBenchWidth", "bedWidth"]);
        benchCarcass(context, id+"longBench", "Long bench", zero,zero,w,l,panelHeight,2,true,"LEFT",d);
        benchCarcass(context, id+"crossBench", "Cross bench", zero,l,crossWidth,p.dLength,panelHeight,1,true,"NONE",d);
        longitudinalSlats(context,id+"longSlats",d);
        rearDrawer(context,id+"drawer",d);
        verifyRearAlignment(context,id,d);
        setVariable(context, "nv200_panelHeight", panelHeight);
        setVariable(context, "nv200_crossBenchFixedWidth", crossWidth);
        setVariable(context, "nv200_crossExtension", p.crossInfillWidth);
        setVariable(context, "nv200_longHatchWidth", (l-3*d.memberWidth)/2);
        setVariable(context, "nv200_hatchHeight", panelHeight-d.memberWidth-d.drawerMountBand);
        setVariable(context, "nv200_wallThickness", d.wallThickness);
        setVariable(context, "nv200_frameThickness", d.frameThickness);
        setVariable(context, "nv200_memberWidth", d.memberWidth);
        if (d.showCushions)
        {
            makeBlock(context, id + "cushionA", "Long seat cushion - layout reference",
                vector(zero, zero, z), vector(w, l, h), color(0.19, 0.47, 0.63));
            makeBlock(context, id + "cushionD", "Cross bench seat cushion",
                vector(zero, l, z), vector(crossWidth, end, h), color(0.26, 0.57, 0.70));

            if (d.layout == "DAY")
            {
                makeBlock(context, id + "cushionB", "Long bench wall-side backrest / inner infill",
                    vector(zero, zero, h), vector(t, l, backTop), color(0.83, 0.52, 0.22));
                makeBlock(context, id + "cushionC1", "Long bench seat-side backrest / outer infill",
                    vector(t, zero, h), vector(2*t, l, backTop), color(0.46, 0.61, 0.35));
                makeBlock(context, id + "cushionC2", "Cross bench side backrest / extension infill",
                    vector(zero, l, h), vector(t, end, h+p.crossInfillWidth), color(0.64, 0.43, 0.66));
            }
            else
            {
                const split = w + p.infillWidth;
                makeBlock(context, id + "cushionB", "Long bench wall-side backrest / inner infill",
                    vector(w, zero, z), vector(split, l, h), color(0.83, 0.52, 0.22));
                makeBlock(context, id + "cushionC1", "Long bench seat-side backrest / outer infill",
                    vector(split, zero, z), vector(bw, l, h), color(0.46, 0.61, 0.35));
                makeBlock(context, id + "cushionC2", "Cross bench side backrest / extension infill",
                    vector(crossWidth, l, z), vector(bw, end, h), color(0.64, 0.43, 0.66));
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

const check=function(ok is boolean,msg is string) { if(!ok) throw regenError(msg); };
const boundsCheck=function(q is Query,lo is Vector,hi is Vector,label is string) {
 const b=evBox3d(context,{"topology":q,"tight":true});
 check(norm(b.minCorner-lo)<0.001*millimeter && norm(b.maxCorner-hi)<0.001*millimeter,label);
};
const noInterference=function(a is Query,b is Query,label is string) {
 for(var c in evCollision(context,{"tools":a,"targets":b}))
   check(c["type"]!=ClashType.INTERFERE,label);
};
var results=[];
for(var c=0;c<9;c+=1) {
 var d=DEFAULTS; d.cabinetHeight=400*millimeter; d.showCushions=true;
 if(c==1 || c==3) d.layout="NIGHT";
 if(c==2 || c==3) d.drawerExtended=true;
 if(c==4) { d.platformHeight=430*millimeter; d.longBenchWidth=620*millimeter; d.drawerPly=15*millimeter; }
 if(c==5) { d.seatLength=1300*millimeter; d.slatWidth=80*millimeter; d.drawerHeight=280*millimeter; }
 if(c==7) d.wallThickness=4*millimeter;
 if(c==8) d.wallThickness=10*millimeter;
 if(c==6) {
  d.longBenchWidth=undefined; d.benchWidth=60*millimeter; d.seatWidth=570*millimeter;
  d.drawerExtended=undefined;
  d.drawerPly=undefined;
  d.drawerLength=undefined;
  d.drawerHeight=undefined;
  d.drawerSideBand=undefined;
  d.drawerFrameHeight=undefined;
  d.drawerMountBand=undefined;
  d.drawerArchClearance=undefined;
  d.drawerFloorClearance=undefined;
  d.drawerRearSetback=undefined;
  d.slideThickness=undefined;
  d.slideHeight=undefined;
  d.slideTravel=undefined;
 }
 const id=makeId("drawerCase" ~ c);
 nv200Interior(context,id,d);
 if(c==6) { d=DEFAULTS; d.cabinetHeight=400*millimeter; }
 const p=drawerDimensions(d);
 const r=id+"drawer";
 const y=-(d.drawerExtended ? d.slideTravel : 0*millimeter);
 const z=d.drawerFloorClearance;
 const ply=d.drawerPly;
 const bottom=qCreatedBy(r+"bottom",EntityType.BODY);
 boundsCheck(bottom,vector(p.left+ply,y+ply,z),
  vector(p.right-ply,y+p.trayLength-ply,z+ply),"Inset bottom dimensions");
 check(size(evaluateQuery(context,qCreatedBy(id+"longBench"+"rear"+"layer0",EntityType.BODY)))==0,
  "Rear outer panel removed");
 const innerFrame=qCreatedBy(r+"mountFrame"+"plate",EntityType.BODY);
 boundsCheck(innerFrame,vector(p.frameX,p.frameStart,0*millimeter),
  vector(p.frameX+d.frameThickness,p.frameEnd,d.platformHeight-d.slatThickness),"Internal frame bounds");
 const tray=qUnion([bottom,qCreatedBy(r+"side0",EntityType.BODY),qCreatedBy(r+"side1",EntityType.BODY),
  qCreatedBy(r+"rearEnd",EntityType.BODY),qCreatedBy(r+"frontEnd",EntityType.BODY)]);
 boundsCheck(qCreatedBy(r+"rearEnd",EntityType.BODY),vector(p.left+ply,y,z),
  vector(p.right-ply,y+ply,z+d.drawerHeight),"Drawer rear face flush at Y=0 when retracted");
 boundsCheck(qCreatedBy(r+"frontEnd",EntityType.BODY),
  vector(p.left+ply,d.drawerRearSetback+d.drawerLength+y-ply,z),
  vector(p.right-ply,d.drawerRearSetback+d.drawerLength+y,z+d.drawerHeight),"Cab end retained");
 for(var side=0;side<2;side+=1) {
  const rail=qCreatedBy(r+("slide" ~ side ~ "stage0"),EntityType.BODY);
  const rb=evBox3d(context,{"topology":rail,"tight":true});
  check(abs((rb.minCorner[1]-d.drawerRearSetback)/millimeter)<0.001,"Fixed slide setback unchanged");
  check(abs((rb.maxCorner[1]-rb.minCorner[1]-d.drawerLength)/millimeter)<0.001,"Slide length unchanged");
 }
 const fixed=qBodyType(qUnion([qCreatedBy(id+"longBench",EntityType.BODY),qCreatedBy(id+"crossBench",EntityType.BODY),
  qCreatedBy(id+"leftArch",EntityType.BODY),innerFrame,qCreatedBy(id+"longSlats",EntityType.BODY)]),BodyType.SOLID);
 noInterference(tray,fixed,"Drawer must clear fixed structure and bed in case " ~ c);
 const allDrawer=qBodyType(qCreatedBy(r,EntityType.BODY),BodyType.SOLID);
 const slideParts=qSubtraction(allDrawer,qUnion([tray,innerFrame]));
 noInterference(slideParts,qUnion([tray,fixed]),"Slide clearance envelope intersects wood");
 // Five plywood pieces meet without overlapping; validate all pairs.
 const pieces=[bottom,qCreatedBy(r+"side0",EntityType.BODY),qCreatedBy(r+"side1",EntityType.BODY),
  qCreatedBy(r+"rearEnd",EntityType.BODY),qCreatedBy(r+"frontEnd",EntityType.BODY)];
 for(var i=0;i<5;i+=1) for(var j=i+1;j<5;j+=1)
  noInterference(pieces[i],pieces[j],"Drawer plywood pieces overlap");
 var bedMoving=[qCreatedBy(id+"longSlats"+"innerStrip",EntityType.BODY),
  qCreatedBy(id+"longSlats"+"movingFrame",EntityType.BODY)];
 for(var i=1;i<getVariable(context,"nv200_longSlatCount");i+=2)
  bedMoving=append(bedMoving,qCreatedBy(id+"longSlats"+("movingSlat" ~ i),EntityType.BODY));
 noInterference(qUnion(bedMoving),qUnion([allDrawer,qCreatedBy(id+"longBench",EntityType.BODY)]),
  "Bed moving parts collide with drawer or fixed frame");
 const cushion=qCreatedBy(id+"cushionA",EntityType.BODY);
 const cb=evBox3d(context,{"topology":cushion,"tight":true});
 check(abs((cb.maxCorner[0]-cb.minCorner[0]-d.longBenchWidth)/millimeter)<0.001,"Seat width follows bench");
 check(abs((getVariable(context,"nv200_infillWidth")-(d.bedWidth-d.longBenchWidth)/2)/millimeter)<0.001,
  "Backrests compensate for seat width");
 const back=qCreatedBy(id+"cushionB",EntityType.BODY);
 const bb=evBox3d(context,{"topology":back,"tight":true});
 const dim=d.layout=="DAY" ? bb.maxCorner[2]-bb.minCorner[2] : bb.maxCorner[0]-bb.minCorner[0];
 check(abs((dim-(d.bedWidth-d.longBenchWidth)/2)/millimeter)<0.001,"Physical backrest dimension");
 const rearFrame=qCreatedBy(id+"longBench"+"rear",EntityType.BODY);
 check(size(evaluateQuery(context,rearFrame))==1,"Single rear header and jamb part");

 // Independent assembly contract: shared rear plane and real support contact areas.
 const headerBounds=evBox3d(context,{"topology":rearFrame,"tight":true});
 const fixedSupport=qCreatedBy(id+"longBench"+"right",EntityType.BODY);
 const fixedBounds=evBox3d(context,{"topology":fixedSupport,"tight":true});
 const innerBounds=evBox3d(context,{"topology":innerFrame,"tight":true});
 const panelBounds=evBox3d(context,{"topology":qCreatedBy(r+"rearEnd",EntityType.BODY),"tight":true});
 const movingBounds=evBox3d(context,{"topology":qCreatedBy(id+"longSlats"+"movingFrame",EntityType.BODY),"tight":true});
 check(abs((headerBounds.minCorner[1]-fixedBounds.minCorner[1])/millimeter)<0.001,"Header flush to aisle post");
 check(abs((innerBounds.minCorner[1]-fixedBounds.minCorner[1])/millimeter)<0.001,"Internal post rear alignment");
 check(abs((movingBounds.minCorner[1]-fixedBounds.minCorner[1])/millimeter)<0.001,"Moving support rear alignment");
 check(abs((panelBounds.minCorner[1]+(d.drawerExtended ? d.slideTravel : 0*millimeter)-fixedBounds.minCorner[1])/millimeter)<0.001,
  "Drawer rear aligned to support when retracted");
 check(abs((headerBounds.minCorner[0]-innerBounds.maxCorner[0])/millimeter)<0.001 &&
       abs((headerBounds.maxCorner[0]-fixedBounds.minCorner[0])/millimeter)<0.001,
  "Header spans between support faces");
 for(var support in [innerFrame,fixedSupport]) {
  var faceContact=false;
  for(var contact in evCollision(context,{"tools":rearFrame,"targets":support})) {
   check(contact["type"]!=ClashType.INTERFERE,"Header penetrates support");
   if(contact["type"]==ClashType.ABUT_NO_CLASS) faceContact=true;
  }
  check(faceContact,"Header must contact both supports");
 }
 verifyRearAlignment(context,id,d);

 if(c<4 || c==6) {
  check(abs((p.width-376*millimeter)/millimeter)<0.001,"376 external width");
  check(abs((p.insideWidth-352*millimeter)/millimeter)<0.001,"352 internal width");
  check(abs((getVariable(context,"nv200_infillWidth")-235*millimeter)/millimeter)<0.001,"235 backrests");
  check(abs((getVariable(context,"nv200_longSlideTravel")-452*millimeter)/millimeter)<0.001,"452 bed travel");
 }

 if(c==0) {
  const probes=[{"q":rearFrame,"name":"crossbeam","offset":7*millimeter},
   {"q":qCreatedBy(r+"rearEnd",EntityType.BODY),"name":"drawer","offset":50*millimeter},
   {"q":innerFrame,"name":"internal support","offset":7*millimeter},
   {"q":qCreatedBy(id+"longSlats"+"movingFrame",EntityType.BODY),"name":"moving support","offset":7*millimeter},
   {"q":fixedSupport,"name":"aisle datum support","offset":7*millimeter}];
  for(var n=0;n<size(probes);n+=1) {
   const probe=probes[n];
   opTransform(context,makeId("misalign" ~ n),{"bodies":probe.q,
    "transform":transform(vector(0*millimeter,probe.offset,0*millimeter))});
   var detected=false;
   try { verifyRearAlignment(context,id,d); } catch { detected=true; }
   check(detected,"Alignment test missed deliberately displaced " ~ probe.name);
   opTransform(context,makeId("restoreAlignment" ~ n),{"bodies":probe.q,
    "transform":transform(vector(0*millimeter,-probe.offset,0*millimeter))});
   verifyRearAlignment(context,id,d);
  }
  results=append(results,"PASS deliberate displacements of drawer, header and all three supports detected");
 }

 if(c==0) {
  // Sweep drawer through its rear opening, including the rounded header corner.
  for(var step=1;step<=5;step+=1) {
   opTransform(context,makeId("drawerMotion" ~ step),{"bodies":tray,
    "transform":transform(vector(0*millimeter,-d.slideTravel/5,0*millimeter))});
   noInterference(tray,fixed,"Intermediate drawer motion collision");
  }
  // Move tray back and sweep bed over complete internal drawer assembly.
  opTransform(context,makeId("drawerReturn"),{"bodies":tray,
   "transform":transform(vector(0*millimeter,d.slideTravel,0*millimeter))});
  for(var step=1;step<=4;step+=1) {
   opTransform(context,makeId("bedMotion" ~ step),{"bodies":qUnion(bedMoving),
    "transform":transform(vector((d.bedWidth-d.longBenchWidth-d.frameThickness)/4,0*millimeter,0*millimeter))});
   noInterference(qUnion(bedMoving),allDrawer,"Intermediate bed motion collision");
  }
  results=append(results,"PASS 5 drawer travel positions and 4 bed travel positions");
 }
 results=append(results,"PASS geometry case " ~ c);
 opDeleteBodies(context,makeId("drawerCleanup" ~ c),{"entities":qCreatedBy(id,EntityType.BODY)});
}
for(var c=0;c<8;c+=1) {
 var d=DEFAULTS;
 if(c==0) d.drawerLength=1250*millimeter;
 if(c==1) d.drawerHeight=320*millimeter;
 if(c==2) d.drawerFrameHeight=350*millimeter;
 if(c==3) d.drawerSideBand=60*millimeter;
 if(c==4) d.longBenchWidth=200*millimeter;
 if(c==5) { d.memberWidth=36*millimeter; d.wallThickness=50*millimeter; }
 if(c==6) d.drawerLength=500*millimeter;
 if(c==7) d.drawerRearSetback=30*millimeter;
 var rejected=false;
 try { drawerDimensions(d); } catch { rejected=true; }
 check(rejected,"Invalid drawer dimensions rejected " ~ c);
}
return append(results,"PASS 8 invalid drawer parameter combinations rejected");

}
