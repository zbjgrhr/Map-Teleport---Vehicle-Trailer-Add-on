from pathlib import Path
p=Path('work/pure-lua-vehicle-test/42/media/lua/client/PLVT_Core.lua')
s=p.read_text()
s=s.replace('    for _,member in ipairs(s.occupants) do\n    local actor=member.actor','    local used={}\n    for _,member in ipairs(s.occupants) do\n    local actor=member.actor',1)
s=s.replace('if square and not square:getVehicleContainer() then landing={x,y} end','if square and not square:getVehicleContainer() and not used[x..","..y] then landing={x,y} end')
s=s.replace('    if s.vehicle:exit(actor) then\n        actor:teleportTo','    if s.vehicle:exit(actor) then\n        used[landing[1]..","..landing[2]]=true\n        actor:teleportTo')
s=s.replace('" target=" .. x .. "," .. y)','" target=" .. x .. "," .. y .. " occupants=" .. #s.occupants)')
p.write_text(s,encoding='utf-8')
