import fs from 'node:fs';
const s=fs.readFileSync('nv200-interior.fs','utf8');
const a=s.replace(/^FeatureScript.*\nimport.*\n/,'').replace(/function (\w+)([\s\S]*?)\n\}/g,(m,n,b)=>'const '+n+' = function'+b+'\n};').replace('export const nv200Interior','const nv200Interior');
const checks=`
const check=function(ok is boolean,msg is string) { if(!ok) throw regenError(msg); };
const clear=function(tools is Query,targets is Query,label is string) {
 for(var clash in evCollision(context,{"tools":tools,"targets":targets}))
  check(clash["type"]!=ClashType.INTERFERE && clash["type"]!=ClashType.TARGET_IN_TOOL &&
    clash["type"]!=ClashType.TOOL_IN_TARGET && clash["type"]!=ClashType.ABUT_TOOL_IN_TARGET,label ~ " " ~ clash["type"]);
};
var results=[];
for(var c=0;c<8;c+=1) {
 var d=DEFAULTS; d.cabinetHeight=400*millimeter; d.daytime=c%2==0;
 d.drawerExtended=c==2 || c==3;
 if(c==4 || c==5) {
  d.longBenchWidth=620*millimeter; d.frameThickness=20*millimeter;
  d.bracketThickness=3*millimeter; d.bracketClearance=2*millimeter;
  d.bracketHeadAllowance=4*millimeter; d.bracketBendRadius=4*millimeter;
 }
 if(c==6 || c==7) { d.showSlats=false; d.showCushions=false; }
 const id=makeId("bracketCase" ~ c);
 nv200Interior(context,id,d);
 const p=longSlatDimensions(d); const b=slideBracketDimensions(d);
 const shift=d.daytime ? 0*millimeter:p.travel;
 const brackets=qCreatedBy(id+"slideBrackets",EntityType.BODY);
 check(size(evaluateQuery(context,brackets))==3,"Exactly three bracket bodies");
 var moving=[qCreatedBy(id+"longSlats"+"movingFrame",EntityType.BODY),qCreatedBy(id+"longSlats"+"innerStrip",EntityType.BODY)];
 for(var i=1;i<p.count;i+=2) moving=append(moving,qCreatedBy(id+"longSlats"+("movingSlat" ~ i),EntityType.BODY));
 const all=qCreatedBy(id,EntityType.BODY);
 const staticBodies=qSubtraction(qUnion([qBodyType(all,BodyType.SOLID),qBodyType(all,BodyType.SHEET)]),qUnion(append(moving,brackets)));
 clear(brackets,qSubtraction(all,brackets),"Bracket intersects generated assembly");
 for(var i=0;i<3;i+=1) {
  const part=qCreatedBy(id+"slideBrackets"+("bracket" ~ i),EntityType.BODY);
  const bounds=evBox3d(context,{"topology":part,"tight":true});
  check(norm(bounds.minCorner-vector(d.longBenchWidth+shift-d.bracketArm,b.centers[i]-d.bracketWidth/2,b.height-d.bracketArm))<0.001*millimeter,"Bracket minimum bounds");
  check(norm(bounds.maxCorner-vector(d.longBenchWidth+shift,b.centers[i]+d.bracketWidth/2,b.height))<0.001*millimeter,"Bracket maximum bounds");
  const sweep=makeId("sweep" ~ c ~ "b" ~ i);
  // Two boxes contain the complete translated bracket, bend and screw-head envelopes at EVERY slide position.
  fCuboid(context,sweep+"horizontal",{"corner1":vector(d.longBenchWidth-d.bracketArm,b.centers[i]-d.bracketWidth/2,b.height-d.bracketThickness-b.headReach),
   "corner2":vector(d.longBenchWidth+p.travel,b.centers[i]+d.bracketWidth/2,b.height)});
  fCuboid(context,sweep+"vertical",{"corner1":vector(d.longBenchWidth-d.bracketThickness-b.headReach,b.centers[i]-d.bracketWidth/2,b.height-d.bracketArm),
   "corner2":vector(d.longBenchWidth+p.travel,b.centers[i]+d.bracketWidth/2,b.height)});
  const swept=qCreatedBy(sweep,EntityType.BODY);
  clear(swept,staticBodies,"Continuous bracket/head sweep collides with stationary geometry");
  const distance=evDistance(context,{"side0":swept,"side1":qCreatedBy(id+"longBench"+"right",EntityType.BODY)}).distance;
  check(distance>=d.bracketClearance-0.001*millimeter,"Running clearance through fixed frame");
  opDeleteBodies(context,sweep+"cleanup",{"entities":swept});
 }
 results=append(results,"PASS case " ~ c ~ ": three brackets, bounds, assembly and continuous hardware sweep clear");
 opDeleteBodies(context,makeId("bracketCleanup" ~ c),{"entities":all});
}
var shortTravel=DEFAULTS;
shortTravel.bedWidth=640*millimeter;
var rejected=false;
try { slideBracketDimensions(shortTravel); } catch { rejected=true; }
check(rejected,"Short travel must reject bracket/inner-strip interference");
return append(results,"PASS short travel rejected before geometry creation");
}`;
fs.writeFileSync('nv200-bracket-validation.fs','function(context,queries) {\n'+a+'\n'+checks);
console.log('Generated bracket continuous-travel verification.');
