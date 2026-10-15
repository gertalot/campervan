annotation { "Feature Type Name" : "CabinetHeightValidation" }
export const cabinetHeightValidation = defineFeature(function(context is Context, id is Id, definition is map)
precondition {}
{
    for (var layout in [NV200Layout.DAY, NV200Layout.NIGHT])
    {
        for (var heightMm in [1300, 1200])
        {
            const caseId = id + (layout ~ heightMm);
            var d = DEFAULTS;
            d.layout = layout;
            // For the 1300 case, omit the new input as in an existing saved feature.
            if (heightMm == 1300)
                d.cabinetHeight = undefined;
            else
                d.cabinetHeight = heightMm * millimeter;
            nv200Interior(context, caseId, d);
            const cabinet = qCreatedBy(caseId + "cabinet", EntityType.BODY);
            const solids = qBodyType(qCreatedBy(caseId, EntityType.BODY), BodyType.SOLID);
            if (size(evaluateQuery(context, solids)) != 8)
                throw regenError("Expected 8 separate solids");
            const b = evBox3d(context, {"topology": cabinet, "tight": true});
            if (norm(b.minCorner / millimeter - vector(1070,0,0)) > 0.001 ||
                norm(b.maxCorner / millimeter - vector(1500,1190,heightMm)) > 0.001)
                throw regenError("Cabinet bounds mismatch");
            const expectedVolume = 4579.5 * centimeter^2 * heightMm * millimeter;
            if (abs((evVolume(context, {"entities":cabinet}) - expectedVolume) / centimeter^3) > 0.001)
                throw regenError("Cabinet volume mismatch");
            println("PASS " ~ layout ~ " cabinet " ~ heightMm ~ " mm: bounds, volume, 8 separate solids");
            opDeleteBodies(context, caseId + "cleanup", {"entities":qCreatedBy(caseId,EntityType.BODY)});
        }
    }
}, {});
