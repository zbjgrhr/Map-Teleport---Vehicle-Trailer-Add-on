from pathlib import Path
p=Path('work/pure-lua-vehicle-test/42/media/lua/client/PLVT_Core.lua')
s=p.read_text(encoding='utf-8-sig')
a=s.index('local function followSeat(s)');b=s.index('\nlocal function persist(s)',a)
s=s[:a]+'''local function followSeat(s)
    for _,member in ipairs(s.occupants) do
        local actor=member.actor
        assert(actor:getVehicle()==s.vehicle,"An occupant left the vehicle; transfer stopped")
        assert(s.vehicle:getCharacter(member.seat)==actor,"An occupant changed seats; transfer stopped")
        local position=s.vehicle:getPassengerWorldPos(member.seat,Vector3f.new())
        assert(position,"Seat position unavailable")
        actor:setX(position:x());actor:setY(position:y());actor:setZ(0)
        actor:setLastX(position:x());actor:setLastY(position:y())
        local square=getCell():getGridSquare(math.floor(position:x()),math.floor(position:y()),0)
        assert(square,"An occupant seat is outside loaded ground")
        actor:setCurrent(square)
    end
end
''' +s[b:]
s=s.replace('    if s.player:getVehicle()~=s.vehicle then return end\n    local landing','    for _,member in ipairs(s.occupants) do\n    local actor=member.actor\n    if actor:getVehicle()==s.vehicle then\n    local landing')
s=s.replace('if s.vehicle:exit(s.player) then\n        s.player:teleportTo(landing[1],landing[2],0)\n        triggerEvent("OnExitVehicle",s.player)','if s.vehicle:exit(actor) then\n        actor:teleportTo(landing[1],landing[2],0)\n        triggerEvent("OnExitVehicle",actor)')
s=s.replace('\nend\n\nfunction P.stop', '\n    end\n    end\nend\n\nfunction P.stop',1)
s=s.replace('        pcall(function() s.player:setBlockMovement(s.wasBlocked) end)\n        s.player:getModData().PLVTGuard=nil','''        for _,member in ipairs(s.occupants) do
            pcall(function()
                member.actor:setBlockMovement(member.wasBlocked)
                member.actor:getModData().PLVTGuard=nil
            end)
        end''')
a=s.index('    for seat=0,vehicle:getMaxPassengers()-1 do',s.index('function P.start'));b=s.index('    if vehicle:getCurrentAbsoluteSpeedKmHour()',a)
s=s[:a]+s[b:]
s=s.replace('    s.wasBlocked=player:isBlockMovement()','''    s.wasBlocked=player:isBlockMovement()
    s.occupants={}
    for seat=0,vehicle:getMaxPassengers()-1 do
        local actor=vehicle:getCharacter(seat)
        if actor then
            if type(actor.isBlockMovement)~="function" or type(actor.setBlockMovement)~="function" then
                say(player,"Unsupported occupant type; nothing moved");return false
            end
            table.insert(s.occupants,{actor=actor,seat=seat,wasBlocked=actor:isBlockMovement()})
        end
    end
    s.visited={};s.lastSearch=0''')
s=s.replace('    player:getModData().PLVTGuard={wasBlocked=s.wasBlocked}\n    local prepared,why=pcall(function() player:setBlockMovement(true);vehicle:shutOff() end)','''    local prepared,why=pcall(function()
        for _,member in ipairs(s.occupants) do
            member.actor:getModData().PLVTGuard={wasBlocked=member.wasBlocked}
            member.actor:setBlockMovement(true)
        end
        vehicle:shutOff()
    end)''')
s=s.replace('    s.detourPath=detour(s)','''    -- Teleport steps need a clear landing, not a driveable connecting path.
    -- Search the wider loaded window to jump over narrow belts of trees.
    local wide,score
    for radius=32,64,8 do
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
    s.detourPath=detour(s)''')
s=s.replace('    s.hops=s.hops+1;s.stepX=x;', '''    local visitKey=math.floor(x/8)..","..math.floor(y/8)
    s.visited[visitKey]=(s.visited[visitKey] or 0)+1
    s.hops=s.hops+1;s.stepX=x;''')
s=s.replace('    local x,y,square,final=candidate(s)','''    local x,y,square,final=candidate(s)''')
s=s.replace('"Checking intermediate landing/loading... (Esc to stop)"','"Searching wider loaded area... (Esc to stop)"')
# The original local actor can change while NPC possession swaps player slot.
# Stop remains deliberate, but the whole occupant group is persisted and unlocked.
p.write_text(s,encoding='utf-8')
for rel in ['42/mod.info','42/media/lua/client/PLVT_Main.lua']:
 p=Path('work/pure-lua-vehicle-test')/rel
 t=p.read_text(encoding='utf-8-sig').replace('0.1.3','0.1.4').replace('First trial: one vehicle, no other passengers or trailers.','Single-player with seated passengers; disconnect trailers.').replace('unload/seat safeguards, detours and map marker','occupant transfer and wider loaded landing search')
 p.write_text(t,encoding='utf-8')
