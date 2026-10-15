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
 const rearSlat=qCreatedBy(id+"longSlats"+"fixedSlat0",EntityType.BODY);
 const rearSlatBounds=evBox3d(context,{"topology":rearSlat,"tight":true});
 check(abs((rearSlatBounds.minCorner[1]-headerBounds.minCorner[1])/millimeter)<0.001,
  "Rear-most slat must be flush with rear header");
 check(abs((rearSlatBounds.minCorner[2]-headerBounds.maxCorner[2])/millimeter)<0.001,
  "Rear-most slat underside must meet header top");
 const slatCount=getVariable(context,"nv200_longSlatCount");
 for(var n=0;n<slatCount;n+=1) {
  const slat=qCreatedBy(id+"longSlats"+(n%2==0 ? "fixedSlat" ~ n : "movingSlat" ~ n),EntityType.BODY);
  const sb=evBox3d(context,{"topology":slat,"tight":true});
  check(abs((sb.minCorner[1]-n*(d.slatWidth+d.slatSideGap))/millimeter)<0.001,
   "Slat sequence must start at rear plane and retain its running gaps");
  check(abs((sb.maxCorner[1]-sb.minCorner[1]-d.slatWidth)/millimeter)<0.001 &&
   abs((sb.maxCorner[2]-sb.minCorner[2]-d.slatThickness)/millimeter)<0.001,
   "Existing timber width and thickness retained");
  check(sb.maxCorner[1]<=d.seatLength+0.001*millimeter,"Slats must fit bench length");
 }
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
   {"q":fixedSupport,"name":"aisle datum support","offset":7*millimeter},
   {"q":rearSlat,"name":"rear-most slat","offset":5*millimeter}];
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
  results=append(results,"PASS deliberate displacements of drawer, header, all three supports and rear-most slat detected");
  results=append(results,"Baseline rear Y (mm): drawer=" ~ panelBounds.minCorner[1]/millimeter ~
   ", header=" ~ headerBounds.minCorner[1]/millimeter ~ ", slat=" ~ rearSlatBounds.minCorner[1]/millimeter ~
   ", fixed aisle support=" ~ fixedBounds.minCorner[1]/millimeter ~ ", inner support=" ~ innerBounds.minCorner[1]/millimeter);
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
