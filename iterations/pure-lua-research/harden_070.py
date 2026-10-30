from pathlib import Path
p=Path('work/vehicle-release-0.7.0/42/media/lua/client/UMV_RemoteSP.lua');s=p.read_text(encoding='utf-8-sig')
s=s.replace('if H.registered(s) and s.didMove then','if H.registered(s) and (s.didMove or s.touchedVehicle) then',1)
s=s.replace('    vehicle:setWorldTransform(transform)\n    vehicle:checkSurroundingChunks()','    s.touchedVehicle=true\n    vehicle:setWorldTransform(transform)\n    vehicle:checkSurroundingChunks()',1)
s=s.replace('    end\nend\nlocal function restoreProtection(s)','    end\n    actor:getModData().UMVRemoteProtection={god=m.remoteGod,ghost=m.remoteGhost}\nend\nlocal function restoreProtection(s)',1)
s=s.replace('        if m.remoteGhost~=nil then pcall(function()m.actor:setGhostMode(m.remoteGhost)end) end\n','        if m.remoteGhost~=nil then pcall(function()m.actor:setGhostMode(m.remoteGhost)end) end\n        m.actor:getModData().UMVRemoteProtection=nil\n',1)
s=s.replace('    elseif s.remotePhase=="return" then\n        local square=', '''    elseif s.remotePhase=="return" then
        if now()-s.phaseStarted>30000 then
            finish(s,"Return failed; check the vehicle marker at its saved checkpoint",false);return
        end
        local square=''')
s=s.replace('        if s.settle>=12 then finish(s,s.returnReason,false) end','''        if s.settle>=12 then
            local stable=math.abs(s.vehicle:getX()-s.startX)<2 and math.abs(s.vehicle:getY()-s.startY)<2
            finish(s,stable and s.returnReason or "Vehicle position changed during recovery; check its map marker",false)
        end''')
s=s.replace('return R\n','''local function recover(actor)
    if not actor then return end
    local active=P.session
    if active and active.remote then
        for _,m in ipairs(active.occupants) do if m.actor==actor then return end end
    end
    local saved=actor:getModData().UMVRemoteProtection
    if saved then
        if saved.god~=nil then actor:setGodMod(saved.god) end
        if saved.ghost~=nil then actor:setGhostMode(saved.ghost) end
        actor:getModData().UMVRemoteProtection=nil
    end
end
Events.OnGameStart.Add(function()recover(getSpecificPlayer(0))end)
if Events.OnPlayerUpdate then Events.OnPlayerUpdate.Add(recover) end
return R
''')
p.write_text(s,encoding='utf-8')
