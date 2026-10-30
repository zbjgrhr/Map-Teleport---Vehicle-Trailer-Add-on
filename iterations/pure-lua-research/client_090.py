from pathlib import Path
p=Path('work/vehicle-release-0.9.0/42/media/lua/client/UMV_NetworkClient.lua');s=p.read_text();a=s.index('local function mirror(args)');b=s.index('\nfunction N.start',a)
s=s[:a]+'''local function records(args)return args.vehicles or {args}end
local function resolved(args)
    local result,ignored={},{}
    for _,point in ipairs(records(args)) do
        local v=findVehicle(point)
        if not v or not v:getController() then return nil end
        table.insert(result,{vehicle=v,point=point});ignored[v]=true
    end
    return result,ignored
end
local function verified(args)
    local group=resolved(args);if not group then return false end
    for _,entry in ipairs(group) do
        local p,v=entry.point,entry.vehicle
        if math.abs(v:getX()-p.x)>=2 or math.abs(v:getY()-p.y)>=2 or
            not getCell():getGridSquare(math.floor(p.x),math.floor(p.y),0) then return false end
    end
    return true
end
local function mirror(args)
    local group=resolved(args);if not group then return false end
    for _,entry in ipairs(group) do
        local p=entry.point
        entry.square=getCell():getGridSquare(math.floor(p.x),math.floor(p.y),0)
        if not entry.square then return false end
    end
    -- Submit every connected body before returning to the next physics frame.
    -- Keep native towing constraints and persistent vehicle identities intact.
    for _,entry in ipairs(group) do
        local v,p=entry.vehicle,entry.point
        v:authorizationChanged(nil)
        local t=Transform.new();v:getWorldTransform(t)
        local origin=t:getOrigin();local world=v:getWorldPos(0,0,0,Vector3f.new())
        origin:set(origin:x()+p.x-world:x(),origin:y(),origin:z()+p.y-world:y())
        v:setWorldTransform(t);v:checkSurroundingChunks();v:setPhysicsActive(true,true);v:setWorldTransform(t)
        v:setX(p.x);v:setY(p.y);v:setZ(0);v:setCurrent(entry.square);v:update()
    end
    for _,entry in ipairs(group) do entry.vehicle:setPhysicsActive(false,false) end
    return verified(args)
end
'''+s[b:]
s=s.replace('    if driver then vehicle:authorizationServerOnSeat(driver,false) end','    if driver then vehicle:authorizationChanged(nil) end',1)
s=s.replace('actor:getVehicle():getId()~=args.vehicleId','not findVehicle(args)',1) # passenger may sit in a connected vehicle rather than the initiating one
s=s.replace('send("ready",{token=s.token,version="0.9.0",remoteCap=pinAvailable(s.player)~=nil})','send("ready",{token=s.token,version="0.9.0",vehiclesReady=resolved(args)~=nil,remoteCap=pinAvailable(s.player)~=nil})',1)
a=s.index('        local v=findVehicle(args);local ready=false',s.index('elseif action=="probe"'));b=s.index('        send("probe"',a)
s=s[:a]+'''        local group,ignored=resolved(args);local ready=group~=nil
        if group then
            for _,entry in ipairs(group) do
                local shape=H.singleGeometry(entry.vehicle);shape.vehicle=entry.vehicle;shape.ignoreVehicles=ignored
                if not H.clear(shape,entry.point.x,entry.point.y) then ready=false;break end
            end
            if not H.ground(args.playerX,args.playerY) then ready=false end
        end
'''+s[b:]
s=s.replace('local ready=v and math.abs(v:getX()-a.x)<2 and math.abs(v:getY()-a.y)<2 and','local ready=verified(a) and',1)
s=s.replace('if v and math.abs(v:getX()-a.x)<2 and math.abs(v:getY()-a.y)<2 and getCell():getGridSquare(math.floor(a.x),math.floor(a.y),0) then','if verified(a) then',1)
p.write_text(s,encoding='utf-8')
# Reject directed tow cycles before the engine's recursive physics activation sees them.
p=Path('work/vehicle-release-0.9.0/42/media/lua/shared/UMV_Convoy.lua');s=p.read_text();s=s.replace('    assert(#queue<=32,"Towing chain is too large")','''    assert(#queue<=32,"Towing chain is too large")
    for _,m in ipairs(members) do
        local path={};local v=m.vehicle
        while v do assert(not path[v],"Cyclic towing connection");path[v]=true;v=v:getVehicleTowing() end
    end''');p.write_text(s,encoding='utf-8')
