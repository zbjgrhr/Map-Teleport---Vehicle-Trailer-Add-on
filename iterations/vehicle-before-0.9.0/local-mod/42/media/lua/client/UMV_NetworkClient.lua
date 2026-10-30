if not isClient() then return end
local P=require "UMV_Vehicle"
local H=P.helpers
local MODULE="UMVVehicle"
local N={session=nil,pending={},cleanup=nil}
local function send(action,args) sendClientCommand(N.session.player,MODULE,action,args) end
local function findVehicle(args)
    local v=getVehicleById(args.vehicleId)
    if v and not v:isRemovedFromWorld() and v:getSqlId()==args.sqlId then return v end
    -- A normally unloaded/reloaded server vehicle may receive a new runtime ID.
    -- Match its persistent SQL identity without recreating or re-registering it.
    local iterator=getCell():getVehicles():iterator()
    while iterator:hasNext() do
        local member=iterator:next()
        if not member:isRemovedFromWorld() and member:getSqlId()==args.sqlId then return member end
    end
end
local function localPlayer()
    local s=N.session
    if s and s.player then return s.player end
    return getSpecificPlayer(0)
end
local function freeze(actor)
    local guard={wasBlocked=actor:isBlockMovement()}
    actor:getModData().UMVNetworkGuard=guard;actor:setBlockMovement(true)
    return guard
end
local function unfreeze(actor,guard)
    actor:setBlockMovement(guard and guard.wasBlocked==true)
    if guard and guard.god~=nil then actor:setGodMod(guard.god) end
    if guard and guard.ghost~=nil then actor:setGhostMode(guard.ghost) end
    actor:getModData().UMVNetworkGuard=nil
end
local function mirror(args)
    local v=findVehicle(args)
    if not v then return false end
    local square=getCell():getGridSquare(math.floor(args.x),math.floor(args.y),0)
    if not square then return false end
    local driver=v:getDriver()
    if driver then v:authorizationServerOnSeat(driver,false) end
    local t=Transform.new();v:getWorldTransform(t)
    local origin=t:getOrigin();local world=v:getWorldPos(0,0,0,Vector3f.new())
    origin:set(origin:x()+args.x-world:x(),origin:y(),origin:z()+args.y-world:y())
    v:setWorldTransform(t)
    v:checkSurroundingChunks()
    v:setPhysicsActive(true,true);v:setWorldTransform(t)
    v:setX(args.x);v:setY(args.y);v:setZ(0);v:setCurrent(square);v:update()
    v:setPhysicsActive(false,false)
    return math.abs(v:getX()-args.x)<2 and math.abs(v:getY()-args.y)<2
end
function N.start(player,x,y)
    if N.session or P.session then return false end
    local vehicle=player and player:getVehicle()
    if not vehicle then return false end
    if vehicle:getDriver()~=player then player:Say("[UMT] The driver must start vehicle teleport");return false end
    N.session={network=true,player=player,vehicle=vehicle,guard=freeze(player),requested=getTimestampMs()}
    P.session=N.session;P.status="Waiting for server and passengers...";P.progress=0
    if P.onStarted then P.onStarted(player) end
    send("request",{vehicleId=vehicle:getId(),x=math.floor(x),y=math.floor(y)})
    return true
end
function N.cancel()
    local s=N.session;if not s then return end
    if s.token then send("cancel",{token=s.token})
    else s.cancelRequested=true end
    P.status="Waiting for server to stop at the checkpoint..."
end
P.networkStart=N.start;P.networkCancel=N.cancel
local detach
local function stop(args)
    local s=N.session;if not s then return end
    if args.token and s.token and args.token~=s.token then return end
    if args.mark and args.playerX and args.playerY then
        pcall(mirror,args)
        detach(s.player)
        s.player:teleportTo(args.playerX,args.playerY,0)
    end
    if s.sourcePin then
        N.cleanup={map=s.sourcePin,args=args,stable=0};s.sourcePin=nil
    end
    unfreeze(s.player,s.guard)
    P.status=args.reason or "Vehicle transfer ended";P.progress=args.success and 1 or P.progress
    N.session=nil;P.session=nil
    if args.mark and P.markVehicle then P.markVehicle(args.x,args.y) end
    s.player:Say("[UMT] "..P.status)
    if P.onStopped then P.onStopped(args.success,nil) end
end
detach=function(actor)
    local vehicle=actor:getVehicle()
    if not vehicle then return end
    local driver=vehicle:getDriver()
    if driver then vehicle:authorizationServerOnSeat(driver,false) end
    -- The server already performed native exit and persistence. Avoid a second
    -- client exit packet racing the transfer; exitRSync is the native receive path.
    vehicle:exitRSync(actor)
    triggerEvent("OnExitVehicle",actor)
end
local function pinAvailable(actor)
    if type(getNumActivePlayers)~="function" or getNumActivePlayers()~=1 or
        type(actor.getPlayerNum)~="function" or getSpecificPlayer(3) or
        type(getCell().getChunkMap)~="function" then return nil end
    local main=getCell():getChunkMap(actor:getPlayerNum());local map=getCell():getChunkMap(3)
    if not main or not map or type(map.copy)~="function" or type(map.Unload)~="function" then return nil end
    for x=0,math.floor(main:getWidthInTiles()/8)-1 do for y=0,math.floor(main:getWidthInTiles()/8)-1 do
        if map:getChunk(x,y) then return nil end
    end end
    return map,main
end
local function protectScout(s)
    if type(s.player.isGodMod)=="function" and s.guard.god==nil then
        s.guard.god=s.player:isGodMod();s.player:setGodMod(true)
    end
    if type(s.player.isGhostMode)=="function" and s.guard.ghost==nil then
        s.guard.ghost=s.player:isGhostMode();s.player:setGhostMode(true)
    end
end
local function command(module,action,args)
    if module~=MODULE or type(args)~="table" then return end
    if action=="commit" then
        N.pending[tostring(args.sqlId)]=args
        if mirror(args) then N.pending[tostring(args.sqlId)]=nil end
        return
    end
    if action=="prepare" then
        if args.version~="0.8.0" then return end
        local s=N.session
        if not s then
            local actor=getSpecificPlayer(0)
            if not actor or not actor:getVehicle() or actor:getVehicle():getId()~=args.vehicleId then return end
            s={network=true,player=actor,vehicle=actor:getVehicle(),guard=freeze(actor),requested=getTimestampMs()}
            N.session=s;P.session=s;P.progress=0
            if P.onStarted then P.onStarted(actor) end
        end
        s.token=args.token;s.sqlId=args.sqlId;s.vehicleId=args.vehicleId
        send("ready",{token=s.token,version="0.8.0",remoteCap=pinAvailable(s.player)~=nil})
        if s.cancelRequested then send("cancel",{token=s.token}) end
        return
    end
    local s=N.session
    if not s then return end
    if action=="rejected" then stop(args);return end
    if args.token~=s.token then return end
    s.lastMessage=getTimestampMs()
    if action=="begin" then
        detach(s.player)
        s.player:teleportTo(args.playerX,args.playerY,0)
        send("leased",{token=s.token})
    elseif action=="pin" then
        local map,main=pinAvailable(s.player)
        if map then
            s.sourcePin=map;s.mainMap=main
            local ok=pcall(function()map:copy(main)end)
            send("pinned",{token=s.token,ready=ok})
        else send("pinned",{token=s.token,ready=false}) end
    elseif action=="releasePin" then
        if s.sourcePin then s.sourcePin:Unload();s.sourcePin=nil end
    elseif action=="scout" then
        protectScout(s);detach(s.player)
        s.player:teleportTo(args.x,args.y,0);s.mainMap:ProcessChunkPos(s.player)
        s.scout=args;P.status="Loading destination; source protected by passenger..."
    elseif action=="probe" then
        local v=findVehicle(args);local ready=false
        if v then
            local shape=H.geometry(v);shape.vehicle=v
            ready=H.clear(shape,args.x,args.y)~=nil and H.ground(args.playerX,args.playerY)~=nil
        end
        send("probe",{token=s.token,sequence=args.sequence,ready=ready})
    elseif action=="move" then
        if s.sequence and args.sequence<=s.sequence then return end
        s.sequence=args.sequence;s.move=args;s.settle=0;s.moveStarted=getTimestampMs();s.remoteMirrorDone=false;s.scout=nil
        mirror(args)
        if args.remote then protectScout(s) end
        detach(s.player);s.player:teleportTo(args.playerX,args.playerY,0)
        if args.remote and s.mainMap then s.mainMap:ProcessChunkPos(s.player) end
        P.progress=math.max(0,math.min(0.99,args.progress or 0))
        P.status="Moving vehicle: "..math.floor(P.progress*100).."%"
    elseif action=="finish" then stop(args) end
end
Events.OnServerCommand.Add(function(module,action,args)
    local ok,why=pcall(command,module,action,args)
    if not ok then
        print("[MapTeleportVehicle/Client] "..tostring(why))
        if N.session then N.cancel() end
    end
end)
local tick=0
Events.OnTick.Add(function()
    local s=N.session
    if s then
        if s.token and getTimestampMs()-(s.lastMessage or s.requested)>45000 then
            stop({reason="Connection to the transfer server was lost; check the current vehicle position"});return
        end
        if not s.token and getTimestampMs()-s.requested>20000 then stop({reason="Server did not respond; nothing moved"});return end
        if s.scout then
            local a=s.scout;local loaded=true
            for dx=-8,8,8 do for dy=-8,8,8 do
                if not getCell():getGridSquare(math.floor(a.x+dx),math.floor(a.y+dy),0) then loaded=false end
            end end
            if loaded then send("scouted",{token=s.token});s.scout=nil end
        end
        if s.move then
            if s.move.remote and not s.remoteMirrorDone then
                local ok,applied=pcall(mirror,s.move)
                if ok and applied then s.remoteMirrorDone=true;s.settle=0 end
                if getTimestampMs()-s.moveStarted>30000 then
                    send("arrived",{token=s.token,sequence=s.move.sequence,ready=false});s.move=nil
                end
            end
            if s.move and (not s.move.remote or s.remoteMirrorDone) then
            s.settle=s.settle+1
            if s.settle>=8 then
                local a=s.move;local v=findVehicle(a)
                local ready=v and math.abs(v:getX()-a.x)<2 and math.abs(v:getY()-a.y)<2 and
                    math.abs(s.player:getX()-a.playerX)<2 and math.abs(s.player:getY()-a.playerY)<2 and
                    getCell():getGridSquare(math.floor(a.playerX),math.floor(a.playerY),0)~=nil
                send("arrived",{token=s.token,sequence=a.sequence,ready=ready==true})
                s.move=nil
            end
            end
        end
    end
    if N.cleanup then
        local c=N.cleanup;local a=c.args
        local v=findVehicle(a)
        if v and math.abs(v:getX()-a.x)<2 and math.abs(v:getY()-a.y)<2 and getCell():getGridSquare(math.floor(a.x),math.floor(a.y),0) then
            c.stable=c.stable+1
            if c.stable>=8 then c.map:Unload();N.cleanup=nil end
        else
            c.stable=0;pcall(mirror,a)
        end
    end
    tick=tick+1
    if tick%30==0 then
        for key,args in pairs(N.pending) do
            local ok,applied=pcall(mirror,args)
            if ok and applied then N.pending[key]=nil end
        end
    end
end)
Events.OnGameStart.Add(function()
    local actor=getSpecificPlayer(0)
    local guard=actor and actor:getModData().UMVNetworkGuard
    if guard then unfreeze(actor,guard) end
end)
return N
