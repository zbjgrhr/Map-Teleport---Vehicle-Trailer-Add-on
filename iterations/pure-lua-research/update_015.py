from pathlib import Path
root=Path('work/pure-lua-vehicle-test')
p=root/'42/media/lua/client/PLVT_Core.lua';s=p.read_text()
s=s.replace('= 24, 20000, 600000','= 64, 20000, 600000')
s=s.replace('ipairs({24,18,12,8})','ipairs({64,56,48,40,32,24,18,12,8})')
s=s.replace('s.phase="plan";s.nextTick=s.ticks+4','s.phase="plan";s.nextTick=s.ticks+1')
s=s.replace('        for _,member in ipairs(s.occupants) do\n            pcall(function()','''        for _,member in ipairs(s.occupants) do
            if member.animals and P.animals then
                local ok,released,why=pcall(P.animals.release,member.actor,member.animals,
                    member.actor:getX(),member.actor:getY())
                if not ok or not released then
                    log("Animal restore: "..tostring(ok and why or released))
                    say(member.actor,"Led animal placement pending; check your inventory")
                end
            end
            pcall(function()''',1)
s=s.replace('    s.visited={};s.lastSearch=0','''    if P.animals then
        for _,member in ipairs(s.occupants) do
            local records,why=P.animals.capture(member.actor)
            if not records then say(player,why);return false end
            member.animals=records
        end
    end
    s.visited={};s.lastSearch=0''')
s=s.replace('            member.actor:setBlockMovement(true)\n','''            member.actor:setBlockMovement(true)
            if member.animals then
                local staged,why=P.animals.stage(member.actor,member.animals)
                assert(staged,why)
                if #member.animals>0 then log("Staged led animals="..#member.animals) end
            end
''')
p.write_text(s,encoding='utf-8')
p=root/'42/media/lua/client/UMTSP_Main.lua';s=p.read_text(encoding='utf-8-sig').replace('PureVehicle.personBusy =','PureVehicle.animals = Animals\nPureVehicle.personBusy =',1)
s=s.replace('    if vehicle and #animals > 0 then\n        tell("Leave the vehicle before teleporting led animals.", player)\n        return\n    end\n','')
p.write_text(s,encoding='utf-8')
for rel in ['42/mod.info','42/media/lua/client/PLVT_Main.lua']:
 p=root/rel;s=p.read_text().replace('0.1.4','0.1.5').replace('occupant transfer and wider loaded landing search','led animals and adaptive longer steps');p.write_text(s,encoding='utf-8')
p=root/'README.md';s=p.read_text().replace('Vehicle Test 0.1.4','Vehicle Test 0.1.5');s+='''
## 0.1.5

- 车辆流程接入原版已验证的牵绳动物暂存/释放模块：每位乘客的牵绳动物在出发前暂存，到达或取消后释放并恢复牵引。没有释放空间时保留在背包并提示。
- 人物传送允许带着牵绳动物离座传送；沿用原生离座、动物暂存和到达恢复。
- 优先尝试 64/56/48/40/32 格落点，周围未加载或有障碍时自动缩短到原步长；保留 8 帧车辆位置确认，将确认后的额外等待从 4 帧缩短到 1 帧。
- 无法保证固定倍数提速；实际步长由加载窗口和地形决定。需要游戏内复测牵引恢复及远距离车辆重载。
''';p.write_text(s,encoding='utf-8')
