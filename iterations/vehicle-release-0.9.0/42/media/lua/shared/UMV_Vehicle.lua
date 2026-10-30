-- Standalone SP vehicle travel through overlapping loaded areas.
-- Uses only vanilla Lua APIs. No Java bridge, ID changes, remove/add or cloning.
local Convoy=require "UMV_Convoy"
local P = {session=nil, status="", progress=0, tracked=nil, watchTicks=0}
local PREFIX = "[MapTeleportVehicle] "
local MAX_STEP, STREAM_TIMEOUT, TRIP_TIMEOUT = 512, 20000, 600000

local function finite(n) return type(n)=="number" and n==n and math.abs(n)<10000000 end
local function now() return getTimestampMs() end
local function distance(x,y,a,b) return math.sqrt((x-a)^2+(y-b)^2) end
local function log(s) print(PREFIX .. s) end
local function say(player,s) if player then player:Say("[UMT] " .. s) end end
local function registered(s)
    return not s.vehicle:isRemovedFromWorld() and
        s.vehicle:getId()==s.id and s.vehicle:getSqlId()==s.sqlId and
        getVehicleById(s.id)==s.vehicle and
        getCell():getVehicles():contains(s.vehicle)
end

local function ground(x,y)
    local square=getCell():getGridSquare(math.floor(x),math.floor(y),0)
    if not square or not square:getFloor() or not square:isFree(false) then return nil end
    local sprite=square:getFloor():getSprite()
    if not sprite or sprite:getProperties():has(IsoFlagType.water) then return nil end
    return square
end

local function clear(s,x,y)
    -- Require a complete surrounding area before touching the physical body.
    for dx=-8,8,8 do for dy=-8,8,8 do
        if not getCell():getGridSquare(math.floor(x+dx),math.floor(y+dy),0) then return nil end
    end end
    local r=s.bound
    for tx=math.floor(x)-r,math.floor(x)+r do
        for ty=math.floor(y)-r,math.floor(y)+r do
            local dx,dy=tx+0.5-x,ty+0.5-y
            if math.abs(dx*s.ux+dy*s.uy)<=s.halfX+0.71 and
                math.abs(dx*s.vx+dy*s.vy)<=s.halfZ+0.71 and not ground(tx,ty) then return nil end
        end
    end
    local iterator=getCell():getVehicles():iterator()
    while iterator:hasNext() do
        local other=iterator:next()
        if other~=s.vehicle and not (s.ignoreVehicles and s.ignoreVehicles[other]) then
            local extents=other:getScript() and other:getScript():getExtents()
            local radius=extents and math.sqrt(extents:x()^2+extents:z()^2)/2 or 5
            if distance(x,y,other:getX(),other:getY()) < s.radius+radius+0.75 then return nil end
        end
    end
    return ground(x,y)
end

local function geometry(vehicle)
    local ext=assert(vehicle:getScript():getExtents(),"Vehicle size is unavailable")
    local o=vehicle:getWorldPos(0,0,0,Vector3f.new())
    local a=vehicle:getWorldPos(1,0,0,Vector3f.new())
    local b=vehicle:getWorldPos(0,0,1,Vector3f.new())
    local ux,uy,vx,vy=a:x()-o:x(),a:y()-o:y(),b:x()-o:x(),b:y()-o:y()
    local u,v=math.sqrt(ux*ux+uy*uy),math.sqrt(vx*vx+vy*vy)
    assert(u>0.01 and v>0.01,"Vehicle orientation is unavailable")
    local hx,hz=ext:x()/2+0.35,ext:z()/2+0.35
    assert(hx>0 and hz>0 and hx<=10 and hz<=12,"Vehicle size exceeds the supported landing search")
    return {halfX=hx,halfZ=hz,ux=ux/u,uy=uy/u,vx=vx/v,vy=vy/v,
        radius=math.sqrt(hx*hx+hz*hz),bound=math.ceil(math.sqrt(hx*hx+hz*hz))+1}
end

local function place(s,x,y,square)
    assert(registered(s),"Vehicle is no longer registered; stopped without recreating it")
    assert(square and clear(s,x,y),"Step destination is no longer clear or loaded")
    local vehicle=s.vehicle
    local transform=Transform.new()
    vehicle:getWorldTransform(transform)
    local origin=transform:getOrigin()
    local physicalPosition=vehicle:getWorldPos(0,0,0,Vector3f.new())
    -- Physics axes are X/height/Y. Relative translation avoids accessing the
    -- unexposed WorldSimulation singleton or hard-coding its world offsets.
    origin:set(origin:x()+x-physicalPosition:x(),origin:y(),origin:z()+y-physicalPosition:y())
    -- Keep the Bullet body dynamic/active while submitting its teleport.
    -- Freezing it first can leave the native body at its previous transform;
    -- the next simulation read then overwrites the Java-side position.
    vehicle:setWorldTransform(transform)
    vehicle:checkSurroundingChunks()
    vehicle:setPhysicsActive(true,true)
    vehicle:setWorldTransform(transform)
    vehicle:setX(x);vehicle:setY(y);vehicle:setZ(0)
    vehicle:setCurrent(square)
    -- Commit the normal native chunk-list transition BEFORE moving the camera.
    -- Both old and new chunks are still in the player's loaded area here.
    vehicle:update()
    assert(registered(s),"Vehicle registration changed during the step")
    assert(distance(vehicle:getX(),vehicle:getY(),x,y)<1.5,"Physics rejected the vehicle step")
    assert(vehicle:getSquare() and vehicle:getSquare():getChunk()==square:getChunk(),
        "Vehicle has not joined the destination chunk")
    return transform
end

local singleRegistered,singleClear,singlePlace,singleGeometry=registered,clear,place,geometry
registered=function(s)return Convoy.registered(s,singleRegistered)end
clear=function(s,x,y)return Convoy.clear(s,x,y,singleClear)end
place=function(s,x,y,square)
    assert(registered(s),"A connected vehicle changed or unloaded")
    assert(clear(s,x,y),"No loaded landing for the complete towing chain")
    return Convoy.place(s,x,y,square,singlePlace)
end
geometry=function(vehicle)
    local shape=singleGeometry(vehicle);Convoy.attach(shape,vehicle,singleGeometry);return shape
end

local function followSeat(s)
    for _,member in ipairs(s.occupants) do
        local actor=member.actor
        local vehicle=member.vehicle or s.vehicle
        assert(actor:getVehicle()==vehicle,"An occupant left the vehicle; transfer stopped")
        assert(vehicle:getCharacter(member.seat)==actor,"An occupant changed seats; transfer stopped")
        local position=vehicle:getPassengerWorldPos(member.seat,Vector3f.new())
        assert(position,"Seat position unavailable")
        actor:setX(position:x());actor:setY(position:y());actor:setZ(0)
        actor:setLastX(position:x());actor:setLastY(position:y())
        local square=getCell():getGridSquare(math.floor(position:x()),math.floor(position:y()),0)
        assert(square,"An occupant seat is outside loaded ground")
        actor:setCurrent(square)
    end
end

local function persist(s)
    if not registered(s) or not s.vehicle:getController() then return end
    s.vehicle:update()
    local used={}
    for _,member in ipairs(s.occupants) do
    local actor=member.actor
    local vehicle=member.vehicle or s.vehicle
    if actor:getVehicle()==vehicle then
    local landing
    for r=math.ceil(s.radius)+1,math.ceil(s.radius)+10 do
        for dx=-r,r do for dy=-r,r do
            if not landing and math.max(math.abs(dx),math.abs(dy))==r then
                local x,y=math.floor(s.vehicle:getX())+dx+0.5,math.floor(s.vehicle:getY())+dy+0.5
                local square=ground(x,y)
                if square and not square:getVehicleContainer() and not used[x..","..y] and Convoy.outside(s,x,y,s.vehicle:getX(),s.vehicle:getY()) then landing={x,y} end
            end
        end end
        if landing then break end
    end
    if not landing then log("No clear player exit; keeping seat at current checkpoint");return end
    -- exit() saves the live vehicle, then clears the player's seat permanently.
    -- Re-entering here left NPC possession holding an unloaded vehicle object.
    if vehicle:exit(actor) then
        used[landing[1]..","..landing[2]]=true
        actor:teleportTo(landing[1],landing[2],0)
        triggerEvent("OnExitVehicle",actor)
        log("native save checkpoint: sqlId=" .. s.sqlId .. " player exited at=" .. landing[1] .. "," .. landing[2])
    end
    end
    end
    if s.convoy then Convoy.persist(s) end
end

function P.stop(message,success)
    if P.session and P.session.remote then return P.remoteCancel(message) end
    if P.session and P.session.network then return P.networkCancel(message) end
    local s=P.session
    P.session=nil
    P.status=message or "Cancelled at the current loaded checkpoint"
    if s then
        if registered(s) then
            local ok,why=pcall(persist,s)
            if not ok then log("checkpoint save failed: " .. tostring(why)) end
            for _,part in ipairs(Convoy.members(s)) do
                pcall(function() part.vehicle:checkSurroundingChunks();part.vehicle:setPhysicsActive(true,true) end)
            end
        end
        for _,member in ipairs(s.occupants) do
            if member.animals and P.animals then
                local ok,released,why=pcall(P.animals.release,member.actor,member.animals,
                    member.actor:getX(),member.actor:getY())
                if not ok or not released then
                    log("Animal restore: "..tostring(ok and why or released))
                    say(member.actor,"Led animal placement pending; check your inventory")
                end
            end
            pcall(function()
                member.actor:setBlockMovement(member.wasBlocked)
                member.actor:getModData().PLVTGuard=nil
            end)
        end
        say(s.player,P.status)
        log((success and "COMPLETE " or "STOP ") .. P.status ..
            " id=" .. s.id .. " sqlId=" .. s.sqlId .. " hops=" .. s.hops ..
            " vehicle=" .. s.vehicle:getX() .. "," .. s.vehicle:getY())
        P.tracked={vehicle=s.vehicle,actor=s.player,sqlId=s.sqlId,id=s.id,
            x=s.vehicle:getX(),y=s.vehicle:getY(),state="loaded"}
    end
    if P.onStopped then P.onStopped(success,s) end
end

local function detour(s)
    -- Local A* over loaded landing spots. Unlike the greedy direct steps, this
    -- can temporarily move sideways/backward to get around an obstruction.
    local sx,sy=s.vehicle:getX(),s.vehicle:getY()
    local initial=distance(sx,sy,s.targetX,s.targetY)
    local root={x=sx,y=sy,g=0,f=initial,key="0,0"}
    local open={root};local closed={};local bestCosts={[root.key]=0}
    for iteration=1,100 do
        if #open==0 then return nil end
        local best=1
        for i=2,#open do if open[i].f<open[best].f then best=i end end
        local node=table.remove(open,best)
        if not closed[node.key] then
            closed[node.key]=true
            if node.parent and distance(node.x,node.y,s.targetX,s.targetY)<initial-6 then
                local path={}
                while node.parent do
                    table.insert(path,1,{node.x,node.y})
                    node=node.parent
                end
                log("loaded detour found: " .. #path .. " short steps")
                return path
            end
            for dx=-1,1 do for dy=-1,1 do
                if dx~=0 or dy~=0 then
                    local x,y=node.x+dx*8,node.y+dy*8
                    local key=math.floor((x-sx)/8+0.5) .. "," .. math.floor((y-sy)/8+0.5)
                    local cost=node.g+math.sqrt(dx*dx+dy*dy)*8
                    if math.abs(x-sx)<=32 and math.abs(y-sy)<=32 and not closed[key] and
                        (not bestCosts[key] or cost<bestCosts[key]) and clear(s,x,y) then
                        bestCosts[key]=cost
                        table.insert(open,{x=x,y=y,parent=node,g=cost,
                            f=distance(x,y,s.targetX,s.targetY)+cost*0.5,key=key})
                    end
                end
            end end
        end
    end
end

local function candidate(s)
    local x,y=s.vehicle:getX(),s.vehicle:getY()
    local remaining=distance(x,y,s.targetX,s.targetY)
    local maxStep=s.maxStep or MAX_STEP
    if s.detourPath and #s.detourPath>0 then
        local step=table.remove(s.detourPath,1)
        local square=clear(s,step[1],step[2])
        if square then return step[1],step[2],square,false end
        s.detourPath=nil
    end
    if remaining<=maxStep+3 then
        -- Final landing searches around the clicked point; a click on a roof,
        -- water or a narrow road may need nearby open ground.
        for radius=0,12 do
            for dx=-radius,radius do for dy=-radius,radius do
                if math.max(math.abs(dx),math.abs(dy))==radius then
                    local cx,cy=math.floor(s.targetX)+dx+0.5,math.floor(s.targetY)+dy+0.5
                    if distance(x,y,cx,cy)<=maxStep+3 then
                        local square=clear(s,cx,cy)
                        if square then return cx,cy,square,true end
                    end
                end
            end end
        end
    end
    local dx,dy=(s.targetX-x)/remaining,(s.targetY-y)/remaining
    local best,bestScore
    for _,length in ipairs({512,384,256,192,160,128,112,96,80,64,56,48,40,32,24,18,12,8}) do
        for _,degrees in ipairs({0,22.5,-22.5,45,-45,67.5,-67.5,90,-90}) do
            local angle=degrees*math.pi/180
            local cx=x+length*(dx*math.cos(angle)-dy*math.sin(angle))
            local cy=y+length*(dx*math.sin(angle)+dy*math.cos(angle))
            cx,cy=math.floor(cx)+0.5,math.floor(cy)+0.5
            local nextDistance=distance(cx,cy,s.targetX,s.targetY)
            local progress=remaining-nextDistance
            if length<=maxStep and progress>1 and (not bestScore or progress>bestScore) then
                local square=clear(s,cx,cy)
                if square then best={cx,cy,square,false};bestScore=progress end
            end
        end
    end
    if best then return unpack(best) end
    -- Teleport steps need a clear landing, not a driveable connecting path.
    -- Search the wider loaded window to jump over narrow belts of trees.
    local wide,score
    for radius=32,maxStep,8 do
        for degrees=0,345,15 do
            local angle=degrees*math.pi/180
            local cx,cy=math.floor(x+radius*math.cos(angle))+0.5,math.floor(y+radius*math.sin(angle))+0.5
            local key=math.floor(cx/8)..","..math.floor(cy/8)
            local gain=remaining-distance(cx,cy,s.targetX,s.targetY)
            local rank=gain-(s.visited[key] or 0)*80
            if gain>2 and (not score or rank>score) then
                local square=clear(s,cx,cy)
                if square then wide={cx,cy,square,false};score=rank end
            end
        end
    end
    if wide then log("WIDE landing jump="..distance(x,y,wide[1],wide[2]));return unpack(wide) end
    s.detourPath=detour(s)
    if s.detourPath and #s.detourPath>0 then
        local step=table.remove(s.detourPath,1)
        return step[1],step[2],clear(s,step[1],step[2]),false
    end
end

function P.start(player,x,y)
    if P.session then say(player,"A transfer is already running") return false end
    if P.personBusy and P.personBusy() then say(player,"Wait for the person teleport to finish") return false end
    if isClient() then return P.networkStart(player,x,y) end
    if isServer() then return false end
    if type(umtspMoveVehicle)=="function" then
        say(player,"Another vehicle bridge is active; restart after updating the vehicle mod") return false
    end
    local vehicle=player and player:getVehicle()
    if not vehicle then say(player,"Sit in a vehicle first") return false end
    if not finite(x) or not finite(y) then return false end
    if vehicle:getCurrentAbsoluteSpeedKmHour()>1 then say(player,"Stop the vehicle first") return false end
    if player:getZ()~=0 or vehicle:getZ()~=0 then say(player,"Start on ground level") return false end
    local ok,s=pcall(geometry,vehicle)
    if not ok then say(player,tostring(s)) return false end
    s.player=player;s.vehicle=vehicle;s.seat=vehicle:getSeat(player)
    s.id=vehicle:getId();s.sqlId=vehicle:getSqlId();s.targetX=x;s.targetY=y
    s.startX=vehicle:getX();s.startY=vehicle:getY()
    s.total=distance(s.startX,s.startY,x,y);s.hops=0;s.phase="plan"
    s.started=now();s.lastProgress=now();s.nextTick=0;s.ticks=0
    s.wasBlocked=player:isBlockMovement()
    s.occupants={}
    for _,car in ipairs(Convoy.members(s)) do
    for seat=0,car.vehicle:getMaxPassengers()-1 do
        local actor=car.vehicle:getCharacter(seat)
        if actor then
            if type(actor.isBlockMovement)~="function" or type(actor.setBlockMovement)~="function" then
                say(player,"Unsupported occupant type; nothing moved");return false
            end
            table.insert(s.occupants,{actor=actor,vehicle=car.vehicle,seat=seat,wasBlocked=actor:isBlockMovement()})
        end
    end
    end
    if P.animals then
        for _,member in ipairs(s.occupants) do
            local records,why=P.animals.capture(member.actor)
            if not records then say(player,why);return false end
            member.animals=records
        end
    end
    s.visited={};s.lastSearch=0
    if not registered(s) then say(player,"Vehicle registration is unavailable") return false end
    P.session=s;P.progress=0;P.status="Preparing distant transfer..."
    local prepared,why=pcall(function()
        for _,member in ipairs(s.occupants) do
            member.actor:getModData().PLVTGuard={wasBlocked=member.wasBlocked}
            member.actor:setBlockMovement(true)
            if member.animals then
                local staged,why=P.animals.stage(member.actor,member.animals)
                assert(staged,why)
                if #member.animals>0 then log("Staged led animals="..#member.animals) end
            end
        end
        vehicle:shutOff()
    end)
    if not prepared then P.stop("Preparation failed: " .. tostring(why));return false end
    if P.remotePrepare then
        local ready,why=pcall(P.remotePrepare,s)
        if not ready then P.stop("Destination preparation failed: "..tostring(why));return false end
    end
    if P.onStarted then
        local shown,uiError=pcall(P.onStarted,player)
        if not shown then P.stop("Could not open progress display: " .. tostring(uiError));return false end
    end
    log("START no Java bridge; id=" .. s.id .. " sqlId=" .. s.sqlId ..
        " origin=" .. s.startX .. "," .. s.startY .. " target=" .. x .. "," .. y .. " occupants=" .. #s.occupants)
    return true
end

local function update()
    local s=P.session
    if not s or s.network or s.remote then return end
    if getSpecificPlayer(0)~=s.player then P.stop("Control changed; transfer stopped at the current checkpoint") return end
    assert(not s.player:isDead(),"Player died")
    assert(s.player:getVehicle()==s.vehicle,"Player left the vehicle")
    assert(registered(s),"Vehicle identity or world registration changed")
    s.ticks=s.ticks+1
    if now()-s.started>TRIP_TIMEOUT then P.stop("Transfer time limit reached; stopped at the last loaded checkpoint") return end
    if s.ticks<s.nextTick then return end
    if s.phase=="settle" then
        local errorDistance=distance(s.vehicle:getX(),s.vehicle:getY(),s.stepX,s.stepY)
        if errorDistance>=2 then
            local physical=s.vehicle:getWorldPos(0,0,0,Vector3f.new())
            log("DRIFT expected=" .. s.stepX .. "," .. s.stepY ..
                " entity=" .. s.vehicle:getX() .. "," .. s.vehicle:getY() ..
                " physicsMirror=" .. physical:x() .. "," .. physical:y() ..
                " player=" .. s.player:getX() .. "," .. s.player:getY() ..
                " active=" .. tostring(s.vehicle:isPhysicsActive()) ..
                " speed=" .. tostring(s.vehicle:getCurrentAbsoluteSpeedKmHour()) ..
                " error=" .. errorDistance)
            pcall(followSeat,s)
            P.stop("Vehicle did not stay at its checkpoint; stopped at its current position")
            return
        end
        followSeat(s)
        if s.final then P.progress=1;P.stop("Vehicle transfer completed",true);return end
        s.phase="plan";s.nextTick=s.ticks+1
        return
    end
    local x,y,square,final=candidate(s)
    if not x then
        P.status="Searching wider loaded area... (Esc to stop)"
        if not s.lastWaitLog or now()-s.lastWaitLog>3000 then
            s.lastWaitLog=now()
            log("WAIT intermediate=" .. s.vehicle:getX() .. "," .. s.vehicle:getY() ..
                " remaining=" .. distance(s.vehicle:getX(),s.vehicle:getY(),s.targetX,s.targetY))
        end
        if now()-s.lastProgress>STREAM_TIMEOUT then
            P.stop("No loaded open route ahead; stopped with the vehicle at the last checkpoint")
        else s.nextTick=s.ticks+15 end
        return
    end
    -- If a native call throws, try to undo only this short step while its
    -- origin is still loaded. Never jump the player back across unloaded areas.
    local oldX,oldY=s.vehicle:getX(),s.vehicle:getY()
    local oldSquare=getCell():getGridSquare(math.floor(oldX),math.floor(oldY),0)
    local moved,why=pcall(place,s,x,y,square)
    if not moved then
        if registered(s) and oldSquare then
            local restored,reason=pcall(place,s,oldX,oldY,oldSquare)
            log("step rollback=" .. tostring(restored) .. " " .. tostring(reason))
            if restored then pcall(followSeat,s) end
        end
        error(why)
    end
    followSeat(s)
    local visitKey=math.floor(x/8)..","..math.floor(y/8)
    s.visited[visitKey]=(s.visited[visitKey] or 0)+1
    s.lastJumpDistance=distance(oldX,oldY,x,y)
    s.hops=s.hops+1;s.stepX=x;s.stepY=y;s.final=final
    s.phase="settle";s.nextTick=s.ticks+8;s.lastProgress=now()
    P.progress=math.max(0,math.min(0.99,1-distance(x,y,s.targetX,s.targetY)/math.max(1,s.total)))
    P.status=string.format("Moving vehicle: %d%% / %d steps",math.floor(P.progress*100),s.hops)
    if s.hops==1 or s.hops%10==0 or final then
        log("STEP " .. s.hops .. " id=" .. s.id .. " sqlId=" .. s.sqlId .. " at=" .. x .. "," .. y .. " jumpDistance=" .. s.lastJumpDistance)
    end
end

local function watchVehicle()
    local tracked=P.tracked
    if not tracked or not getCell() then return end
    P.watchTicks=P.watchTicks+1
    if P.watchTicks%60~=0 then return end
    local found
    local iterator=getCell():getVehicles():iterator()
    while iterator:hasNext() do
        local member=iterator:next()
        if member:getSqlId()==tracked.sqlId and not member:isRemovedFromWorld() and member:getController() then
            found=member;break
        end
    end
    local state=found and "loaded" or "unloaded"
    if state~=tracked.state then
        log("TRACK sqlId=" .. tracked.sqlId .. " state=" .. state ..
            " lastLanding=" .. tracked.x .. "," .. tracked.y)
        tracked.state=state
    end
    if found then tracked.vehicle=found;tracked.id=found:getId() end
    if not found and tracked.actor and tracked.actor:getVehicle()==tracked.vehicle then
        -- Do not call exit()/isStopped() on an unloaded body. Both can touch
        -- invalid physics or save a recycled chunk pointer to the vehicle DB.
        local index=tracked.vehicle:getSeat(tracked.actor)
        if index>=0 then tracked.vehicle:clearPassenger(index) end
        tracked.actor:setVehicle(nil);tracked.actor:setCollidable(true)
        log("Detached a stale actor seat without saving an unloaded vehicle")
    end
end

function P.tick()
    local ok,why=pcall(update)
    if not ok then log("ERROR " .. tostring(why));P.stop("Transfer stopped: " .. tostring(why)) end
    local watched,watchError=pcall(watchVehicle)
    if not watched then log("TRACK diagnostic skipped: " .. tostring(watchError));P.tracked=nil end
end

function P.recover(player)
    local guard=player and player:getModData().PLVTGuard
    if guard then player:setBlockMovement(guard.wasBlocked==true);player:getModData().PLVTGuard=nil end
end

P.helpers={convoyMembers=Convoy.members,convoyPayload=Convoy.payload,outsideConvoy=Convoy.outside,persistConvoy=Convoy.persist,singleGeometry=singleGeometry,geometry=geometry,clear=clear,candidate=candidate,place=place,ground=ground,registered=registered}
return P
