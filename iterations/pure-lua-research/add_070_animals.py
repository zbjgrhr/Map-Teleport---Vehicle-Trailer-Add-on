from pathlib import Path
p=Path('work/pure-lua-research/test_remote_070.py');s=p.read_text(encoding='utf-8-sig')
s+='''
# Combine the real animal module with the fast path and a second seated actor.
animal_test=Path('work/pure-lua-research/test_015.py').read_text(encoding='utf-8-sig')
animal_fixture=animal_test.split("l.execute(\"\"\"",1)[-1] if False else animal_test.split("l.execute("+chr(39)*3+"\\nfunction list()",1)[1].split(chr(39)*3+")",1)[0]
l=runtime();l.execute("function list()"+animal_fixture)
l.globals().P.animals=l.execute((root/'shared/UMV_Animals.lua').read_text(encoding='utf-8-sig'))
l.execute(\"\"\"
npc=setmetatable({x=p.x,y=p.y,z=0,vehicle=v,block=true,god=false,ghost=false,data={},attached=list()},{__index=p})
function v:getCharacter(seat)if seat==0 then return p.vehicle==self and p or nil end;return npc.vehicle==self and npc or nil end
assert(P.start(p,6100,4100));assert(P.session.remote)
for i=1,500 do frame();if not P.session then break end end
assert(not P.session and P.progress==1,P.status)
assert(p.attached:size()==1 and p.attached:get(0).owner==p and #inventory.items==0)
assert(npc.vehicle==nil and not p.block and npc.block and not npc.god and not npc.ghost)
assert(math.abs(p.x-npc.x)+math.abs(p.y-npc.y)>0)
assert(math.abs(p.x-v.x)<12 and math.abs(npc.x-v.x)<12)
\"\"\");print('PASS fast path with two occupants and real animal module: rope restored, separate exits beside vehicle, each actor state restored')
'''
p.write_text(s,encoding='utf-8')
