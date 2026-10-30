import sys
from pathlib import Path
sys.path.insert(0,str(Path('work/lua-test-deps').resolve()))
from lupa import LuaRuntime
from luaparser import ast
src=Path('work/pure-lua-vehicle-test/42/media/lua/client/PLVT_Core.lua').read_text(encoding='utf-8-sig')
ast.parse(src)
fixture=r'''
unpack=unpack or table.unpack
require=function() end
clock=0; saved=0; mutations=0; unsafe=0; rollbacks=0
function getTimestampMs() return clock end
function getSpecificPlayer() return p end
function triggerEvent() end
function isClient() return false end
function isServer() return false end
IsoFlagType={water='water'}
function vec(x,y,z)
 return {a=x or 0,b=y or 0,c=z or 0,x=function(s)return s.a end,y=function(s)return s.b end,z=function(s)return s.c end,set=function(s,x,y,z)s.a=x;s.b=y;s.c=z;return s end}
end
Vector3f={new=function()return vec()end}
Transform={new=function()local t={o=vec()}; t.getOrigin=function(s)return s.o end; return t end}
chunks={}
function chunk(x,y)
 local key=math.floor(x/8)..','..math.floor(y/8)
 if not chunks[key] then chunks[key]={key=key} end
 return chunks[key]
end
p={x=100.5,y=100.5,z=0,block=false,data={},dead=false}
function p:getX()return self.x end
function p:getY()return self.y end
function p:getZ()return self.z end
function p:setX(x)self.x=x end
function p:setY(y)self.y=y end
function p:setZ(z)self.z=z end
function p:setLastX(x)end
function p:setLastY(y)end
function p:setCurrent(s)self.square=s end
function p:teleportTo(x,y,z)self.x=x;self.y=y;self.z=z end
function p:setVehicle(v)self.vehicle=v end
function p:setCollidable(v)end
function p:getVehicle()return self.vehicle end
function p:isDead()return self.dead end
function p:isBlockMovement()return self.block end
function p:setBlockMovement(b)self.block=b end
function p:getModData()return self.data end
function p:Say(s)self.message=s end
function square(x,y)
 return {getChunk=function()return chunk(x,y)end,getVehicleContainer=function()return nil end,getFloor=function()return {getSprite=function()return {getProperties=function()return {has=function()return false end}end}end}end,isFree=function()return true end}
end
v={x=p.x,y=p.y,z=0,id=252,sql=1007,origin=vec(p.x-10000,0.3,p.y-20000),removed=false,seat=true,active=true}
p.vehicle=v
v.square=square(v.x,v.y);v.current=v.square
function v:getX()return self.x end
function v:getY()return self.y end
function v:getZ()return self.z end
function v:setX(x)self.x=x end
function v:setY(y)self.y=y end
function v:setZ(z)self.z=z end
function v:getController()if not self.removed then return {} end end
function v:getId()return self.id end
function v:getSqlId()return self.sql end
function v:isRemovedFromWorld()return self.removed end
function v:getScript()return {getExtents=function()return vec(1.8,1.5,4.2)end}end
function v:getVehicleTowing()return self.towing end
function v:getVehicleTowedBy()return nil end
function v:getMaxPassengers()return 2 end
function v:getCharacter(index)if index==0 and self.seat then return p end;return self.extra end
function v:getSeat()return 0 end
function v:getCurrentAbsoluteSpeedKmHour()return 0 end
function v:getWorldPos(a,b,c,out)return out:set(self.origin:x()+10000+a,self.origin:z()+20000+c,b)end
function v:getWorldTransform(out)out.o:set(self.origin:x(),self.origin:y(),self.origin:z());return out end
function v:setWorldTransform(t)
 mutations=mutations+1
 if not cell:getGridSquare(t.o:x()+10000,t.o:z()+20000,0) then unsafe=unsafe+1;error('unloaded physical destination')end
 self.origin:set(t.o:x(),t.o:y(),t.o:z())
 if self.injectFailure then self.injectFailure=false;error('injected failure AFTER physics write')end
end
function v:setCurrent(s)self.current=s end
function v:getSquare()return self.square end
function v:update()
 self.x=self.origin:x()+10000;self.y=self.origin:z()+20000;self.square=self.current
 assert(cell:getGridSquare(self.x,self.y,0),'native update lost loaded area')
end
function v:getPassengerWorldPos(seat,out)return out:set(self.x,self.y,0)end
function v:setPhysicsActive(active,static)self.active=active end
function v:checkSurroundingChunks()end
function v:shutOff()end
function v:exit(player)saved=saved+1;player.vehicle=nil;self.seat=false;return true end
function v:enter(index,player)player.vehicle=self;self.seat=true;return true end
function v:setCharacterPosition()end
function v:teleportTo()error('must never call teleportTo')end
function v:addToWorld()error('must not re-add vehicle')end
function v:removeFromWorld()error('must not unload vehicle')end
function v:createPhysics()error('must not recreate physics')end
function getVehicleById(id)if id==v.id and not v.removed then return v end end
loadedX=p.x;loadedY=p.y;loadTick=0
cell={}
function cell:getGridSquare(x,y,z)
 if math.abs(x-loadedX)>48 or math.abs(y-loadedY)>48 then return nil end
 if blocked and x>130 then return nil end
 return square(x,y)
end
function cell:getVehicles()return {contains=function(_,obj)return obj==v end,iterator=function()local first=true;return {hasNext=function()return first end,next=function()first=false;return v end}end}end
function getCell()return cell end
function frame()
 clock=clock+16
 loadTick=loadTick+1
 if loadTick%5==0 then loadedX=p.x;loadedY=p.y end
 P.tick()
end
'''
def runtime():
 l=LuaRuntime();l.execute(fixture);l.globals().P=l.execute(src);return l
l=runtime();l.execute('''
assert(P.start(p,3100,2100))
for i=1,20000 do frame();if not P.session then break end end
assert(not P.session and P.progress==1,P.status)
assert(math.abs(v.x-3100)<14 and math.abs(v.y-2100)<14,P.status)
assert(v.id==252 and v.sql==1007 and p.vehicle==nil)
assert(not p.block and v.active and saved==1 and unsafe==0)
assert(mutations>100,'did not exercise distant travel')
''');print('PASS: 3,600-tile journey through a moving loaded window; >100 steps; same runtime/SQL IDs; native save checkpoint; controls restored')
l=runtime();l.execute('''
assert(P.start(p,2000,100));v.injectFailure=true;frame()
assert(not P.session and not p.block and v.active)
assert(math.abs(v.x-100.5)<0.01 and math.abs(v.origin:x()+10000-100.5)<0.01,'rollback failed')
assert(p.vehicle==nil and unsafe==0)
''');print('PASS: failure after physical write rolls back the short step without detaching the player')
l=runtime();l.execute('assert(P.start(p,2000,100));for i=1,20 do frame()end;P.stop("cancel");assert(not P.session and not p.block and v.active and p.vehicle==nil)');print('PASS: cancellation saves vehicle, exits to nearby ground and restores controls')
l=runtime();l.execute('blocked=true;assert(P.start(p,2000,100));for i=1,3000 do frame();if not P.session then break end end;assert(not P.session and not p.block and unsafe==0)');print('PASS: no loaded route times out at a retained checkpoint')
l=runtime();l.execute('v.extra={};assert(not P.start(p,2000,100));assert(mutations==0);v.extra=nil;v.towing={};assert(not P.start(p,2000,100));assert(mutations==0)');print('PASS: unsupported passenger/trailer test cases reject before moving anything')
l=runtime();l.execute('umtspMoveVehicle=function()end;assert(not P.start(p,2000,100));assert(mutations==0)');print('PASS: detects active Java bridge; no false dependency-free test')
