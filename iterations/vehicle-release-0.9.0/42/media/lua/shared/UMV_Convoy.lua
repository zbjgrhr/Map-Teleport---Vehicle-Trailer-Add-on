-- Translate native towing partners together without detaching or rebuilding them.
-- Every transform is submitted in the same Lua call, before the next physics step.
local C={}
function C.attach(s,root,geometry)
    s.vehicle=root;s.id=root:getId();s.sqlId=root:getSqlId()
    local queue={root};local seen={[root]=true};local members={}
    for index=1,32 do
        local vehicle=queue[index];if not vehicle then break end
        local m=geometry(vehicle);m.vehicle=vehicle;m.id=vehicle:getId();m.sqlId=vehicle:getSqlId()
        m.dx=vehicle:getX()-root:getX();m.dy=vehicle:getY()-root:getY()
        m.towing=vehicle:getVehicleTowing();m.towedBy=vehicle:getVehicleTowedBy()
        table.insert(members,m)
        for _,nextVehicle in pairs({m.towing,m.towedBy}) do
            if nextVehicle and not seen[nextVehicle] then seen[nextVehicle]=true;table.insert(queue,nextVehicle) end
        end
    end
    assert(#queue<=32,"Towing chain is too large")
    for _,m in ipairs(members) do
        local path={};local v=m.vehicle
        while v do assert(not path[v],"Cyclic towing connection");path[v]=true;v=v:getVehicleTowing() end
    end
    if #members>1 then
        s.convoy={members=members,vehicles=seen}
        for _,m in ipairs(members) do
            assert(m.vehicle:getCurrentAbsoluteSpeedKmHour()<=1,"Stop every vehicle in the towing chain")
            assert(m.vehicle:getZ()==0,"Every vehicle must start on ground level")
            m.ignoreVehicles=seen
        end
    end
end
function C.members(s)
    return s.convoy and s.convoy.members or {{vehicle=s.vehicle,dx=0,dy=0,id=s.id,sqlId=s.sqlId}}
end
function C.registered(s,single)
    if not s.convoy then return single(s) end
    for _,m in ipairs(s.convoy.members) do
        if not single(m) or m.vehicle:getVehicleTowing()~=m.towing or m.vehicle:getVehicleTowedBy()~=m.towedBy then return false end
    end
    return true
end
function C.clear(s,x,y,single)
    if not s.convoy then return single(s,x,y) end
    for _,m in ipairs(s.convoy.members) do if not single(m,x+m.dx,y+m.dy) then return nil end end
    return getCell():getGridSquare(math.floor(x),math.floor(y),0)
end
function C.place(s,x,y,square,single)
    if not s.convoy then return single(s,x,y,square) end
    local old={}
    for i,m in ipairs(s.convoy.members) do old[i]={m.vehicle:getX(),m.vehicle:getY()} end
    local ok,why=pcall(function()
        for _,m in ipairs(s.convoy.members) do
            local tx,ty=x+m.dx,y+m.dy
            single(m,tx,ty,getCell():getGridSquare(math.floor(tx),math.floor(ty),0))
        end
    end)
    if not ok then
        -- A far source is protected by native pins but is not in the active
        -- lookup map; its caller reloads the source before a complete rollback.
        for i,m in ipairs(s.convoy.members) do
            local point=old[i];local tile=getCell():getGridSquare(math.floor(point[1]),math.floor(point[2]),0)
            if tile then pcall(single,m,point[1],point[2],tile) end
        end
        error(why)
    end
end
function C.outside(s,px,py,x,y)
    if not s.convoy then return true end
    for _,m in ipairs(s.convoy.members) do
        local dx,dy=px-x-m.dx,py-y-m.dy
        if math.abs(dx*m.ux+dy*m.uy)<=m.halfX+0.71 and math.abs(dx*m.vx+dy*m.vy)<=m.halfZ+0.71 then return false end
    end
    return true
end
function C.payload(s,x,y)
    if not s.convoy then return nil end
    local result={}
    for _,m in ipairs(s.convoy.members) do
        table.insert(result,{vehicleId=m.vehicle:getId(),sqlId=m.sqlId,x=x+m.dx,y=y+m.dy})
    end
    return result
end
function C.persist(s)
    for _,m in ipairs(C.members(s)) do
        if not m.vehicle:isRemovedFromWorld() and m.vehicle:getController() then
            m.vehicle:update();m.vehicle:exit(nil)
        end
    end
end
return C
