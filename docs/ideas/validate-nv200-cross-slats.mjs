import fs from 'node:fs';
const source=fs.readFileSync('nv200-interior.fs','utf8');
// Onshape precondition annotations require printable ASCII; evaluator geometry tests do not enforce this.
if (/[^\x09\x0A\x0D\x20-\x7E]/.test(source)) throw new Error('FeatureScript source contains non-ASCII characters; UI annotations require printable ASCII.');
const adapted=source.replace(/^FeatureScript.*\nimport.*\n/,'').replace(/function (\w+)([\s\S]*?)\n\}/g,(m,n,b)=>'const '+n+' = function'+b+'\n};').replace('export const nv200Interior','const nv200Interior');
const checks=`
const check=function(ok is boolean,msg is string) { if(!ok) throw regenError(msg); };
const clear=function(tools is Query,targets is Query,label is string) {
 for(var clash in evCollision(context,{"tools":tools,"targets":targets}))
  check(clash["type"]!=ClashType.INTERFERE && clash["type"]!=ClashType.TARGET_IN_TOOL &&
   clash["type"]!=ClashType.TOOL_IN_TARGET && clash["type"]!=ClashType.ABUT_TOOL_IN_TARGET,label ~ " " ~ clash["type"]);
};
var results=[];
for(var c=0;c<12;c+=1) {
 var d=DEFAULTS; d.cabinetHeight=400*millimeter; d.daytime=c%2==0;
 if(c==2 || c==3) d.drawerExtended=true;
 if(c==4 || c==5) { d.longBenchWidth=620*millimeter; d.bedWidth=1110*millimeter;
  d.frameThickness=20*millimeter; d.platformHeight=430*millimeter; }
 if(c==6) { d.showSlats=false; d.showCushions=false; }
 if(c==7) { d.showSlats=false; d.showCrossSlats=true; }
 if(c==8 || c==9) { d.cargoLength=1880*millimeter; d.showCrossSlats=false; }
 if(c==10 || c==11) { d.toiletDepth=400*millimeter; d.toiletBayAllowance=30*millimeter; d.storageLidGap=3*millimeter; d.storageLidFingerDiameter=30*millimeter; }
 const id=makeId("crossCase" ~ c);
 nv200Interior(context,id,d);
 const p=crossSlatDimensions(d); const b=slidingBracketDimensions(d,p); const st=crossStopDimensions(d); const storage=crossStorageDimensions(d,p);
 const shift=d.daytime ? 0*millimeter:p.travel;
 const bracket=qCreatedBy(id+"crossBrackets",EntityType.BODY);
 check(size(evaluateQuery(context,bracket))==3,"Three cross brackets");
 const movingFrame=qCreatedBy(id+"crossSlats"+"movingFrame",EntityType.BODY);
 const frameBounds=evBox3d(context,{"topology":movingFrame,"tight":true});
 check(abs((frameBounds.maxCorner[0]-p.closedWidth-shift)/millimeter)<0.001,"Cross outer edge follows layout");
 check(abs((frameBounds.minCorner[1]-d.seatLength)/millimeter)<0.001 &&
  abs((frameBounds.maxCorner[1]-d.cargoLength)/millimeter)<0.001,"Cross frame depth unchanged");
 var moving=[movingFrame,qCreatedBy(id+"crossStops",EntityType.BODY),bracket];
 var fixedSlats=[];
 var previousEnd=d.seatLength+p.margin-d.slatSideGap;
 for(var i=0;i<p.count;i+=1) {
  const q=qCreatedBy(id+"crossSlats"+(i%2==1 ? "movingSlat" ~ i:"fixedSlat" ~ i),EntityType.BODY);
  check(size(evaluateQuery(context,q))==(d.showSlats?1:0),"Cross slat visibility");
  if(i%2==1) moving=append(moving,q); else fixedSlats=append(fixedSlats,q);
  if(d.showSlats) {
   const bounds=evBox3d(context,{"topology":q,"tight":true});
   check(abs((bounds.minCorner[1]-previousEnd-d.slatSideGap)/millimeter)<0.001,"Exact slat gap");
   previousEnd=bounds.maxCorner[1];
   if(i%2==1) {
    const lp=longSlatDimensions(d);
    const longOverlap=lp.closedWidth-lp.movingStart-lp.travel;
    check(abs((bounds.minCorner[0]-p.movingStart-shift)/millimeter)<0.001,"Shortened moving slat wall endpoint");
    check(abs((p.closedWidth-(bounds.minCorner[0]+p.travel-shift)-longOverlap)/millimeter)<0.001,"Cross extended overlap matches long bench");
    if(c==0) check(abs((bounds.maxCorner[0]-bounds.minCorner[0]-376*millimeter)/millimeter)<0.001,"Baseline cross moving slat length376mm");
   }
   check(abs((bounds.maxCorner[0]-(p.closedWidth+(i%2==1?shift:0*millimeter)))/millimeter)<0.001,"Slat aisle endpoint");
  }
 }
 if(d.showSlats) check(abs((previousEnd+p.margin-d.cargoLength)/millimeter)<0.001,"Slats fill cross bench depth including end margins");
 const deck=qCreatedBy(id+"crossSlats"+"deck",EntityType.BODY);
 const lid=qCreatedBy(id+"crossSlats"+"lid",EntityType.BODY);
 const divider=qCreatedBy(id+"crossPartition",EntityType.BODY);
 check(size(evaluateQuery(context,divider))==2,"Divider contains7mm skin and18mm frame");
 clear(divider,qSubtraction(qCreatedBy(id,EntityType.BODY),divider),"Divider must clear all other components");
 const divSkin=qCreatedBy(id+"crossPartition"+"layer0"+"plate",EntityType.BODY);
 const divFrame=qCreatedBy(id+"crossPartition"+"layer1"+"plate",EntityType.BODY);
 const ds=evBox3d(context,{"topology":divSkin,"tight":true});
 const df=evBox3d(context,{"topology":divFrame,"tight":true});
 check(abs((ds.maxCorner[0]-ds.minCorner[0]-d.wallThickness)/millimeter)<0.001,"Divider skin thickness follows walls");
 check(abs((df.maxCorner[0]-df.minCorner[0]-d.frameThickness)/millimeter)<0.001,"Divider frame thickness follows construction");
 // Shape checks catch a reversed opening cutter even when outer bounds and collisions look correct.
 const dw=df.maxCorner[1]-df.minCorner[1];
 const dh=df.maxCorner[2]-df.minCorner[2];
 const notchArea=2*d.frameThickness*d.memberWidth;
 const holeArea=(dw-2*d.memberWidth)*(dh-2*d.memberWidth)-(4-PI)*d.insideRadius^2;
 const expectedFrame=(dw*dh-notchArea-holeArea)*d.frameThickness;
 check(abs((evVolume(context,{"entities":divFrame})-expectedFrame)/expectedFrame)<1e-8,"Rectangular frame has full centre removed and60mm perimeter members");
 const expectedSkin=(dw*dh-notchArea)*d.wallThickness;
 check(abs((evVolume(context,{"entities":divSkin})-expectedSkin)/expectedSkin)<1e-8,"Separating skin has only the two beam recesses");
 const empty=makeId("dividerEmptyCentre" ~ c);
 fCuboid(context,empty+"solid",{"corner1":vector(df.minCorner[0]-millimeter,df.minCorner[1]+d.memberWidth+d.insideRadius,d.memberWidth+d.insideRadius),
  "corner2":vector(df.maxCorner[0]+millimeter,df.maxCorner[1]-d.memberWidth-d.insideRadius,dh-d.memberWidth-d.insideRadius)});
 clear(qCreatedBy(empty,EntityType.BODY),divFrame,"Centre of18mm frame must be empty");
 opDeleteBodies(context,empty+"cleanup",{"entities":qCreatedBy(empty,EntityType.BODY)});
 const bottom=makeId("dividerBottomRail" ~ c);
 fCuboid(context,bottom+"solid",{"corner1":vector(df.minCorner[0]+0.1*millimeter,df.minCorner[1]+0.1*millimeter,0.1*millimeter),
  "corner2":vector(df.maxCorner[0]-0.1*millimeter,df.maxCorner[1]-0.1*millimeter,d.memberWidth-0.1*millimeter)});
 opBoolean(context,bottom+"cut",{"tools":divFrame,"targets":qCreatedBy(bottom+"solid",EntityType.BODY),"operationType":BooleanOperationType.SUBTRACTION,"keepTools":true});
 check(size(evaluateQuery(context,qCreatedBy(bottom+"solid",EntityType.BODY)))==0,"Rectangle has continuous bottom rail");
 check(abs((p.fixedInner-ds.maxCorner[0]-d.toiletDepth-d.toiletBayAllowance)/millimeter)<0.001,"Toilet depth plus allowance reserved");
 // Solid skin closes across the storage/toilet boundary, including beside the end frames.
 const seal=makeId("dividerSeal" ~ c);
 fCuboid(context,seal+"solid",{"corner1":vector(ds.minCorner[0]+0.1*millimeter,p.startY+d.wallThickness+0.1*millimeter,0*millimeter),
  "corner2":vector(ds.maxCorner[0]-0.1*millimeter,p.endY-d.wallThickness-0.1*millimeter,storage.top-d.memberWidth-0.1*millimeter)});
 opBoolean(context,seal+"cut",{"tools":divSkin,"targets":qCreatedBy(seal+"solid",EntityType.BODY),"operationType":BooleanOperationType.SUBTRACTION,"keepTools":true});
 check(size(evaluateQuery(context,qCreatedBy(seal+"solid",EntityType.BODY)))==0,"Divider skin has no end bypass gaps");
 if(!d.showSlats) {
  check(size(evaluateQuery(context,deck))==0,"Shared visibility hides cross fixed deck");
  check(size(evaluateQuery(context,lid))==0,"Shared visibility hides removable lid");
  for(var k=0;k<p.count;k+=2)
   check(size(evaluateQuery(context,qCreatedBy(id+"crossSlats"+("lidSlat" ~ k),EntityType.BODY)))==0,"Shared visibility hides lid slats");
  check(size(evaluateQuery(context,qCreatedBy(id+"crossStops",EntityType.BODY)))==0,"Shared visibility hides plate stops");
  const lp=longSlatDimensions(d);
  for(var li=0;li<lp.count;li+=1)
   check(size(evaluateQuery(context,qCreatedBy(id+"longSlats"+(li%2==1?"movingSlat" ~ li:"fixedSlat" ~ li),EntityType.BODY)))==0,"Shared visibility hides long slats");
  check(size(evaluateQuery(context,movingFrame))>0,"Cross frame remains visible");
  check(size(evaluateQuery(context,qCreatedBy(id+"drawer"+"rearEnd",EntityType.BODY)))>0,"Drawer remains visible");
  check(size(evaluateQuery(context,qCreatedBy(id+"cushionD",EntityType.BODY)))==(d.showCushions?1:0),"Cushion visibility remains independent");
  results=append(results,"PASS shared slat/lid visibility case " ~ c);
  opDeleteBodies(context,makeId("crossCleanup" ~ c),{"entities":qCreatedBy(id,EntityType.BODY)});
  continue;
 }
 const db=evBox3d(context,{"topology":deck,"tight":true});
 const lb=evBox3d(context,{"topology":lid,"tight":true});
 check(abs((db.minCorner[0]-lb.maxCorner[0]-d.storageLidGap)/millimeter)<0.001,"Lid seam gap");
 check(norm(lb.minCorner-vector(storage.lidStart,storage.lidRear,storage.top))<0.001*millimeter &&
  norm(lb.maxCorner-vector(storage.lidEnd,storage.lidFront,storage.top+d.crossDeckThickness))<0.001*millimeter,"Lift-out lid bounds");
 var liftBodies=[lid];
 for(var k=0;k<p.count;k+=2) {
  const slat=qCreatedBy(id+"crossSlats"+("lidSlat" ~ k),EntityType.BODY);
  check(size(evaluateQuery(context,slat))==1,"Four lid slat sections present");
  const sb=evBox3d(context,{"topology":slat,"tight":true});
  check(sb.maxCorner[0]<=lb.maxCorner[0] && sb.minCorner[1]>=lb.minCorner[1] && sb.maxCorner[1]<=lb.maxCorner[1],"Attached slats fit lid perimeter");
  check(abs((sb.maxCorner[2]-d.platformHeight)/millimeter)<0.001,"Lid slats retain400mm surface");
  check(evDistance(context,{"side0":slat,"side1":lid}).distance<0.001*millimeter,"Lid slats sit on plywood");
  liftBodies=append(liftBodies,slat);
 }
 const lidAssembly=qUnion(liftBodies);
 const foam=qUnion([qCreatedBy(id+"cushionA",EntityType.BODY),qCreatedBy(id+"cushionB",EntityType.BODY),qCreatedBy(id+"cushionC1",EntityType.BODY),qCreatedBy(id+"cushionRear",EntityType.BODY),qCreatedBy(id+"cushionC2",EntityType.BODY),qCreatedBy(id+"cushionD",EntityType.BODY)]);
 const liftTargets=qSubtraction(qCreatedBy(id,EntityType.BODY),qUnion([lidAssembly,foam]));
 clear(lidAssembly,liftTargets,"Closed lid clears hardware, sliding slats and frames");
 // Lift vertically until the underside clears the entire slatted top; cushions must first be removed.
 const lift=makeId("lidLift" ~ c);
 fCuboid(context,lift+"solid",{"corner1":lb.minCorner,"corner2":vector(lb.maxCorner[0],lb.maxCorner[1],d.platformHeight+60*millimeter)});
 clear(qCreatedBy(lift,EntityType.BODY),liftTargets,"Unobstructed vertical lid extraction");
 opDeleteBodies(context,lift+"cleanup",{"entities":qCreatedBy(lift,EntityType.BODY)});
 for(var support in [divFrame,qCreatedBy(id+"crossBench"+"left"+"layer1"+"plate",EntityType.BODY),
   qCreatedBy(id+"crossBench"+"rear"+"layer1"+"plate",EntityType.BODY),qCreatedBy(id+"crossBench"+"front"+"layer1"+"plate",EntityType.BODY)])
  check(evDistance(context,{"side0":lid,"side1":support}).distance<0.001*millimeter,"Lid rests on all four supporting frames");
 const finger=makeId("fingerClear" ~ c);
 fCylinder(context,finger+"solid",{"bottomCenter":vector(storage.fingerX,storage.fingerY,storage.top-10*millimeter),
  "topCenter":vector(storage.fingerX,storage.fingerY,d.platformHeight+10*millimeter),"radius":d.storageLidFingerDiameter/2-0.1*millimeter});
 clear(qCreatedBy(finger,EntityType.BODY),qSubtraction(qCreatedBy(id,EntityType.BODY),foam),"Finger hole unobstructed through lid and slat gap");
 opDeleteBodies(context,finger+"cleanup",{"entities":qCreatedBy(finger,EntityType.BODY)});
 check(abs((db.maxCorner[2]-d.platformHeight+d.slatThickness)/millimeter)<0.001,"Slats remain at platform height");
 check(abs((db.minCorner[2]-d.platformHeight+d.slatThickness+d.crossDeckThickness)/millimeter)<0.001,"Deck underside and carcass height");
 const fixedFrameBounds=evBox3d(context,{"topology":qCreatedBy(id+"crossBench"+"right",EntityType.BODY),"tight":true});
 check(abs((fixedFrameBounds.maxCorner[2]-db.minCorner[2])/millimeter)<0.001,"Fixed carcass supports deck without overlap");
 check(size(evaluateQuery(context,qCreatedBy(id+"crossSlats"+"innerStrip",EntityType.BODY)))==0,"Cross bench has no redundant moving strip");
 const movingBodies=qUnion(moving);
 const all=qCreatedBy(id,EntityType.BODY);
 clear(deck,qSubtraction(all,deck),"Deck must meet frames and slats without overlap");
 if(d.showSlats) {
  check(size(evaluateQuery(context,qCreatedBy(id+"crossStops",EntityType.BODY)))==2,"Exactly two stop plates");
  for(var j=0;j<2;j+=1) {
   const plate=qCreatedBy(id+"crossStops"+("stop" ~ j)+"plate",EntityType.BODY);
   const fixed=qCreatedBy(id+"crossSlats"+("fixedSlat" ~ st.fixedIndices[j]),EntityType.BODY);
   const pb=evBox3d(context,{"topology":plate,"tight":true});
   check(abs((pb.maxCorner[0]-pb.minCorner[0]-d.stopPlateWidth)/millimeter)<0.001 &&
    abs((pb.maxCorner[1]-pb.minCorner[1]-d.stopPlateLength)/millimeter)<0.001,"100x22 plate orientation");
   check(abs((pb.minCorner[0]-st.x0-shift+d.stopPlateWidth/2)/millimeter)<0.001,"Plate follows slide");
   const mounted=qCreatedBy(id+"crossSlats"+("movingSlat" ~ st.movingIndices[j]),EntityType.BODY);
   const mb=evBox3d(context,{"topology":mounted,"tight":true});
   check(pb.minCorner[0]-d.stopRunningClearance>mb.minCorner[0] && pb.maxCorner[0]+d.stopRunningClearance<mb.maxCorner[0],"Mount pocket lies inside shortened slat length");
   check(evDistance(context,{"side0":plate,"side1":mounted}).distance<0.001*millimeter,"Plate remains attached against mounting pocket ceiling");
   check(evDistance(context,{"side0":plate,"side1":fixed}).distance<0.001*millimeter,"Plate contacts closed recess end at day/night limit");
   // The same plate shifted 1 mm beyond either limit MUST hit the fixed slat.
   const probe=makeId("stopOvertravel" ~ c ~ "p" ~ j);
   const over=d.daytime?-millimeter:millimeter;
   fCuboid(context,probe+"solid",{"corner1":pb.minCorner+vector(over,0*millimeter,0*millimeter),
    "corner2":pb.maxCorner+vector(over,0*millimeter,0*millimeter)});
   var hits=false;
   for(var clash in evCollision(context,{"tools":qCreatedBy(probe,EntityType.BODY),"targets":fixed}))
    if(clash["type"]==ClashType.INTERFERE) hits=true;
   check(hits,"Overtravel must be blocked by recess end");
   opDeleteBodies(context,probe+"cleanup",{"entities":qCreatedBy(probe,EntityType.BODY)});
   // The head projection envelope occupies only the attached half of each plate.
   const head=makeId("stopHead" ~ c ~ "p" ~ j);
   const mi=st.movingIndices[j];
   const edge=j==0?p.slats[mi].y:p.slats[mi].y+p.slats[mi].width;
   fCuboid(context,head+"solid",{"corner1":vector(pb.minCorner[0]-shift,j==0?edge:pb.minCorner[1],pb.minCorner[2]-d.stopHeadAllowance),
    "corner2":vector(pb.maxCorner[0]+p.travel-shift,j==0?pb.maxCorner[1]:edge,pb.minCorner[2])});
   check(evDistance(context,{"side0":qCreatedBy(head,EntityType.BODY),"side1":deck}).distance>=d.stopRunningClearance-0.001*millimeter,"Head envelope clears lid throughout travel");
   opDeleteBodies(context,head+"cleanup",{"entities":qCreatedBy(head,EntityType.BODY)});
  }
 } else check(size(evaluateQuery(context,qCreatedBy(id+"crossStops",EntityType.BODY)))==0,"Plate visibility follows cross slats");
 // An uninterrupted 1 mm bottom skin away from edge bracket reliefs proves stops never pierce the lid.
 const skin=makeId("deckSkin" ~ c);
 fCuboid(context,skin+"solid",{"corner1":vector(storage.fixedDeckStart,p.startY,db.minCorner[2]),
  "corner2":vector(p.fixedWidth-b.pocketDepth,p.endY,db.minCorner[2]+millimeter)});
 opBoolean(context,skin+"cut",{"tools":deck,"targets":qCreatedBy(skin+"solid",EntityType.BODY),
  "operationType":BooleanOperationType.SUBTRACTION,"keepTools":true});
 check(size(evaluateQuery(context,qCreatedBy(skin+"solid",EntityType.BODY)))==0,"Lid remains closed beneath the mechanism");
 const staticBodies=qSubtraction(qUnion([qBodyType(all,BodyType.SOLID),qBodyType(all,BodyType.SHEET)]),movingBodies);
 clear(movingBodies,staticBodies,"Cross moving assembly against all fixed geometry");
 // Full-travel bounding prisms conservatively contain every moving part at every position.
 var n=0;
 for(var body in evaluateQuery(context,movingBodies)) {
  const bounds=evBox3d(context,{"topology":body,"tight":true});
  const lo=bounds.minCorner-vector(shift,0*millimeter,0*millimeter);
  const hi=bounds.maxCorner+vector(p.travel-shift,0*millimeter,0*millimeter);
  const sweep=makeId("crossSweep" ~ c ~ "part" ~ n); n+=1;
  // Bracket boxes fill their elbow void; hardware sweeps are checked separately below.
  if(size(evaluateQuery(context,qIntersection([body,bracket])))==0) {
   fCuboid(context,sweep+"solid",{"corner1":lo,"corner2":hi});
   clear(qCreatedBy(sweep,EntityType.BODY),staticBodies,"Continuous full-travel assembly sweep");
   opDeleteBodies(context,sweep+"cleanup",{"entities":qCreatedBy(sweep,EntityType.BODY)});
  }
 }
 for(var i=0;i<3;i+=1) {
  const sweep=makeId("crossHardware" ~ c ~ "b" ~ i);
  fCuboid(context,sweep+"horizontal",{"corner1":vector(p.fixedWidth-d.bracketArm,b.centers[i]-d.bracketWidth/2,b.height-d.bracketThickness-b.headReach),
   "corner2":vector(p.fixedWidth+p.travel,b.centers[i]+d.bracketWidth/2,b.height)});
  fCuboid(context,sweep+"vertical",{"corner1":vector(p.fixedWidth-d.bracketThickness-b.headReach,b.centers[i]-d.bracketWidth/2,b.height-d.bracketArm),
   "corner2":vector(p.fixedWidth+p.travel,b.centers[i]+d.bracketWidth/2,b.height)});
  clear(qCreatedBy(sweep,EntityType.BODY),staticBodies,"Continuous screw/head/bend sweep");
  const distance=evDistance(context,{"side0":qCreatedBy(sweep,EntityType.BODY),"side1":qCreatedBy(id+"crossBench"+"right",EntityType.BODY)}).distance;
  check(distance>=d.bracketClearance-0.001*millimeter,"Bracket running clearance");
  opDeleteBodies(context,sweep+"cleanup",{"entities":qCreatedBy(sweep,EntityType.BODY)});
 }
 // The center of the toilet opening stays clear down to the floor in both support frames.
 const opening=makeId("toiletOpening" ~ c);
 fCuboid(context,opening+"solid",{"corner1":vector(p.fixedInner+0.1*millimeter,d.seatLength+d.memberWidth+30*millimeter,0*millimeter),
  "corner2":vector(d.bedWidth-0.1*millimeter,d.cargoLength-d.memberWidth-30*millimeter,b.height-d.crossDeckThickness-d.memberWidth-1*millimeter)});
 clear(qCreatedBy(opening,EntityType.BODY),qUnion([qCreatedBy(id+"crossBench"+"right",EntityType.BODY),movingFrame]),"Floor-level opening retained");
 opDeleteBodies(context,opening+"cleanup",{"entities":qCreatedBy(opening,EntityType.BODY)});
 if(c==0) {
  check(abs((storage.clearStorageWidth-327*millimeter)/millimeter)<0.001 && abs((storage.clearStorageDepth-530*millimeter)/millimeter)<0.001,"Baseline clear storage327x530");
  check(p.count==7 && abs((p.edgeWidth-75*millimeter)/millimeter)<0.001,"Seven slats with75mm end strips");
  check(abs((p.closedWidth-853*millimeter)/millimeter)<0.001 && abs((p.travel-217*millimeter)/millimeter)<0.001,"Baseline closed width and travel");
 }
 if(c==0) check(abs((p.travel+d.stopPlateWidth-239*millimeter)/millimeter)<0.001,"239 mm stop recess");
 if(c==8) check(p.count==7 && abs((p.margin-5*millimeter)/millimeter)<0.001,"600mm depth uses seven80mm slats with5mm end margins");
 results=append(results,"PASS cross case " ~ c ~ ": geometry, toilet opening, full moving assembly and hardware travel");
 opDeleteBodies(context,makeId("crossCleanup" ~ c),{"entities":all});
}
var bad=DEFAULTS; bad.stopPlateThickness=4*millimeter;
var rejected=false; try { crossStopDimensions(bad); } catch { rejected=true; }
check(rejected,"Thick plate that scrapes the deck must be rejected");
results=append(results,"PASS invalid hardware thickness rejected");
var invalid=DEFAULTS; invalid.toiletDepth=250*millimeter;
var invalidLid=false; try { crossStorageDimensions(invalid,crossSlatDimensions(invalid)); } catch { invalidLid=true; }
check(invalidLid,"Divider split that traps lid under moving slats must be rejected");
invalid=DEFAULTS; invalid.toiletDepth=800*millimeter;
var noStorage=false; try { crossStorageDimensions(invalid,crossSlatDimensions(invalid)); } catch { noStorage=true; }
check(noStorage,"Oversize toilet that consumes storage must be rejected");
results=append(results,"PASS invalid divider/lid dimensions rejected");
return results;
}`;
fs.writeFileSync('nv200-cross-slat-validation.fs','function(context,queries) {\n'+adapted+'\n'+checks);
console.log('Generated cross bench full-travel test.');
