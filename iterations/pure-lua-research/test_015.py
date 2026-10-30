from pathlib import Path
import sys
sys.path.insert(0,str(Path('work/lua-test-deps').resolve()))
from lupa import LuaRuntime
fixture=Path('work/pure-lua-research/test_vehicle_steps.py').read_text().split("fixture=r'''",1)[1].split("'''",1)[0]
root=Path('work/pure-lua-vehicle-test/42/media/lua')
src=(root/'client/PLVT_Core.lua').read_text()
def runtime(source=src):
 l=LuaRuntime();l.execute(fixture);l.execute('print=function()end');l.globals().P=l.execute(source);return l
# Compare identical loading-window and terrain assumptions.
old=Path('outputs/PureLuaVehicleTest-0.1.4/UMTSPPureLuaVehicleTest/42/media/lua/client/PLVT_Core.lua').read_text()
for version,source in [('0.1.4',old),('0.1.5',src)]:
 l=runtime(source);l.execute('P.onStopped=function(ok,s)hops=s.hops end;assert(P.start(p,3100,2100));for i=1,20000 do frame();if not P.session then frames=i;break end end;assert(P.progress==1,P.status);assert(unsafe==0)')
 print(version,'hops',l.globals().hops,'frames',l.globals().frames)
l=runtime()
l.execute('''
function list()return {values={},size=function(s)return #s.values end,get=function(s,i)return s.values[i+1]end,remove=function(s,v)for i,a in ipairs(s.values)do if a==v then table.remove(s.values,i);break end end end,contains=function(s,v)for _,a in ipairs(s.values)do if a==v then return true end end return false end,add=function(s,v)table.insert(s.values,v)end}end
p.attached=list();inventory={items={}}
function inventory:AddItem(item)table.insert(self.items,item);return item end
function inventory:Remove(item)for i,v in ipairs(self.items)do if v==item then table.remove(self.items,i);return end end end
function p:getInventory()return inventory end
function p:getAttachedAnimals()return self.attached end
function animal()
 local a={world=true,owner=p}
 function a:isExistInTheWorld()return self.world end
 function a:isDead()return false end
 function a:getData()return {getAttachedPlayer=function()return a.owner end,setAttachedPlayer=function(_,v)a.owner=v end}end
 function a:getOnlineID()return 5 end
 function a:getAnimalType()return 'cow' end
 function a:setWild()end
 function a:removeFromWorld()self.world=false end
 function a:removeFromSquare()end
 function a:setSquare()end
 return a
end
originalAnimal=animal();p.attached:add(originalAnimal)
function instanceItem()return {setAnimal=function(s,a)s.animal=a end}end
local prior=square
function square(x,y)
 local sq=prior(x,y);sq.animals=list()
 function sq:getAnimals()return self.animals end
 function sq:AddWorldInventoryItem(item)local a=animal();a.owner=nil;self.animals:add(a);return {} end
 return sq
end
''')
l.globals().P.animals=l.execute((root/'shared/UMTSP_Animals.lua').read_text())
l.execute('''assert(P.start(p,600,100));assert(p.attached:size()==0 and #inventory.items==1 and not originalAnimal.world)
for i=1,3000 do frame();if not P.session then break end end
assert(P.progress==1 and p.attached:size()==1 and #inventory.items==0,P.status)
assert(p.attached:get(0)~=originalAnimal and p.attached:get(0).owner==p)
-- Cancel a subsequent trip: the animal must also be restored at that checkpoint.
p.vehicle=v;v.seat=true
assert(P.start(p,900,100));frame();P.stop('cancel')
assert(p.attached:size()==1 and #inventory.items==0 and not p.block)
''')
print('PASS actual Animals module plus actual vehicle core: stage, native drop replacement, rope restoration on success and cancellation')
