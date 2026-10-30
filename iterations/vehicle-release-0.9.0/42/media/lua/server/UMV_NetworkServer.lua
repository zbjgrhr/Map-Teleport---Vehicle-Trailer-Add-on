-- Server coordinates the transfer; clients never choose an authoritative landing.
if not isServer() then return end
local P=require "UMV_Vehicle"
local H=P.helpers
local Animals=require "UMV_Animals"
local MODULE="UMVVehicle"
local active,serial,lastRequest=nil,0,{}
local returnRemote
local function now() return getTimestampMs() end
local function log(s) print("[MapTeleportVehicle/Server] "..tostring(s)) end
local function send(actor,command,args)
    local ok,why=pcall(sendServerCommand,actor,MODULE,command,args)
    if not ok then log("client notification: "..tostring(why)) end
end
local function finite(n) return type(n)=="number" and n==n and math.abs(n)<10000000 end
local function broadcast(command,args) sendServerCommand(MODULE,command,args) end
local function member(s,actor)
    for _,m in ipairs(s.occupants) do if m.actor==actor then return m end end
end
local function all(s,field)
    for _,m in ipairs(s.occupants) do if not m[field] then return false end end
    return true
end
local function identity(s)
    return H.registered(s) and s.vehicle:getSqlId()==s.sqlId
end
local function finish(reason,success)
    local s=active;if not s then return end
    if s.remoteScouting and not s.remoteCommitted and not s.remoteReturning and returnRemote then
        return returnRemote(s,reason)
    end
    active=nil
    if s.begun and identity(s) then
        -- Native exit writes the live vehicle record before checking the seat.
        -- Pass nil to save without invoking any character's seat behavior.
        local ok,why=pcall(function() H.persistConvoy(s) end)
        if not ok then log("checkpoint save: "..tostring(why)) end
    end
    for _,m in ipairs(s.occupants) do
        if m.staged then
            local ok,released,why=pcall(Animals.release,m.actor,m.animals,m.actor:getX(),m.actor:getY())
            if not ok or not released then log("animal restore: "..tostring(ok and why or released)) end
        end
        pcall(function()
            m.actor:setBlockMovement(m.wasBlocked)
            if m.remoteGod~=nil then m.actor:setGodMod(m.remoteGod) end
            if m.remoteGhost~=nil then m.actor:setGhostMode(m.remoteGhost) end
        end)
        send(m.actor,"finish",{token=s.token,vehicleId=s.id,sqlId=s.sqlId,vehicles=H.convoyPayload(s,s.vehicle:getX(),s.vehicle:getY()),
            x=s.vehicle:getX(),y=s.vehicle:getY(),playerX=m.actor:getX(),playerY=m.actor:getY(),success=success==true,reason=reason,mark=s.begun==true})
    end
    log((success and "COMPLETE " or "STOP ")..reason.." sql="..s.sqlId.." steps="..s.sequence)
end
local function exitSquares(s,x,y)
    local positions,used={},{}
    for i,m in ipairs(s.occupants) do
        local chosen
        for radius=math.ceil(s.radius)+1,math.ceil(s.radius)+8 do
            for dx=-radius,radius do for dy=-radius,radius do
                local ax,ay=math.floor(x)+dx+0.5,math.floor(y)+dy+0.5
                local key=ax..","..ay
                if not chosen and math.max(math.abs(dx),math.abs(dy))==radius and not used[key] then
                    local square=H.ground(ax,ay)
                    if square and not square:getVehicleContainer() and H.outsideConvoy(s,ax,ay,x,y) then chosen={x=ax,y=ay};used[key]=true end
                end
            end end
            if chosen then break end
        end
        if not chosen then return nil end
        positions[i]=chosen
    end
    return positions
end
local function begin(s)
    assert(identity(s),"Vehicle registration changed before departure")
    for _,m in ipairs(s.occupants) do
        assert(m.actor:getVehicle()==m.vehicle and m.vehicle:getCharacter(m.seat)==m.actor,"An occupant changed seats")
    end
    assert(s.vehicle:getCurrentAbsoluteSpeedKmHour()<=1 and
        math.abs(s.vehicle:getX()-s.startX)<2 and math.abs(s.vehicle:getY()-s.startY)<2,
        "Vehicle moved while passengers were preparing")
    local exits=assert(exitSquares(s,s.vehicle:getX(),s.vehicle:getY()),"No room to leave the vehicle")
    s.originExits=exits
    -- Revoke driving authority before exiting or moving the vehicle.
    for _,car in ipairs(H.convoyMembers(s)) do car.vehicle:authorizationChanged(nil) end
    assert(s.vehicle:getNetPlayerId()==-1,"Could not obtain server vehicle authority")
    s.begun=true
    for i,m in ipairs(s.occupants) do
        m.staged=true
        local ok,why=Animals.stage(m.actor,m.animals);assert(ok,why)
        assert(m.vehicle:exit(m.actor),"Could not release a passenger seat")
        m.actor:teleportTo(exits[i].x,exits[i].y,0)
        triggerEvent("OnExitVehicle",m.actor)
    end
    s.vehicle:shutOff()
    for i,m in ipairs(s.occupants) do
        send(m.actor,"begin",{token=s.token,playerX=exits[i].x,playerY=exits[i].y})
    end
    s.phase="lease";s.changed=now()
end
local function request(actor,args)
    if active then send(actor,"rejected",{reason="Another vehicle transfer is in progress"});return end
    if lastRequest[actor] and now()-lastRequest[actor]<1000 then send(actor,"rejected",{reason="Wait before teleporting again"});return end
    lastRequest[actor]=now()
    assert(finite(args.x) and finite(args.y),"Invalid destination")
    assert(getWorld():getMetaGrid():isValidChunk(math.floor(args.x/8),math.floor(args.y/8)),"Destination is outside the map")
    local vehicle=actor:getVehicle()
    assert(vehicle and vehicle:getId()==args.vehicleId and vehicle:getDriver()==actor,"The driver must initiate vehicle teleport")
    assert(not actor:isDead() and vehicle:getCurrentAbsoluteSpeedKmHour()<=1,"Stop the vehicle before teleporting")
    assert(vehicle:getZ()==0,"Start on ground level")
    local s=H.geometry(vehicle)
    serial=serial+1;s.token=tostring(now())..":"..serial
    s.vehicle=vehicle;s.id=vehicle:getId();s.sqlId=vehicle:getSqlId();s.driver=actor
    s.targetX=math.floor(args.x);s.targetY=math.floor(args.y);s.maxStep=64
    s.startX=vehicle:getX();s.startY=vehicle:getY();s.total=math.sqrt((s.startX-s.targetX)^2+(s.startY-s.targetY)^2)
    s.started=now();s.changed=now();s.sequence=0;s.visited={};s.phase="prepare";s.occupants={}
    assert(identity(s),"Vehicle is not registered")
    for _,car in ipairs(H.convoyMembers(s)) do
    for seat=0,car.vehicle:getMaxPassengers()-1 do
        local occupant=car.vehicle:getCharacter(seat)
        if occupant then
            assert(occupant:getOnlineID()>=0,"An occupant has no network player identity")
            local animals,why=Animals.capture(occupant);assert(animals,why)
            table.insert(s.occupants,{actor=occupant,vehicle=car.vehicle,seat=seat,animals=animals,wasBlocked=occupant:isBlockMovement()})
        end
    end
    end
    active=s
    for _,m in ipairs(s.occupants) do
        m.actor:setBlockMovement(true)
        send(m.actor,"prepare",{token=s.token,vehicleId=s.id,sqlId=s.sqlId,vehicles=H.convoyPayload(s,s.vehicle:getX(),s.vehicle:getY()),version="0.9.0"})
    end
    log("START token="..s.token.." occupants="..#s.occupants)
end
local function command(module,action,actor,args)
    if module~=MODULE or not actor or type(args)~="table" then return end
    if action=="request" then
        local ok,why=pcall(request,actor,args)
        if not ok then
            if active and active.driver==actor then finish(tostring(why),false)
            else send(actor,"rejected",{reason=tostring(why)}) end
        end
        return
    end
    local s=active
    if not s or args.token~=s.token then return end
    local m=member(s,actor);if not m then return end
    if action=="cancel" then finish("Cancelled at the current checkpoint",false);return end
    if action=="ready" and s.phase=="prepare" and args.version=="0.9.0" then
        if args.vehiclesReady==false then finish("A connected vehicle is not loaded on a client; nothing moved",false);return end
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
    if action=="scouted" and s.phase=="remoteScout" and m~=s.anchor then m.scouted=true;return end
    if action=="leased" and s.phase=="lease" then m.leased=true;return end
    if args.sequence~=s.sequence then return end
    if action=="probe" and (s.phase=="probe" or s.phase=="remoteProbe") then
        if args.ready==true then m.probed=true
        elseif s.phase=="remoteProbe" then finish("A destination client could not confirm the landing",false)
        else
            local attempted=math.sqrt((s.stepX-s.vehicle:getX())^2+(s.stepY-s.vehicle:getY())^2)
            if attempted<=9 then finish("No shared loaded landing; stopped at the checkpoint",false);return end
            local smaller=8
            for _,length in ipairs({56,48,40,32,24,18,12,8}) do
                if length<attempted-1 and length<s.maxStep then smaller=length;break end
            end
            s.phase="plan";s.maxStep=smaller;s.retry=(s.retry or 0)+1;s.changed=now()
            log("Client landing not ready; reducing step cap to "..smaller)
        end
    elseif action=="arrived" and (s.phase=="arrive" or s.phase=="remoteArrive" or s.phase=="remoteReturn") then
        if args.ready~=true then finish("A client could not confirm the vehicle; stopped at the current checkpoint",false)
        else m.arrived=true end
    end
end
Events.OnClientCommand.Add(command)

local function protectRemote(s)
    for _,m in ipairs(s.occupants) do
        if type(m.actor.isGodMod)=="function" then m.remoteGod=m.actor:isGodMod();m.actor:setGodMod(true) end
        if type(m.actor.isGhostMode)=="function" then m.remoteGhost=m.actor:isGhostMode();m.actor:setGhostMode(true) end
    end
end
returnRemote=function(s,reason)
    s.remoteReturning=true;s.returnReason=reason;s.sequence=s.sequence+1
    local positions=exitSquares(s,s.startX,s.startY) or s.originExits
    if not positions then s.remoteScouting=false;finish(reason.."; source exit unavailable",false);return end
    for i,m in ipairs(s.occupants) do
        m.arrived=false;m.actor:teleportTo(positions[i].x,positions[i].y,0)
        send(m.actor,"move",{token=s.token,sequence=s.sequence,vehicleId=s.id,sqlId=s.sqlId,vehicles=H.convoyPayload(s,s.vehicle:getX(),s.vehicle:getY()),
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
            if m~=s.anchor then send(m.actor,"probe",{token=s.token,sequence=s.sequence,vehicleId=s.id,sqlId=s.sqlId,vehicles=H.convoyPayload(s,x,y),
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
        broadcast("commit",{token=s.token,sequence=s.sequence,vehicleId=s.id,sqlId=s.sqlId,vehicles=H.convoyPayload(s,s.stepX,s.stepY),x=s.stepX,y=s.stepY})
        for i,m in ipairs(s.occupants) do
            m.arrived=false;m.actor:teleportTo(s.exits[i].x,s.exits[i].y,0)
            send(m.actor,"move",{token=s.token,sequence=s.sequence,vehicleId=s.id,sqlId=s.sqlId,vehicles=H.convoyPayload(s,s.stepX,s.stepY),
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

local function update()
    local s=active;if not s then return end
    assert(identity(s),"Vehicle registration changed")
    assert(s.vehicle:getNetPlayerId()==-1 or not s.begun,"Vehicle authority changed")
    for _,m in ipairs(s.occupants) do assert(not m.actor:isDead(),"An occupant died") end
    if now()-s.started>600000 or now()-s.changed>20000 then finish("Transfer timed out at the current checkpoint",false);return end
    if s.phase=="prepare" then if all(s,"ready") then begin(s) end;return end
    if s.phase=="lease" then
        if all(s,"leased") then
            local capable=#s.occupants>=2 and s.total>128 and H.clear(s,s.startX,s.startY)~=nil
            for _,m in ipairs(s.occupants) do capable=capable and m.remoteCap end
            if capable then
                s.phase="remotePin"
                for _,m in ipairs(s.occupants) do send(m.actor,"pin",{token=s.token}) end
            else s.phase="plan" end
            s.changed=now()
        end
        return
    end
    if remoteUpdate(s) then return end
    if s.phase=="probe" then
        if not all(s,"probed") then return end
        local square=assert(H.clear(s,s.stepX,s.stepY),"Landing changed before commit")
        local oldX,oldY=s.vehicle:getX(),s.vehicle:getY()
        local oldSquare=getCell():getGridSquare(math.floor(oldX),math.floor(oldY),0)
        local moved,why=pcall(H.place,s,s.stepX,s.stepY,square)
        if not moved then
            if identity(s) and oldSquare then
                local restored,reason=pcall(H.place,s,oldX,oldY,oldSquare)
                log("step rollback="..tostring(restored).." "..tostring(reason))
            end
            error(why)
        end
        for i,m in ipairs(s.occupants) do
            m.actor:teleportTo(s.exits[i].x,s.exits[i].y,0)
        end
        broadcast("commit",{token=s.token,sequence=s.sequence,vehicleId=s.id,sqlId=s.sqlId,vehicles=H.convoyPayload(s,s.stepX,s.stepY),x=s.stepX,y=s.stepY})
        for i,m in ipairs(s.occupants) do
            send(m.actor,"move",{token=s.token,sequence=s.sequence,vehicleId=s.id,sqlId=s.sqlId,vehicles=H.convoyPayload(s,s.stepX,s.stepY),
                x=s.stepX,y=s.stepY,playerX=s.exits[i].x,playerY=s.exits[i].y,
                progress=math.max(0,1-math.sqrt((s.stepX-s.targetX)^2+(s.stepY-s.targetY)^2)/math.max(1,s.total))})
        end
        s.phase="arrive";s.changed=now();return
    end
    if s.phase=="arrive" then
        if not all(s,"arrived") then return end
        s.retry=0
        if s.final then finish("Vehicle transfer completed",true);return end
        s.phase="plan";s.changed=now();return
    end
    -- Do not repeat the expensive landing search on every server tick.
    if s.searchAfter and now()<s.searchAfter then return end
    s.searchAfter=now()+250
    local x,y,square,final=H.candidate(s)
    if not x then return end
    local exits=exitSquares(s,x,y);if not exits then return end
    s.sequence=s.sequence+1;s.stepX=x;s.stepY=y;s.final=final;s.exits=exits
    for i,m in ipairs(s.occupants) do
        m.probed=false;m.arrived=false
        send(m.actor,"probe",{token=s.token,sequence=s.sequence,vehicleId=s.id,sqlId=s.sqlId,vehicles=H.convoyPayload(s,x,y),
            x=x,y=y,playerX=exits[i].x,playerY=exits[i].y})
    end
    s.phase="probe";s.changed=now()
    if s.retry and s.retry>=10 then finish("Clients could not load a shared landing; stopped at the checkpoint",false) end
end
Events.OnTick.Add(function()
    local ok,why=pcall(update)
    if not ok then log(why);finish("Vehicle transfer stopped: "..tostring(why),false) end
end)
return {command=command,update=update,getSession=function()return active end}
