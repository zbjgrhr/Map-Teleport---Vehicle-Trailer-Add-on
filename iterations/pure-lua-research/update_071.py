from pathlib import Path
import shutil
root=Path('work/vehicle-release-0.7.1');assert not root.exists();shutil.copytree('work/vehicle-release-0.7.0',root)
for p in root.rglob('*'):
 if p.is_file() and p.suffix in ('.lua','.md','.info'):
  p.write_text(p.read_text(encoding='utf-8-sig').replace('0.7.0','0.7.1'),encoding='utf-8')
p=root/'42/media/lua/server/UMV_NetworkServer.lua';s=p.read_text()
s=s.replace('s.maxStep=24','s.maxStep=64',1)
s=s.replace('else s.phase="plan";s.maxStep=math.max(8,s.maxStep-8);s.retry=(s.retry or 0)+1;s.changed=now() end','''else
            local attempted=math.sqrt((s.stepX-s.vehicle:getX())^2+(s.stepY-s.vehicle:getY())^2)
            if attempted<=9 then finish("No shared loaded landing; stopped at the checkpoint",false);return end
            local smaller=8
            for _,length in ipairs({56,48,40,32,24,18,12,8}) do
                if length<attempted-1 and length<s.maxStep then smaller=length;break end
            end
            s.phase="plan";s.maxStep=smaller;s.retry=(s.retry or 0)+1;s.changed=now()
            log("Client landing not ready; reducing step cap to "..smaller)
        end''')
s=s.replace('        if not all(s,"arrived") then return end\n        if s.final','        if not all(s,"arrived") then return end\n        s.retry=0\n        if s.final',1)
s=s.replace('s.retry>=6','s.retry>=10')
p.write_text(s,encoding='utf-8')
# Reuse isolated server/client realms; count actual commits, not probe attempts.
test=Path('work/pure-lua-research/test_network_061.py').read_text(encoding='utf-8-sig')
cut=test.split('s=Simulation();s.start();s.frames(2400)',1)[0]
cut=cut.replace('self.queue=[];self.realms={};self.missing=missing','self.queue=[];self.realms={};self.missing=missing;self.commits=0')
cut=cut.replace('mod,cmd,args=a\n      for target','mod,cmd,args=a\n      if cmd=="commit":self.commits+=1\n      for target')
for version in ['0.7.0','0.7.1']:
 ns={};exec(compile(cut.replace('work/vehicle-release-0.6.1','work/vehicle-release-'+version),'network-'+version,'exec'),ns)
 sim=ns['Simulation']();sim.start()
 for frames in range(1,2401):
  sim.frames(1)
  if sim.realms[0].globals().S.getSession() is None:break
 sim.check(0,'assert(math.abs(v.x-800)<14 and unsafe==0 and not p.block and not npc.block)')
 print(version,'committed checkpoints',sim.commits,'simulation frames',frames)
# Lifecycle regressions against the real updated files.
exec(compile(test.replace('work/vehicle-release-0.6.1','work/vehicle-release-0.7.1'),'network-071-lifecycle','exec'))
# One lagging client: deny long probes and ensure no server move occurs until a shorter probe succeeds.
ns={};exec(compile(cut.replace('work/vehicle-release-0.6.1','work/vehicle-release-0.7.1'),'network-lag','exec'),ns)
sim=ns['Simulation']()
sim.realms[2].execute('local old=cell.getGridSquare;function cell:getGridSquare(x,y,z)if math.abs(x-loadedX)>32 or math.abs(y-loadedY)>32 then return nil end;return old(self,x,y,z)end')
sim.start();sim.frames(2400)
sim.check(0,'assert(S.getSession()==nil and math.abs(v.x-800)<14 and unsafe==0)')
for who in [1,2]:sim.check(who,'assert(N.session==nil and P.progress==1 and not p.block and not npc.block)')
print('PASS smaller passenger loading window: cap falls back and whole group completes')
