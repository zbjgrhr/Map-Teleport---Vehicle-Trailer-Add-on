from pathlib import Path
import sys
sys.path.insert(0,str(Path('work/lua-test-deps').resolve()))
from lupa import LuaRuntime
original=Path('work/pure-lua-research/test_network_061.py').read_text(encoding='utf-8-sig')
cut=original.split('s=Simulation();s.start();s.frames(2400)',1)[0].replace('work/vehicle-release-0.6.1','work/vehicle-candidate-0.8.0')
world=Path('work/pure-lua-research/test_remote_070.py').read_text(encoding='utf-8-sig').split("extra=r'''",1)[1].split("'''\ndef runtime",1)[0]
def install_world(l,who):
 if who==0:
  l.execute('''
function cell:getGridSquare(x,y,z)
 if (math.abs(x-p.x)<=48 and math.abs(y-p.y)<=48) or (math.abs(x-npc.x)<=48 and math.abs(y-npc.y)<=48) then
  return square(x,y)
 end
 return nil
end
function worldTick()
 if not cell:getGridSquare(v.x,v.y,0)then v.removed=true end
end
''')
 else:
  l.execute(world)
  l.execute('''
function getSpecificPlayer(slot)if slot==0 then return realm==2 and npc or p end end
function v:getCharacter(seat)if seat==0 then return p.vehicle==self and p or nil end;return npc.vehicle==self and npc or nil end
function worldTick()
 local m=maps[0]
 if m.pending and clock>=m.due then local pending=m.pending;m.pending=nil;m:populate(pending[1],pending[2])end
 v:checkSurroundingChunks();v.origin:set(v.native:x(),v.native:y(),v.native:z());v:update()
 if v.chunk then local n=0;for _ in pairs(v.chunk.refs)do n=n+1 end;if n==0 then v.removed=true end end
end
''')
cut=cut.replace('l.globals().P=l.execute','install_world(l,who)\n   l.globals().P=l.execute',1)
cut=cut.replace('self.queue=[];self.realms={};self.missing=missing','self.queue=[];self.realms={};self.missing=missing;self.commits=0')
cut=cut.replace('mod,cmd,args=a\n      for target','mod,cmd,args=a\n      if cmd=="commit":self.commits+=1\n      for target')
cut=cut.replace('clock=clock+16;loadTick=loadTick+1','clock=clock+16;worldTick();loadTick=loadTick+1')
namespace={'install_world':install_world};exec(compile(cut,'anchor-worlds','exec'),namespace)
Simulation=namespace['Simulation']
s=Simulation();s.realms[1].execute('assert(P.start(p,6100,4100))');s.pump();s.frames(500)
s.check(0,'assert(S.getSession()==nil and math.abs(v.x-6100)<24 and math.abs(v.y-4100)<24);assert(not v.removed and unsafe==0 and not p.block and not npc.block)')
for who in [1,2]:
 s.check(who,'assert(N.session==nil and P.progress==1,P.status);assert(not v.removed and not p.block and not npc.block);assert(next(maps[3].grid)==nil and N.cleanup==nil)')
assert s.commits==1,s.commits
print('PASS 7,200 tiles with server + two independently loaded client worlds: ONE actual vehicle commit; source anchor, destination loading, native-state readback, arrival ACKs and pin release')
# Cancel while the first client is still loading; server car must never leave source.
s=Simulation();s.realms[1].execute('assert(P.start(p,6100,4100))');s.pump();s.frames(6);s.realms[1].execute('N.cancel()');s.pump();s.frames(500)
s.check(0,'assert(S.getSession()==nil and math.abs(v.x-100.5)<1 and not v.removed);assert(not p.block and not npc.block)')
for who in [1,2]:s.check(who,'assert(N.session==nil and next(maps[3].grid)==nil and not p.block and not npc.block)')
assert s.commits==0
print('PASS cancellation during remote load: scouts return; server car never moves; original-area pins released')

s=Simulation();s.realms[0].execute('v.injectFailure=true');s.realms[1].execute('assert(P.start(p,6100,4100))');s.pump();s.frames(500)
s.check(0,'assert(S.getSession()==nil and math.abs(v.x-100.5)<1 and not v.removed);assert(not p.block and not npc.block)')
for who in [1,2]:s.check(who,'assert(N.session==nil and next(maps[3].grid)==nil and not p.block and not npc.block)')
assert s.commits==0
print('PASS partial server write: short rollback while both server areas remain loaded, scouts return, no remote vehicle commit')
