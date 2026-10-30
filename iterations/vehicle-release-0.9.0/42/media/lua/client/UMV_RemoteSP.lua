-- Preserve source chunks using unused native chunk-map references, load the
-- destination with the active player map, then move the original live vehicle.
if isClient() or isServer() then return end
local P=require "UMV_Vehicle"
local H=P.helpers
local R={}
local function now() return getTimestampMs() end
local function log(s) print("[MapTeleportVehicle/Remote] "..tostring(s)) end
local function idleMap(slot,width)
    if getSpecificPlayer(slot) then return nil end
    local map=getCell():getChunkMap(slot)
    if not map or type(map.copy)~="function" or type(map.Unload)~="function" then return nil end
    local count=math.floor(width/8)
    for x=0,count-1 do for y=0,count-1 do
        if map:getChunk(x,y) then return nil end
    end end
    return map
end
local function pin(map,main)
    -- copy() adds a native reference for every already-loaded source chunk.
    -- Do not construct an unregistered map or use Dispose(): Dispose clears
    -- the shared global load queue, and map 0 Unload would disable active physics.
    map:copy(main)
end
local function releasePins(s)
    for _,key in ipairs({"sourcePin","destinationPin"}) do
        local map=s[key]
        if map then
            local ok,why=pcall(function() map:Unload() end)
            if not ok then log("pin release failed: "..tostring(why)) end
            s[key]=nil
        end
    end
end
local function protect(m)
    local actor=m.actor
    if type(actor.isGodMod)=="function" and type(actor.setGodMod)=="function" then
        m.remoteGod=actor:isGodMod();actor:setGodMod(true)
    end
    if type(actor.isGhostMode)=="function" and type(actor.setGhostMode)=="function" then
        m.remoteGhost=actor:isGhostMode();actor:setGhostMode(true)
    end
    actor:getModData().UMVRemoteProtection={god=m.remoteGod,ghost=m.remoteGhost}
end
local function restoreProtection(s)
    for _,m in ipairs(s.occupants) do
        if m.remoteGod~=nil then pcall(function()m.actor:setGodMod(m.remoteGod)end) end
        if m.remoteGhost~=nil then pcall(function()m.actor:setGhostMode(m.remoteGhost)end) end
        m.actor:getModData().UMVRemoteProtection=nil
    end
end
local function finish(s,message,success)
    if H.registered(s) and (s.didMove or s.touchedVehicle) then
        local ok,why=pcall(function() H.persistConvoy(s) end)
        if not ok then log("live vehicle save failed: "..tostring(why)) end
    end
    restoreProtection(s)
    s.remote=false
    if success then P.progress=1 end
    -- Keep both pins until native persistence, animal release and UI cleanup
    -- finish. P.stop handles all movement guards and the usual vehicle marker.
    local ok,why=pcall(P.stop,message,success)
    releasePins(s)
    if not ok then
        P.session=nil
        for _,m in ipairs(s.occupants) do
            pcall(function()m.actor:setBlockMovement(m.wasBlocked);m.actor:getModData().PLVTGuard=nil end)
        end
        log("finish error: "..tostring(why))
    end
    log((success and "COMPLETE " or "STOP ").."vehicleJumps="..(s.remoteJumps or 0)..
        " elapsedMs="..(now()-s.remoteStarted).." reason="..message)
end
local function scout(s,x,y)
    for _,m in ipairs(s.occupants) do m.actor:teleportTo(x,y,0) end
    -- Start the same registered map transition that native player movement uses.
    -- The separate source reference prevents that transition from unloading the car.
    s.mainMap:ProcessChunkPos(s.player)
end
local function requestReturn(s,reason)
    if s.remotePhase=="return" or s.remotePhase=="returnSettle" then return end
    s.returnReason=reason or "Cancelled; returned to the starting checkpoint"
    -- The destination must also remain pinned if a partial move already put the
    -- vehicle in it. Reusing the source slot here would lose its only reference.
    if not s.destinationPin then
        s.destinationPin=s.spareDestination
        pin(s.destinationPin,s.mainMap)
    end
    s.remotePhase="return";s.phaseStarted=now();P.status="Returning to the starting checkpoint..."
    scout(s,s.startX,s.startY)
    log("RETURN requested: "..s.returnReason)
end
function R.cancel(message)
    local s=P.session
    if s and s.remote then requestReturn(s,message) end
end
P.remoteCancel=R.cancel
local function moveVehicle(s,x,y,square)
    assert(H.registered(s),"Vehicle registration changed before the distant move")
    local vehicle=s.vehicle
    local transform=Transform.new();vehicle:getWorldTransform(transform)
    local origin=transform:getOrigin();local world=vehicle:getWorldPos(0,0,0,Vector3f.new())
    origin:set(origin:x()+x-world:x(),origin:y(),origin:z()+y-world:y())
    -- The pinned origin is intentionally outside the active physics map. Prime
    -- the mirror at the loaded destination, reactivate there, then submit the
    -- transform again through the checked normal placement path.
    s.touchedVehicle=true
    vehicle:setWorldTransform(transform)
    vehicle:checkSurroundingChunks();vehicle:setPhysicsActive(true,true)
    H.place(s,x,y,square)
    s.didMove=true
end
local function exits(s,x,y)
    local result,used={},{}
    for i,_ in ipairs(s.occupants) do
        local chosen
        for radius=math.ceil(s.radius)+1,math.ceil(s.radius)+8 do
            for dx=-radius,radius do for dy=-radius,radius do
                local ax,ay=math.floor(x)+dx+0.5,math.floor(y)+dy+0.5
                local key=ax..","..ay
                if not chosen and math.max(math.abs(dx),math.abs(dy))==radius and not used[key] then
                    local square=H.ground(ax,ay)
                    if square and not square:getVehicleContainer() and H.outsideConvoy(s,ax,ay,x,y) then chosen={ax,ay};used[key]=true end
                end
            end end
            if chosen then break end
        end
        if not chosen then return nil end
        result[i]=chosen
    end
    return result
end
local function landing(s)
    local x,y=math.floor(s.targetX)+0.5,math.floor(s.targetY)+0.5
    local square=H.clear(s,x,y)
    if square then local positions=exits(s,x,y);if positions then return x,y,square,positions end end
    for _,radius in ipairs({2,4,6,8,12,16,24}) do
        for degrees=0,345,15 do
            local a=degrees*math.pi/180
            local cx,cy=math.floor(x+radius*math.cos(a))+0.5,math.floor(y+radius*math.sin(a))+0.5
            square=H.clear(s,cx,cy)
            if square then local positions=exits(s,cx,cy);if positions then return cx,cy,square,positions end end
        end
    end
end
function R.prepare(s)
    local cell=getCell()
    if type(cell.getChunkMap)~="function" or type(s.player.getPlayerNum)~="function" or
        type(getNumActivePlayers)~="function" or getNumActivePlayers()~=1 then return false end
    local main=cell:getChunkMap(s.player:getPlayerNum())
    if not main or type(main.ProcessChunkPos)~="function" then return false end
    local width=main:getWidthInTiles()
    if s.total<=width or not H.clear(s,s.startX,s.startY) then return false end
    local source=idleMap(3,width);local destination=idleMap(2,width)
    if not source or not destination then log("No unused native chunk slots; using loaded-area steps");return false end
    s.remote=true;s.mainMap=main;s.sourcePin=source;s.spareDestination=destination
    s.remoteStarted=now();s.phaseStarted=now();s.remotePhase="loading";s.remoteJumps=0
    pin(source,main)
    for _,m in ipairs(s.occupants) do
        protect(m)
        assert((m.vehicle or s.vehicle):exit(m.actor),"Could not release an occupant before loading")
        triggerEvent("OnExitVehicle",m.actor)
    end
    s.vehicle:shutOff()
    scout(s,math.floor(s.targetX)+0.5,math.floor(s.targetY)+0.5)
    P.progress=0.1;P.status="Loading destination; holding origin..."
    log("START distance="..s.total.." sourceSlot=3 destinationSlot=2; original vehicle retained")
    return true
end
P.remotePrepare=R.prepare
local function update()
    local s=P.session
    if not s or not s.remote then return end
    assert(H.registered(s),"The original vehicle is no longer registered")
    if getSpecificPlayer(s.player:getPlayerNum())~=s.player then
        -- Preserve the last confirmed vehicle location if NPC possession changes
        -- control mid-load. Do not steer the new player's active map elsewhere.
        if not s.didMove then
            for _,m in ipairs(s.occupants) do m.actor:teleportTo(s.startX,s.startY,0) end
        end
        finish(s,"Control changed; vehicle retained at its last checkpoint",false);return
    end
    if s.remotePhase=="loading" then
        if now()-s.phaseStarted>30000 then requestReturn(s,"Destination did not load; returned to origin");return end
        if s.searchAfter and now()<s.searchAfter then return end
        s.searchAfter=now()+250
        local x,y,square,positions=landing(s)
        if not x then return end
        s.destinationPin=s.spareDestination;pin(s.destinationPin,s.mainMap)
        local moved,why=pcall(moveVehicle,s,x,y,square)
        if not moved then requestReturn(s,"Vehicle placement failed: "..tostring(why));return end
        s.remoteJumps=s.remoteJumps+1;s.hops=s.remoteJumps;s.landingX=x;s.landingY=y
        for i,m in ipairs(s.occupants) do m.actor:teleportTo(positions[i][1],positions[i][2],0) end
        s.remotePhase="settle";s.settle=0;P.progress=0.9;P.status="Confirming the vehicle at destination..."
        log("JUMP distance="..math.sqrt((x-s.startX)^2+(y-s.startY)^2).." loadMs="..(now()-s.remoteStarted))
    elseif s.remotePhase=="settle" then
        s.settle=s.settle+1
        if s.settle<12 then return end
        if math.abs(s.vehicle:getX()-s.landingX)>=2 or math.abs(s.vehicle:getY()-s.landingY)>=2 then
            requestReturn(s,"Vehicle did not stay at destination; returned to origin");return
        end
        finish(s,"Vehicle transfer completed",true)
    elseif s.remotePhase=="return" then
        if now()-s.phaseStarted>30000 then
            finish(s,"Return failed; check the vehicle marker at its saved checkpoint",false);return
        end
        local square=H.clear(s,s.startX,s.startY)
        if square then
            local restored,why=pcall(moveVehicle,s,s.startX,s.startY,square)
            if not restored then log("Return placement retry: "..tostring(why));return end
            local positions=exits(s,s.startX,s.startY)
            if positions then
                for i,m in ipairs(s.occupants) do m.actor:teleportTo(positions[i][1],positions[i][2],0) end
            end
            s.remotePhase="returnSettle";s.settle=0
        elseif now()-s.phaseStarted>30000 then
            finish(s,"Return loading failed; vehicle saved at its last protected checkpoint",false)
        end
    elseif s.remotePhase=="returnSettle" then
        s.settle=s.settle+1
        if s.settle>=12 then
            local stable=math.abs(s.vehicle:getX()-s.startX)<2 and math.abs(s.vehicle:getY()-s.startY)<2
            finish(s,stable and s.returnReason or "Vehicle position changed during recovery; check its map marker",false)
        end
    end
end
Events.OnTick.Add(function()
    local ok,why=pcall(update)
    if not ok then
        log("ERROR "..tostring(why))
        local s=P.session
        if s and s.remote then
            local returned,reason=pcall(requestReturn,s,"Transfer stopped: "..tostring(why))
            if not returned then finish(s,"Could not resume transfer: "..tostring(reason),false) end
        end
    end
end)
local function recover(actor)
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
