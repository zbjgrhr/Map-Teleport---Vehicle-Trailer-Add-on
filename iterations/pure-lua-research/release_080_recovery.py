from pathlib import Path
p=Path('work/vehicle-candidate-0.8.0/42/media/lua/server/UMV_NetworkServer.lua');s=p.read_text();s=s.replace('    -- Revoke driving authority before exiting or moving the vehicle.','    s.originExits=exits\n    -- Revoke driving authority before exiting or moving the vehicle.',1);s=s.replace('    local positions=exitSquares(s,s.startX,s.startY)','    local positions=exitSquares(s,s.startX,s.startY) or s.originExits',1);p.write_text(s,encoding='utf-8')
p=Path('work/vehicle-candidate-0.8.0/42/media/lua/client/UMV_NetworkClient.lua');s=p.read_text();s=s.replace('    if v and not v:isRemovedFromWorld() and v:getSqlId()==args.sqlId then return v end','''    if v and not v:isRemovedFromWorld() and v:getSqlId()==args.sqlId then return v end
    -- A normally unloaded/reloaded server vehicle may receive a new runtime ID.
    -- Match its persistent SQL identity without recreating or re-registering it.
    local iterator=getCell():getVehicles():iterator()
    while iterator:hasNext() do
        local member=iterator:next()
        if not member:isRemovedFromWorld() and member:getSqlId()==args.sqlId then return member end
    end''',1);p.write_text(s,encoding='utf-8')
