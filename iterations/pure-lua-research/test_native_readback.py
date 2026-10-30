import sys
from pathlib import Path
sys.path.insert(0,str(Path('work/lua-test-deps').resolve()))
from lupa import LuaRuntime
# Reuse the world fixture without executing its test cases.
t=Path('work/pure-lua-research/test_vehicle_steps.py').read_text(encoding='utf-8-sig')
fixture=t.split("fixture=r'''",1)[1].split("'''\ndef runtime",1)[0]
native=r'''
v.native=vec(v.origin:x(),v.origin:y(),v.origin:z())
local oldTransform=v.setWorldTransform
function v:setWorldTransform(t)
 local injected=self.injectFailure
 self.injectFailure=false
 oldTransform(self,t)
 if self.active then self.native:set(t.o:x(),t.o:y(),t.o:z()) end
 if injected then error('injected failure AFTER native write')end
end
function v:isPhysicsActive()return self.active end
function frame()
 clock=clock+16;loadTick=loadTick+1
 if loadTick%5==0 then loadedX=p.x;loadedY=p.y end
 -- Independent native simulation readback. Java mirror writes alone do not count.
 v.origin:set(v.native:x(),v.native:y(),v.native:z());v:update()
 P.tick()
end
'''
old=Path('work/pure-lua-012-backup/PLVT_Core.lua').read_text(encoding='utf-8-sig')
new=Path('work/pure-lua-vehicle-test/42/media/lua/client/PLVT_Core.lua').read_text(encoding='utf-8-sig')
def run(src):
 l=LuaRuntime();l.execute(fixture);l.execute(native);l.globals().P=l.execute(src);return l
l=run(old);l.execute('assert(P.start(p,112,106));for i=1,25 do frame()end;assert(not P.session and P.progress<1);assert(math.abs(v.x-100.5)<0.1)');print('REPRODUCED: 0.1.1 freezes the body, then independent physics readback returns it to origin')
l=run(new);l.execute('assert(P.start(p,112,106));for i=1,25 do frame()end;assert(not P.session and P.progress==1);assert(math.abs(v.native:x()+10000-v.x)<0.01)');print('PASS: 0.1.2 nearby move survives independent native readback')
l=run(new);l.execute('assert(P.start(p,3100,2100));for i=1,20000 do frame();if not P.session then break end end;assert(not P.session and P.progress==1,P.status);assert(v.id==252 and v.sql==1007 and not p.block and unsafe==0)');print('PASS: distant journey with separate native and entity transforms')
l=run(new);l.execute('assert(P.start(p,2000,100));v.injectFailure=true;frame();assert(not P.session and not p.block);assert(math.abs(v.native:x()+10000-100.5)<0.01)');print('PASS: failure after native write restores the previous physical checkpoint')
# Exercise the actual progress-panel callback with a strict DrawText signature.
l=LuaRuntime();l.execute('''
require=function()return P end
P={status='test',progress=0.5}
Events=setmetatable({}, {__index=function()return {Add=function()end}end})
ISWorldMap={HideWorldMap=function()end};UIFont={Small={}}
function getCore()return {getScreenWidth=function()return 1920 end}end
ISPanel={prerender=function()end,new=function()
 panel={initialise=function()end,addToUIManager=function()end,removeFromUIManager=function()end,addChild=function()end,
 drawText=function(self,str,x,y,r,g,b,a,font)assert(type(a)=='number','missing numeric alpha');assert(font==UIFont.Small)end,
 drawRect=function()end}
 return panel
end}
ISButton={new=function()return {initialise=function()end}end}
''');l.execute(Path('work/pure-lua-vehicle-test/42/media/lua/client/PLVT_Main.lua').read_text(encoding='utf-8-sig'));l.execute('P.onStarted({getPlayerNum=function()return 0 end});panel:prerender();P.onStopped()');print('PASS: progress-panel DrawText arguments and cleanup')
