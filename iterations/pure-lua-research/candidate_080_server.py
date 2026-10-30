from pathlib import Path
import shutil
root=Path('work/vehicle-candidate-0.8.0');assert not root.exists();shutil.copytree('work/vehicle-release-0.7.1',root)
for p in root.rglob('*'):
 if p.is_file() and p.suffix in ('.lua','.md','.info'):
  p.write_text(p.read_text(encoding='utf-8-sig').replace('0.7.1','0.8.0'),encoding='utf-8')
p=root/'42/media/lua/server/UMV_NetworkServer.lua';s=p.read_text()
# Forward reference: early cancellation/timeout must return scouts while the source anchor remains.
s=s.replace('local active,serial,lastRequest=nil,0,{}','local active,serial,lastRequest=nil,0,{}\nlocal returnRemote')
s=s.replace('    active=nil\n    if s.begun', '''    if s.remoteScouting and not s.remoteCommitted and not s.remoteReturning and returnRemote then
        return returnRemote(s,reason)
    end
    active=nil
    if s.begun''',1)
s=s.replace('        pcall(function() m.actor:setBlockMovement(m.wasBlocked) end)','''        pcall(function()
            m.actor:setBlockMovement(m.wasBlocked)
            if m.remoteGod~=nil then m.actor:setGodMod(m.remoteGod) end
            if m.remoteGhost~=nil then m.actor:setGhostMode(m.remoteGhost) end
        end)''',1)
s=s.replace('if action=="ready" and s.phase=="prepare" and args.version=="0.8.0" then m.ready=true;return end','''if action=="ready" and s.phase=="prepare" and args.version=="0.8.0" then
        m.ready=true;m.remoteCap=args.remoteCap==true;return
    end
    if action=="pinned" and s.phase=="remotePin" then
        if args.ready==true then m.pinned=true
        else
            for _,o in ipairs(s.occupants) do send(o.actor,"releasePin",{token=s.token}) end
            s.phase="plan";s.changed=now()
        end
        return
    end
    if action=="scouted" and s.phase=="remoteScout" and m~=s.anchor then m.scouted=true;return end''')
s=s.replace('if action=="probe" and s.phase=="probe" then','if action=="probe" and (s.phase=="probe" or s.phase=="remoteProbe") then')
s=s.replace('        if args.ready==true then m.probed=true\n        else','        if args.ready==true then m.probed=true\n        elseif s.phase=="remoteProbe" then finish("A destination client could not confirm the landing",false)\n        else',1)
s=s.replace('elseif action=="arrived" and s.phase=="arrive" then','elseif action=="arrived" and (s.phase=="arrive" or s.phase=="remoteArrive" or s.phase=="remoteReturn") then')
insert='''
local function protectRemote(s)
    for _,m in ipairs(s.occupants) do
        if type(m.actor.isGodMod)=="function" then m.remoteGod=m.actor:isGodMod();m.actor:setGodMod(true) end
        if type(m.actor.isGhostMode)=="function" then m.remoteGhost=m.actor:isGhostMode();m.actor:setGhostMode(true) end
    end
end
returnRemote=function(s,reason)
    s.remoteReturning=true;s.returnReason=reason;s.sequence=s.sequence+1
    local positions=exitSquares(s,s.startX,s.startY)
    if not positions then s.remoteScouting=false;finish(reason.."; source exit unavailable",false);return end
    for i,m in ipairs(s.occupants) do
        m.arrived=false;m.actor:teleportTo(positions[i].x,positions[i].y,0)
        send(m.actor,"move",{token=s.token,sequence=s.sequence,vehicleId=s.id,sqlId=s.sqlId,
            x=s.vehicle:getX(),y=s.vehicle:getY(),playerX=positions[i].x,playerY=positions[i].y,remote=true,progress=0})
    end
    s.phase="remoteReturn";s.changed=now()
end
local function remoteLanding(s)
    local x,y=math.floor(s.targetX)+0.5,math.floor(s.targetY)+0.5
    for radius=0,24,2 do
        for degrees=0,345,15 do
            local a=degrees*math.pi/180
            local cx,cy=math.floor(x+radius*math.cos(a))+0.5,math.floor(y+radius*math.sin(a))+0.5
            local square=H.clear(s,cx,cy)
            if square then local positions=exitSquares(s,cx,cy);if positions then return cx,cy,square,positions end end
            if radius==0 then break end
        end
    end
end
local function remoteUpdate(s)
    if s.phase=="remotePin" then
        if not all(s,"pinned") then return true end
        protectRemote(s);s.remoteScouting=true;s.anchor=s.occupants[#s.occupants]
        for _,m in ipairs(s.occupants) do
            if m~=s.anchor then
                m.actor:teleportTo(s.targetX+0.5,s.targetY+0.5,0)
                send(m.actor,"scout",{token=s.token,x=s.targetX+0.5,y=s.targetY+0.5})
            end
        end
        s.phase="remoteScout";s.changed=now();return true
    end
    if s.phase=="remoteScout" then
        for _,m in ipairs(s.occupants) do if m~=s.anchor and not m.scouted then return true end end
        if s.searchAfter and now()<s.searchAfter then return true end
        s.searchAfter=now()+250
        local x,y,square,positions=remoteLanding(s)
        if not x then return true end
        s.sequence=s.sequence+1;s.stepX=x;s.stepY=y;s.exits=positions
        for i,m in ipairs(s.occupants) do
            m.probed=m==s.anchor
            if m~=s.anchor then send(m.actor,"probe",{token=s.token,sequence=s.sequence,vehicleId=s.id,sqlId=s.sqlId,
                x=x,y=y,playerX=positions[i].x,playerY=positions[i].y}) end
        end
        s.phase="remoteProbe";s.changed=now();return true
    end
    if s.phase=="remoteProbe" then
        if not all(s,"probed") then return true end
        -- Keep the last player's server relevance at the source until native
        -- chunk membership is committed at the already-loaded destination.
        assert(math.abs(s.anchor.actor:getX()-s.startX)<20 and math.abs(s.anchor.actor:getY()-s.startY)<20,"Source anchor moved")
        local oldSquare=assert(H.clear(s,s.startX,s.startY),"Source area no longer loaded")
        local square=assert(H.clear(s,s.stepX,s.stepY),"Destination changed")
        local moved,why=pcall(H.place,s,s.stepX,s.stepY,square)
        if not moved then
            local restored=pcall(H.place,s,s.startX,s.startY,oldSquare)
            if not restored then s.remoteCommitted=true end
            error(why)
        end
        s.remoteCommitted=true;s.final=true
        broadcast("commit",{token=s.token,sequence=s.sequence,vehicleId=s.id,sqlId=s.sqlId,x=s.stepX,y=s.stepY})
        for i,m in ipairs(s.occupants) do
            m.arrived=false;m.actor:teleportTo(s.exits[i].x,s.exits[i].y,0)
            send(m.actor,"move",{token=s.token,sequence=s.sequence,vehicleId=s.id,sqlId=s.sqlId,
                x=s.stepX,y=s.stepY,playerX=s.exits[i].x,playerY=s.exits[i].y,remote=true,progress=0.95})
        end
        s.phase="remoteArrive";s.changed=now();return true
    end
    if s.phase=="remoteArrive" or s.phase=="remoteReturn" then
        if all(s,"arrived") then
            if s.phase=="remoteReturn" then s.remoteScouting=false;finish(s.returnReason,false)
            else finish("Vehicle transfer completed",true) end
        end
        return true
    end
    return false
end
'''
s=s.replace('local function update()\n',insert+'\nlocal function update()\n',1)
s=s.replace('    if s.phase=="lease" then if all(s,"leased") then s.phase="plan";s.changed=now() end;return end','''    if s.phase=="lease" then
        if all(s,"leased") then
            local capable=#s.occupants>=2 and s.total>128
            for _,m in ipairs(s.occupants) do capable=capable and m.remoteCap end
            if capable then
                s.phase="remotePin"
                for _,m in ipairs(s.occupants) do send(m.actor,"pin",{token=s.token}) end
            else s.phase="plan" end
            s.changed=now()
        end
        return
    end
    if remoteUpdate(s) then return end''',1)
p.write_text(s,encoding='utf-8')
