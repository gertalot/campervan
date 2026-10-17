# Measuring Gert's NV200

The goal is an interior envelope for furniture clearance, including the finished ceiling and existing trim.
Start with the easy measurements below; no trim removal is needed. Record millimetres and photograph endpoints.
Leave inaccessible measurements blank rather than estimating them silently.

## Establish repeatable references

- Use the flat cargo floor as Z = 0. Note whether this is metal, an existing covering or a fitted floor.
- Mark a transverse line at the cargo-floor rear threshold; this is the measurement Y = 0. Positive Y goes toward cab.
- Mark a longitudinal centreline, with a square or equal offsets from matching body features.
- Measure left and right distances from that line separately. These can be mapped to the model's X coordinates later.
- Record the offset between the threshold and the closed hatch's innermost surface. They are not the same datum.

Use a tape, straightedge, square and masking tape. A plumb line helps transfer high points to the floor.
Keep normal driving seat positions fixed while measuring. Note seat recline, floor covering and whether doors are shut.
For the cab floor, seats and headliner, follow the [cab measurement sequence](cab.md#small-measurement-set-to-resolve-the-remaining-uncertainty)
using these same datums.

## First visit: the measurements that resolve most uncertainty

| Measurement | How to record it |
| --- | --- |
| Bed rear gap | Closed hatch inner surface to mattress rear edge; owner estimates 70–100 for the upright solar panel |
| Usable length | Threshold to seat backs at floor, bed-top and cabinet-top heights; both sides |
| Width | At floor, 400, 800 and 1200 above floor, at the stations below |
| Finished ceiling | Height at centreline and 300 / 600 to each side, at each station |
| Wheel houses | Rear and front Y, maximum Z, inward-most X on each side |
| Rear aperture | Clear width at sill, middle and top; height at centre and both sides; sill Z |
| Sliding openings | Each opening's front/rear Y, sill Z, width and height; record rounded corners |
| Existing trim | Largest intrusion where furniture approaches panels, handles or pillars |

Choose stations at the rear aperture, wheel-house centre, rear edge of the sliding opening, and just behind the seats.
Record their actual Y distances; do not force them onto presumed brochure positions. At a pillar or bulge, add a
nearby station on each side of the obstruction. Width should be measured horizontally, not along a sloping panel.

Use this repeatable record for each section:

| Y from threshold | Z above floor | Left distance from centreline | Right distance from centreline | Surface / note |
| --- | --- | --- | --- | --- |
| | | | | |

For roof points, record Y, sideways distance from centreline and ceiling Z. Record the underside of ribs or lining
where that is the actual clearance limit. The lining should not be inferred by subtracting 3mm from catalogue height.

## Ceiling bows

Number the visible bows from rear to front. Include the rear header and cab header separately.
For each accessible member, measure:

- Rear and front edges from the same rear-threshold Y datum; centre position is their average.
- Fore–aft width including flanges, and width of the lower face if different.
- Floor-to-underside height at the centreline and 300 / 600mm to either side.
- Drop below the adjacent roof skin at those same points, where exposed.
- End positions where the bow meets the side roof rails, and any brackets projecting below it.

Also record whether the fitted plywood passes below the bows or fits between them. Do not remove lining just to
complete the table; mark hidden dimensions unknown. A photo showing the whole ceiling establishes the bow count
and distinguishes any seat-belt reinforcement from the narrow bows.

| Member | Rear Y | Front Y | Underside Z at centre | Drop below roof | Notes |
| --- | --- | --- | --- | --- | --- |
| Rear header | | | | | |
| Rear bow | | | | | |
| Middle bow | | | | | |
| Front bow | | | | | |
| Cab header | | | | | |

## Second pass: curves and door motion

For a curved wall, hold a vertical straightedge at a recorded sideways offset and measure horizontal gaps to the
surface at several heights. For the roof, use a horizontal straightedge and measure upward gaps across its width.
A cardboard contour template can help at a tight corner; include a ruler in a square-on photograph.

For the tailgate, record hinge-axis height and Y if accessible, closed inner-panel depth, and lowest open-door height
above the cargo floor. Photograph the hinge area and door side-on, closed and fully open. The gas struts and handle can
intrude farther than the broad door panel. We can approximate the leaf first and add those obstacles where relevant.

For each sliding door, photograph closed, just clear of the opening and fully open. Measure outward displacement and
rearward travel of the same marked point. Also record the gap between the open door and van side. This gives a useful
motion envelope without reverse-engineering the complete roller mechanism.

Measure wheel-house longitudinal profiles at the wall and inner edge if the furniture needs a close fit. A single
rounded box cannot capture taper or asymmetric front/rear shoulders reliably.

## Using the results

The main editable controls under **Vehicle references** map to these measurements:

| Measurement | Sidebar control |
| --- | --- |
| Main cargo width, with endpoints recorded | Floor outline → Width (body and layout) |
| Rear datum to chosen cab boundary | Body length; keep Furniture layout length separate |
| Bare roof centre height, if accessible | Bare roof height |
| Width where wall turns into roof | Side walls → Roof shoulder width |
| Height where the lower wall starts leaning inward | Side walls → Taper starts above floor |
| Centre roof height minus shoulder height | Roof → Bare roof → Crown rise |
| Bow centre positions and fore–aft widths | Roof → Roof bows → Position / Fore–aft width |
| Roof-to-bow underside distance at centre | Roof → Roof bows → Centre depth |
| Bow underside centre height minus height at roof shoulders | Roof → Roof bows → Underside crown rise |
| Actual lining sheet thickness | Roof → Finished ceiling → Plywood thickness |
| Front edge of each side aperture relative to body front | Side walls → Left wall / Right wall → Door setback |
| Rear aperture widths, height and corner extent | Rear opening controls |
| Wheel-house bounds and rounded crown | Wheel arches controls |

Measure wall width at cabinet-top and roof-shoulder heights before using the scribed cabinet outlines for fabrication.
Its contours follow the estimated body and ceiling. If measured left/right or front/rear profiles differ, retain
those readings; they are evidence to add another section, not values to average away to fit the symmetric model.

Record whether a value is measured, taken from Nissan documentation or estimated. Keep approximate readings rounded
to the precision actually achieved. Owner measurements with clear endpoints take precedence for this van's fit.
Once the broad envelope is fitted, remeasure only locations where the furniture is close to an obstruction.
