from pathlib import Path
import shutil
root=Path('work/vehicle-release-0.6.1');assert not root.exists();shutil.copytree('work/vehicle-release-0.6.0',root)
p=root/'42/media/lua/client/UMV_Vehicle.lua';s=p.read_text();s=s.replace('    if isClient() or isServer() then say(player,"Vehicle teleport currently supports single-player saves") return false end','    if isClient() then return P.networkStart(player,x,y) end\n    if isServer() then return false end')
s=s.replace('function P.stop(message,success)\n','function P.stop(message,success)\n    if P.session and P.session.network then return P.networkCancel(message) end\n')
s=s.replace('    if not s then return end\n    if getSpecificPlayer(0)', '    if not s or s.network then return end\n    if getSpecificPlayer(0)')
# Cap network hops independently, while retaining the single-player 96-tile behavior.
s=s.replace('    local remaining=distance(x,y,s.targetX,s.targetY)','    local remaining=distance(x,y,s.targetX,s.targetY)\n    local maxStep=s.maxStep or MAX_STEP',1)
s=s.replace('remaining<=MAX_STEP+3','remaining<=maxStep+3').replace('<=MAX_STEP+3 then','<=maxStep+3 then')
s=s.replace('            if progress>1 and (not bestScore','            if length<=maxStep and progress>1 and (not bestScore')
s=s.replace('    for radius=32,96,8 do','    for radius=32,maxStep,8 do')
s=s.replace('return P\n','P.helpers={geometry=geometry,clear=clear,candidate=candidate,place=place,ground=ground,registered=registered}\nreturn P\n')
p.unlink();(root/'42/media/lua/shared/UMV_Vehicle.lua').write_text(s,encoding='utf-8')
p=root/'42/media/lua/client/UMV_Progress.lua';s=p.read_text().replace('local P=require "UMV_Vehicle"','local P=require "UMV_Vehicle"\nrequire "UMV_NetworkClient"').replace('Loaded 0.6.0','Loaded 0.6.1');p.write_text(s,encoding='utf-8')
p=root/'42/mod.info';s=p.read_text(encoding='utf-8').replace('0.6.0','0.6.1');p.write_text(s,encoding='utf-8')
