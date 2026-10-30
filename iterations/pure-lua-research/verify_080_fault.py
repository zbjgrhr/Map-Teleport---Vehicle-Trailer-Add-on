from pathlib import Path
p=Path('work/vehicle-candidate-0.8.0/42/media/lua/server/UMV_NetworkServer.lua');s=p.read_text();s=s.replace('local capable=#s.occupants>=2 and s.total>128','local capable=#s.occupants>=2 and s.total>128 and H.clear(s,s.startX,s.startY)~=nil');p.write_text(s,encoding='utf-8')
p=Path('work/pure-lua-research/test_remote_network_080.py');s=p.read_text(encoding='utf-8-sig');s+='''
s=Simulation();s.realms[0].execute('v.injectFailure=true');s.realms[1].execute('assert(P.start(p,6100,4100))');s.pump();s.frames(500)
s.check(0,'assert(S.getSession()==nil and math.abs(v.x-100.5)<1 and not v.removed);assert(not p.block and not npc.block)')
for who in [1,2]:s.check(who,'assert(N.session==nil and next(maps[3].grid)==nil and not p.block and not npc.block)')
assert s.commits==0
print('PASS partial server write: short rollback while both server areas remain loaded, scouts return, no remote vehicle commit')
''';p.write_text(s,encoding='utf-8')
