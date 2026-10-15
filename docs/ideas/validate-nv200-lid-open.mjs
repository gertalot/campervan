import fs from 'node:fs';
const source=fs.readFileSync('nv200-interior.fs','utf8');
if (/[^\x09\x0A\x0D\x20-\x7E]/.test(source)) throw new Error('FeatureScript UI annotations require ASCII.');
const adapted=source.replace(/^FeatureScript.*\nimport.*\n/,'').replace(/function (\w+)([\s\S]*?)\n\}/g,(m,n,b)=>'const '+n+' = function'+b+'\n};').replace('export const nv200Interior','const nv200Interior');
const checks=`
const check=function(ok is boolean,msg is string) {if(!ok) throw regenError(msg);};
const clear=function(a is Query,b is Query,msg is string) {
 if(size(evaluateQuery(context,a))==0 || size(evaluateQuery(context,b))==0) return;
 for(var hit in evCollision(context,{"tools":a,"targets":b}))
  check(hit["type"]!=ClashType.INTERFERE && hit["type"]!=ClashType.TARGET_IN_TOOL && hit["type"]!=ClashType.TOOL_IN_TARGET && hit["type"]!=ClashType.ABUT_TOOL_IN_TARGET,msg);
};
var results=[];
for(var c=0;c<7;c+=1) {
 var d=DEFAULTS;d.daytime=c<2 || c==4 || c==6;d.openStorageLid=c%2==1 || c==4 || c==6;
 d.showCushions=c==6;d.cabinetHeight=400*millimeter;
 if(c==4) d.showSlats=false;
 if(c==5) {d.platformHeight=430*millimeter;d.cargoLength=1880*millimeter;d.toiletDepth=400*millimeter;}
 const id=makeId("lidOpenCase" ~ c);nv200Interior(context,id,d);
 const p=crossSlatDimensions(d);const s=crossStorageDimensions(d,p);
 var parts=[{"q":qCreatedBy(id+"crossSlats"+"lid",EntityType.BODY),
  "lo":vector(s.lidStart,s.lidRear,s.top),"hi":vector(s.lidEnd,s.lidFront,s.top+d.crossDeckThickness)}];
 for(var i=0;i<p.count;i+=2)
  parts=append(parts,{"q":qCreatedBy(id+"crossSlats"+("lidSlat" ~ i),EntityType.BODY),
   "lo":vector(max(d.wallThickness,s.lidStart),max(p.slats[i].y,s.lidRear),d.platformHeight-d.slatThickness),
   "hi":vector(s.lidEnd,min(p.slats[i].y+p.slats[i].width,s.lidFront),d.platformHeight)});
 var moving=[];
 for(var part in parts) {
  check(size(evaluateQuery(context,part.q))==(d.showSlats?1:0),"Lid and attached slat visibility");
  moving=append(moving,part.q);
  if(d.showSlats) {
   const angle=d.openStorageLid?70*degree:0*degree;
   const a=part.lo;const b=part.hi;const y=s.lidFront;const z=d.platformHeight;
   const expectedLo=vector(a[0],y+(a[1]-y)*cos(angle)+(a[2]-z)*sin(angle),z-(b[1]-y)*sin(angle)+(a[2]-z)*cos(angle));
   const expectedHi=vector(b[0],y+(b[1]-y)*cos(angle)+(b[2]-z)*sin(angle),z-(a[1]-y)*sin(angle)+(b[2]-z)*cos(angle));
   const actual=evBox3d(context,{"topology":part.q,"tight":true});
   check(norm(actual.minCorner-expectedLo)<0.001*millimeter && norm(actual.maxCorner-expectedHi)<0.001*millimeter,"Actual bodies rotate70deg upward around cab-side top edge");
  }
 }
 const lidAssembly=qUnion(moving);
 const foam=qUnion([qCreatedBy(id+"cushionA",EntityType.BODY),qCreatedBy(id+"cushionB",EntityType.BODY),qCreatedBy(id+"cushionC1",EntityType.BODY),qCreatedBy(id+"cushionRear",EntityType.BODY),qCreatedBy(id+"cushionC2",EntityType.BODY),qCreatedBy(id+"cushionD",EntityType.BODY)]);
 const fixed=qSubtraction(qCreatedBy(id,EntityType.BODY),qUnion([lidAssembly,foam]));
 clear(lidAssembly,fixed,"Open/closed lid clears furniture and mechanism with cushions removed");
 check(size(evaluateQuery(context,foam))==(d.showCushions?6:0),"Cushion control remains independent");
 check(size(evaluateQuery(context,qCreatedBy(id+"crossSlats"+"deck",EntityType.BODY)))==(d.showSlats?1:0),"Fixed toilet deck visibility retained");
 if(d.showSlats) {
  for(var i=1;i<size(parts);i+=1)
   check(evDistance(context,{"side0":parts[0].q,"side1":parts[i].q}).distance<0.001*millimeter,"Lid slats stay attached while rotating");
  // Sample the intermediate opening path in10deg steps; no hinge hardware or foam fit is claimed.
  if(c==1 || c==3) {
   const axis=line(vector(0*millimeter,s.lidFront,d.platformHeight),vector(1,0,0));
   for(var k=1;k<=7;k+=1) {
    opTransform(context,makeId("lidMotion" ~ c ~ "step" ~ k),{"bodies":lidAssembly,"transform":rotationAround(axis,10*degree)});
    clear(lidAssembly,fixed,"Lid sampled opening motion clears furniture and slats");
   }
  }
 }
 results=append(results,"PASS lid open control case " ~ c);
 opDeleteBodies(context,makeId("lidOpenCleanup" ~ c),{"entities":qCreatedBy(id,EntityType.BODY)});
}
return results;
}`;
fs.writeFileSync('nv200-lid-open-validation.fs','function(context,queries) {\n'+adapted+'\n'+checks);
console.log('Generated lid-open checks.');
