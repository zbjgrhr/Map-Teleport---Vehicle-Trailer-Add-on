from pathlib import Path
import sys
sys.path.insert(0,str(Path('work/lua-test-deps').resolve()))
from lupa import LuaRuntime
base=Path('work/vehicle-release-0.6.1/42/media/lua')
fixture=Path('work/pure-lua-research/test_vehicle_steps.py').read_text().split("fixture=r'''",1)[1].split("'''",1)[0]
class Simulation:
 def __init__(self,missing=False):
  self.queue=[];self.realms={};self.missing=missing
  for who in [0,1,2]:
   l=LuaRuntime();self.realms[who]=l;l.execute(fixture)
   l.execute('''
print=function()end
callbacks={}
Events=setmetatable({}, {__index=function(t,k)local a={};callbacks[k]=a;local v={Add=function(f)table.insert(a,f)end};rawset(t,k,v);return v end})
function triggerEvent()end
function getWorld()return {getMetaGrid=function()return {isValidChunk=function()return true end}end}end
p.onlineID=1
function p:getOnlineID()return self.onlineID end
npc=setmetatable({onlineID=2,x=p.x,y=p.y,z=0,block=false,data={},vehicle=v},{__index=p})
function v:getDriver()if p.vehicle==self then return p end end
function v:getCharacter(seat)if seat==0 then return p.vehicle==self and p or nil else return npc.vehicle==self and npc or nil end end
function v:getSeat(actor)if actor==p and p.vehicle==self then return 0 elseif actor==npc and npc.vehicle==self then return 1 end return -1 end
function v:exit(actor)saved=saved+1;if not actor then return false end;local seat=self:getSeat(actor);if seat<0 then return false end;actor.vehicle=nil;return true end
function v:exitRSync(actor)local seat=self:getSeat(actor);if seat<0 then return false end;actor.vehicle=nil;return true end
v.netID=1
function v:getNetPlayerId()return self.netID end
function v:authorizationServerOnSeat(actor,enter)if not enter and actor:getOnlineID()==self.netID then self.netID=-1 end end
Animals={capture=function()return {} end,stage=function()return true end,release=function()return true end}
''')
   l.globals().realm=who
   l.execute('function isServer()return realm==0 end;function isClient()return realm~=0 end;function getSpecificPlayer()if realm==2 then return npc else return p end end')
   l.globals().P=l.execute((base/'shared/UMV_Vehicle.lua').read_text(encoding='utf-8-sig'))
   l.execute('P.onStarted=function()ui=true end;P.onStopped=function()ui=false end;P.markVehicle=function(x,y)markerX=x;markerY=y end;require=function(name)if name=="UMV_Vehicle" then return P else return Animals end end')
   if who==0:
    def send(*a):
     if len(a)==4:
      actor,mod,cmd,args=a;target=int(actor.getOnlineID(actor));self.queue.append((target,mod,cmd,dict(args.items())))
     else:
      mod,cmd,args=a
      for target in [1,2]:self.queue.append((target,mod,cmd,dict(args.items())))
    l.globals().sendServerCommand=send
    l.globals().S=l.execute((base/'server/UMV_NetworkServer.lua').read_text(encoding='utf-8-sig'))
   else:
    def send(actor,mod,cmd,args,who=who):self.queue.append((0,mod,cmd,dict(args.items()),who))
    l.globals().sendClientCommand=send
    l.globals().N=l.execute((base/'client/UMV_NetworkClient.lua').read_text(encoding='utf-8-sig'))
 def pump(self):
  for _ in range(1000):
   if not self.queue:return
   event=self.queue.pop(0);who,mod,cmd,args,*sender=event;l=self.realms[who]
   if self.missing and who==2:continue
   table=l.table_from(args)
   if who==0:
    actor=l.globals().p if sender[0]==1 else l.globals().npc
    l.globals().S.command(mod,cmd,actor,table)
   else:
    l.globals()._mod=mod;l.globals()._cmd=cmd;l.globals()._args=table
    l.execute('for _,f in ipairs(callbacks.OnServerCommand)do f(_mod,_cmd,_args)end')
  raise AssertionError('message loop')
 def frames(self,count):
  for _ in range(count):
   for who,l in self.realms.items():
    l.execute('clock=clock+16;loadTick=loadTick+1;if loadTick%5==0 then local a=getSpecificPlayer(0);loadedX=a.x;loadedY=a.y end;for _,f in ipairs(callbacks.OnTick or {})do f()end')
   self.pump()
 def start(self):self.realms[1].execute('assert(P.start(p,800,100))');self.pump()
 def check(self,who,code):self.realms[who].execute(code)
s=Simulation();s.start();s.frames(2400)
s.check(0,'assert(S.getSession()==nil);assert(math.abs(v.x-800)<14);assert(p.vehicle==nil and npc.vehicle==nil and not p.block and not npc.block);assert(saved>=3 and unsafe==0)')
for who in [1,2]:s.check(who,'assert(N.session==nil and P.session==nil and P.progress==1);assert(not p.block and not npc.block);assert(markerX and math.abs(markerX-v.x)<1);assert(not ui)')
print('PASS separate server + two client runtimes: multi-step vehicle transfer, both passengers, authority revoke, loaded-area probes, arrival ACKs, markers and locks')
s=Simulation(missing=True);s.start();s.frames(1400)
s.check(0,'assert(S.getSession()==nil and mutations==0 and saved==0);assert(p.vehicle==v and npc.vehicle==v and not p.block and not npc.block)')
s.check(1,'assert(N.session==nil and not p.block)')
print('PASS missing passenger client: timeout before movement; both original seats retained')
s=Simulation();s.start();s.frames(35);s.realms[2].execute('N.cancel()');s.pump();s.frames(20)
s.check(0,'assert(S.getSession()==nil and not p.block and not npc.block);assert(v.x<800 and p.vehicle==nil and npc.vehicle==nil)')
for who in [1,2]:s.check(who,'assert(N.session==nil and not p.block and not npc.block)')
print('PASS passenger cancellation: ends the whole group at the current checkpoint')
s=Simulation();s.realms[2].execute('assert(not P.start(npc,800,100));assert(N.session==nil)')
print('PASS passenger cannot initiate a transfer without the driver')
