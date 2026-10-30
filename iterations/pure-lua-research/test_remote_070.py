from pathlib import Path
import sys
sys.path.insert(0,str(Path('work/lua-test-deps').resolve()))
from lupa import LuaRuntime
root=Path('work/vehicle-release-0.7.0/42/media/lua')
fixture=Path('work/pure-lua-research/test_vehicle_steps.py').read_text().split("fixture=r'''",1)[1].split("'''",1)[0]
extra=r'''
print=function()end
callbacks={}
Events=setmetatable({}, {__index=function(t,k)local a={};callbacks[k]=a;local v={Add=function(f)table.insert(a,f)end};rawset(t,k,v);return v end})
function triggerEvent()end
function getNumActivePlayers()return 1 end
function getSpecificPlayer(slot)if slot==0 then return controlled or p end end
function p:getPlayerNum()return 0 end
function p:isGodMod()return self.god==true end
function p:setGodMod(v)self.god=v end
function p:isGhostMode()return self.ghost==true end
function p:setGhostMode(v)self.ghost=v end
function v:getCharacter(seat)if seat==0 then return p.vehicle==self and p or nil end end
local baseChunk=chunk
function chunk(x,y)local c=baseChunk(x,y);c.refs=c.refs or {};return c end
maps={};pinsReleased={}
local function countRefs(c)local n=0;for _ in pairs(c.refs)do n=n+1 end;return n end
function makeMap(id)
 local map={id=id,grid={},cx=12,cy=12}
 function map:getWidthInTiles()return 104 end
 function map:getChunk(x,y)return self.grid[x..','..y]end
 function map:copy(other)
  self.cx=other.cx;self.cy=other.cy
  for key,c in pairs(other.grid)do self.grid[key]=c;c.refs[self.id]=true end
 end
 function map:Unload()
  for _,c in pairs(self.grid)do c.refs[self.id]=nil end
  self.grid={};pinsReleased[self.id]=(pinsReleased[self.id] or 0)+1
  if v.chunk and countRefs(v.chunk)==0 then v.removed=true end
 end
 function map:populate(cx,cy)
  self.cx=cx;self.cy=cy
  for ix=0,12 do for iy=0,12 do
   local c=chunk((cx-6+ix)*8,(cy-6+iy)*8)
   self.grid[ix..','..iy]=c;c.refs[self.id]=true
  end end
 end
 function map:ProcessChunkPos(actor)
  local cx,cy=math.floor(actor.x/8),math.floor(actor.y/8)
  if cx==self.cx and cy==self.cy and not self.pending then return end
  self:Unload();self.cx=cx;self.cy=cy
  local source=chunk(cx*8,cy*8)
  if countRefs(source)>0 then self:populate(cx,cy);self.pending=nil
  else self.pending={cx,cy};self.due=clock+320 end
 end
 return map
end
for id=0,3 do maps[id]=makeMap(id)end
maps[0]:populate(12,12);v.chunk=chunk(v.x,v.y)
function cell:getChunkMap(id)return maps[id]end
function cell:getGridSquare(x,y,z)
 local m=maps[0]
 if m.pending or x<(m.cx-6)*8 or x>=(m.cx+7)*8 or y<(m.cy-6)*8 or y>=(m.cy+7)*8 then return nil end
 if blockedDestination and x>1000 then return nil end
 return square(x,y)
end
v.native=vec(v.origin:x(),v.origin:y(),v.origin:z())
function v:setWorldTransform(t)
 mutations=mutations+1
 self.origin:set(t.o:x(),t.o:y(),t.o:z())
 if self.active then self.native:set(t.o:x(),t.o:y(),t.o:z())end
 if self.injectFailure then self.injectFailure=false;error('injected partial vehicle write')end
end
function v:checkSurroundingChunks()
 self.disabled=not cell:getGridSquare(self.origin:x()+10000,self.origin:z()+20000,0)
 if self.disabled then self.active=false end
end
function v:setPhysicsActive(active)self.active=active and not self.disabled end
function v:update()
 self.x=self.origin:x()+10000;self.y=self.origin:z()+20000
 if self.current and cell:getGridSquare(self.x,self.y,0)then self.square=self.current;self.chunk=self.current:getChunk()end
end
function v:exit(actor)
 saved=saved+1;savedChunk=self.chunk.key;savedX=self.x;savedY=self.y
 if not actor then return false end
 if actor.vehicle~=self then return false end
 actor.vehicle=nil;return true
end
function frame()
 clock=clock+16
 local m=maps[0]
 if m.pending and clock>=m.due then local pending=m.pending;m.pending=nil;m:populate(pending[1],pending[2])end
 v:checkSurroundingChunks()
 v.origin:set(v.native:x(),v.native:y(),v.native:z());v:update()
 if v.chunk and countRefs(v.chunk)==0 then v.removed=true end
 for _,f in ipairs(callbacks.OnTick or {})do f()end
 P.tick()
end
'''
def runtime():
 l=LuaRuntime();l.execute(fixture);l.execute(extra)
 l.globals().P=l.execute((root/'shared/UMV_Vehicle.lua').read_text(encoding='utf-8-sig'))
 l.execute('require=function()return P end;P.onStarted=function()ui=true end;P.onStopped=function()ui=false end')
 l.globals().R=l.execute((root/'client/UMV_RemoteSP.lua').read_text(encoding='utf-8-sig'))
 return l
l=runtime();l.execute('''assert(P.start(p,6100,4100));assert(P.session.remote and maps[3]:getChunk(0,0));assert(not v.removed and p.vehicle==nil)
for i=1,500 do frame();if not P.session then break end end
assert(P.session==nil and P.progress==1,P.status)
assert(math.abs(v.x-6100)<25 and math.abs(v.y-4100)<25)
assert(not v.removed and v.id==252 and v.sql==1007)
assert(savedChunk==v.chunk.key and math.abs(savedX-v.x)<1)
assert(not p.block and not p.god and not p.ghost and not ui)
assert(next(maps[2].grid)==nil and next(maps[3].grid)==nil)
assert(mutations<8,'used intermediate short hops')
''');print('PASS 7,200-tile trip: one long move, pinned origin survives active-map unload, loaded destination/native readback, correct SQL chunk, both pins and character flags restored')
l=runtime();l.execute('''assert(P.start(p,6100,4100));P.stop('cancel');for i=1,200 do frame();if not P.session then break end end
assert(not P.session and math.abs(v.x-100.5)<1 and not v.removed,P.status)
assert(not p.block and not p.god and not p.ghost and next(maps[3].grid)==nil)
''');print('PASS cancellation while destination loads: return to pinned origin and release all locks/references')
l=runtime();l.execute('''assert(P.start(p,6100,4100));v.injectFailure=true;for i=1,500 do frame();if not P.session then break end end
assert(not P.session and math.abs(v.x-100.5)<1 and not v.removed,P.status)
assert(savedChunk==v.chunk.key and not p.block and not p.god)
''');print('PASS partial physical write: original vehicle restored and saved in its source chunk')
l=runtime();l.execute('''blockedDestination=true;assert(P.start(p,6100,4100));for i=1,2200 do frame();if not P.session then break end end
assert(not P.session and math.abs(v.x-100.5)<1 and not v.removed,P.status)
assert(not p.block and next(maps[2].grid)==nil and next(maps[3].grid)==nil)
''');print('PASS unavailable destination: timeout returns to the source; no vehicle loss')
l=runtime();l.execute('''p.god=true;p.ghost=true;assert(P.start(p,6100,4100));for i=1,500 do frame();if not P.session then break end end
assert(p.god and p.ghost and p.data.UMVRemoteProtection==nil)
''');print('PASS original character protection settings are preserved')
l=runtime();l.execute('''maps[3].grid['0,0']=chunk(0,0);assert(P.start(p,6100,4100));assert(not P.session.remote);P.stop('fallback')
assert(not p.block and p.vehicle==nil)
''');print('PASS occupied spare slot: no fast-load changes, existing vehicle flow retained')

# Combine the real animal module with the fast path and a second seated actor.
animal_test=Path('work/pure-lua-research/test_015.py').read_text(encoding='utf-8-sig')
animal_fixture=animal_test.split("l.execute("+chr(39)*3+"\nfunction list()",1)[1].split(chr(39)*3+")",1)[0]
l=runtime();l.execute("function list()"+animal_fixture)
l.globals().P.animals=l.execute((root/'shared/UMV_Animals.lua').read_text(encoding='utf-8-sig'))
l.execute("""
npc=setmetatable({x=p.x,y=p.y,z=0,vehicle=v,block=true,god=false,ghost=false,data={},attached=list()},{__index=p})
function v:getCharacter(seat)if seat==0 then return p.vehicle==self and p or nil end;return npc.vehicle==self and npc or nil end
assert(P.start(p,6100,4100));assert(P.session.remote)
for i=1,500 do frame();if not P.session then break end end
assert(not P.session and P.progress==1,P.status)
assert(p.attached:size()==1 and p.attached:get(0).owner==p and #inventory.items==0)
assert(npc.vehicle==nil and not p.block and npc.block and not npc.god and not npc.ghost)
assert(math.abs(p.x-npc.x)+math.abs(p.y-npc.y)>0)
assert(math.abs(p.x-v.x)<12 and math.abs(npc.x-v.x)<12)
""");print('PASS fast path with two occupants and real animal module: rope restored, separate exits beside vehicle, each actor state restored')
