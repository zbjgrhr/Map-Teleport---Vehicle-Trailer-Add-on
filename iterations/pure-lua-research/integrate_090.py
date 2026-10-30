from pathlib import Path
root=Path('work/vehicle-release-0.9.0/42/media/lua')
p=root/'shared/UMV_Vehicle.lua';s=p.read_text();s=s.replace('local P = {','local Convoy=require "UMV_Convoy"\nlocal P = {',1)
s=s.replace('if other~=s.vehicle then','if other~=s.vehicle and not (s.ignoreVehicles and s.ignoreVehicles[other]) then',1)
# Prime at a distant loaded target before re-enabling physics, for every member.
s=s.replace('    vehicle:checkSurroundingChunks()\n    vehicle:setPhysicsActive(true,true)','    vehicle:setWorldTransform(transform)\n    vehicle:checkSurroundingChunks()\n    vehicle:setPhysicsActive(true,true)',1)
a=s.index('local function followSeat(s)')
s=s[:a]+'''local singleRegistered,singleClear,singlePlace,singleGeometry=registered,clear,place,geometry
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

'''+s[a:]
s=s.replace('assert(actor:getVehicle()==s.vehicle,','local vehicle=member.vehicle or s.vehicle\n        assert(actor:getVehicle()==vehicle,',1)
s=s.replace('assert(s.vehicle:getCharacter(member.seat)==actor,','assert(vehicle:getCharacter(member.seat)==actor,',1)
s=s.replace('local position=s.vehicle:getPassengerWorldPos(member.seat,','local position=vehicle:getPassengerWorldPos(member.seat,',1)
s=s.replace('    if actor:getVehicle()==s.vehicle then','    local vehicle=member.vehicle or s.vehicle\n    if actor:getVehicle()==vehicle then',1)
s=s.replace('not used[x..","..y] then landing','not used[x..","..y] and Convoy.outside(s,x,y,s.vehicle:getX(),s.vehicle:getY()) then landing',1)
s=s.replace('    if s.vehicle:exit(actor) then','    if vehicle:exit(actor) then',1)
s=s.replace('    end\n    end\nend\n\nfunction P.stop','    end\n    end\n    if s.convoy then Convoy.persist(s) end\nend\n\nfunction P.stop',1)
a=s.index('    if vehicle:getVehicleTowing() or vehicle:getVehicleTowedBy() then',s.index('function P.start'));b=s.index('    if vehicle:getCurrentAbsoluteSpeed',a);s=s[:a]+s[b:]
s=s.replace('    for seat=0,vehicle:getMaxPassengers()-1 do\n        local actor=vehicle:getCharacter(seat)','    for _,car in ipairs(Convoy.members(s)) do\n    for seat=0,car.vehicle:getMaxPassengers()-1 do\n        local actor=car.vehicle:getCharacter(seat)',1)
s=s.replace('table.insert(s.occupants,{actor=actor,seat=seat,wasBlocked=actor:isBlockMovement()})','table.insert(s.occupants,{actor=actor,vehicle=car.vehicle,seat=seat,wasBlocked=actor:isBlockMovement()})',1)
s=s.replace('    end\n    if P.animals then\n        for _,member','    end\n    end\n    if P.animals then\n        for _,member',1)
s=s.replace('P.helpers={geometry=geometry,','P.helpers={convoyMembers=Convoy.members,convoyPayload=Convoy.payload,outsideConvoy=Convoy.outside,persistConvoy=Convoy.persist,singleGeometry=singleGeometry,geometry=geometry,')
p.write_text(s,encoding='utf-8')
p=root/'client/UMV_RemoteSP.lua';s=p.read_text();s=s.replace('s.vehicle:update();s.vehicle:exit(nil)','H.persistConvoy(s)')
s=s.replace('if square and not square:getVehicleContainer() then chosen=','if square and not square:getVehicleContainer() and H.outsideConvoy(s,ax,ay,x,y) then chosen=',1)
s=s.replace('assert(s.vehicle:exit(m.actor),','assert((m.vehicle or s.vehicle):exit(m.actor),',1)
p.write_text(s,encoding='utf-8')
p=root/'server/UMV_NetworkServer.lua';s=p.read_text()
s=s.replace('s.vehicle:update();s.vehicle:exit(nil)','H.persistConvoy(s)',1)
s=s.replace('if square and not square:getVehicleContainer() then chosen=','if square and not square:getVehicleContainer() and H.outsideConvoy(s,ax,ay,x,y) then chosen=',1)
s=s.replace('m.actor:getVehicle()==s.vehicle and s.vehicle:getCharacter(m.seat)==m.actor','m.actor:getVehicle()==m.vehicle and m.vehicle:getCharacter(m.seat)==m.actor',1)
s=s.replace('    s.vehicle:authorizationServerOnSeat(s.driver,false)','    for _,car in ipairs(H.convoyMembers(s)) do car.vehicle:authorizationChanged(nil) end',1)
s=s.replace('assert(s.vehicle:exit(m.actor),','assert(m.vehicle:exit(m.actor),',1)
s=s.replace('    assert(not vehicle:getVehicleTowing() and not vehicle:getVehicleTowedBy(),"Disconnect trailers before teleporting")\n','')
s=s.replace('    for seat=0,vehicle:getMaxPassengers()-1 do\n        local occupant=vehicle:getCharacter(seat)','    for _,car in ipairs(H.convoyMembers(s)) do\n    for seat=0,car.vehicle:getMaxPassengers()-1 do\n        local occupant=car.vehicle:getCharacter(seat)',1)
s=s.replace('table.insert(s.occupants,{actor=occupant,seat=seat,animals=animals,wasBlocked=occupant:isBlockMovement()})','table.insert(s.occupants,{actor=occupant,vehicle=car.vehicle,seat=seat,animals=animals,wasBlocked=occupant:isBlockMovement()})',1)
s=s.replace('    end\n    active=s\n','    end\n    end\n    active=s\n',1)
# Include the entire convoy in every coordinate-bearing server message.
s=s.replace('vehicleId=s.id,sqlId=s.sqlId,','vehicleId=s.id,sqlId=s.sqlId,vehicles=H.convoyPayload(s,s.vehicle:getX(),s.vehicle:getY()),')
# Planned target messages must carry the target positions, not the current ones.
s=s.replace('vehicles=H.convoyPayload(s,s.vehicle:getX(),s.vehicle:getY()),x=s.stepX','vehicles=H.convoyPayload(s,s.stepX,s.stepY),x=s.stepX')
s=s.replace('vehicles=H.convoyPayload(s,s.vehicle:getX(),s.vehicle:getY()),\n                x=s.stepX','vehicles=H.convoyPayload(s,s.stepX,s.stepY),\n                x=s.stepX')
s=s.replace('vehicles=H.convoyPayload(s,s.vehicle:getX(),s.vehicle:getY()),\n            x=x','vehicles=H.convoyPayload(s,x,y),\n            x=x')
s=s.replace('vehicles=H.convoyPayload(s,s.vehicle:getX(),s.vehicle:getY()),\n                x=x','vehicles=H.convoyPayload(s,x,y),\n                x=x')
s=s.replace('        m.ready=true;m.remoteCap=args.remoteCap==true;return','''        if args.vehiclesReady==false then finish("A connected vehicle is not loaded on a client; nothing moved",false);return end
        m.ready=true;m.remoteCap=args.remoteCap==true;return''',1)
p.write_text(s,encoding='utf-8')
