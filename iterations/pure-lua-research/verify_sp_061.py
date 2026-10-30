from pathlib import Path
p=Path('work/vehicle-release-0.6.1/42/media/lua/server/UMV_NetworkServer.lua');s=p.read_text();s=s.replace('    local exits=assert(exitSquares(s,s.vehicle:getX(),s.vehicle:getY()),"No room to leave the vehicle")','''    assert(s.vehicle:getCurrentAbsoluteSpeedKmHour()<=1 and
        math.abs(s.vehicle:getX()-s.startX)<2 and math.abs(s.vehicle:getY()-s.startY)<2,
        "Vehicle moved while passengers were preparing")
    local exits=assert(exitSquares(s,s.vehicle:getX(),s.vehicle:getY()),"No room to leave the vehicle")''');p.write_text(s,encoding='utf-8')
# Run the proven SP lifecycle and menu checks against the actual 0.6.1 paths.
s=Path('work/pure-lua-research/verify_release_060.py').read_text(encoding='utf-8-sig')
s=s.replace("work/vehicle-release-0.6.0/42/media/lua","work/vehicle-release-0.6.1/42/media/lua")
s=s.replace("client/UMV_Vehicle.lua","shared/UMV_Vehicle.lua")
# Prior menu test's byte-for-byte comparison has already been omitted by this runner.
exec(compile(s,'SP-release-061-regression','exec'))
