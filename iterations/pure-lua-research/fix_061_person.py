from pathlib import Path
p=Path('work/vehicle-release-0.6.1/42/media/lua/server/UMV_Server.lua');s=p.read_text()
a=s.index('        if vehicle and #animals > 0 then');b=s.index('        if mode == "vehicle" then',a)
s=s[:a]+'''        if mode=="vehicle" then
            reply(player,"rejected",{id=id,reason="Use the vehicle transfer command."});return
        end
'''+s[b:]
# The old vehicle branch is unreachable; remove it rather than retaining Java-only calls.
a=s.index('        if mode == "vehicle" then',a);b=s.index('        local originX, originY, originZ',a);s=s[:a]+s[b:]
a=s.index('        if vehicle then\n            local exited, success = pcall');b=s.index('        local prepared, prepareError',a)
s=s[:a]+'''        if vehicle then
            local exited,success=pcall(function() return vehicle:exit(player) end)
            if not exited or not success then
                sessions[player]=nil
                reply(player,"rejected",{id=id,reason="Could not leave the original seat."});return
            end
            triggerEvent("OnExitVehicle",player)
        end
'''+s[b:]
p.write_text(s,encoding='utf-8')
