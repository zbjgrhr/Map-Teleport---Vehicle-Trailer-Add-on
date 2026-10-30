from pathlib import Path
p=Path('work/pure-lua-vehicle-test/README.md');s=p.read_text(encoding='utf-8-sig').replace('Vehicle Test 0.1.4','Vehicle Test 0.1.5');s+='''
## 0.1.5

- 传车流程复用正式版牵绳动物模块，出发前暂存每位乘客的牵绳动物，到达或取消后放出并恢复牵引。附近无落点时保留在背包并提示。
- 允许带着牵绳动物离座使用人物传送。
- 自适应尝试 64/56/48/40/32 格落点，不可用时缩短；保留 8 帧位置确认，确认后的等待由 4 帧缩至 1 帧。
- 相同加载窗口的约 3,600 格离线模拟：150 步/1797 帧降至 75 步/675 帧。这不是游戏内测速，真实速度取决于地形和加载。
- 实际动物 Lua 模块与车辆流程联合模拟通过：暂存、生成新实体、恢复牵引、取消恢复。仍需游戏内验证。
''';p.write_text(s,encoding='utf-8')
p=Path('work/pure-lua-research/test_standalone_menu.py');s=p.read_text();s=s.replace("assert(counts.stage==2 and counts.release==2 and counts.vehicle==1)","""assert(counts.stage==2 and counts.release==2 and counts.vehicle==1)
p.vehicle={getX=function()return 10 end,getY=function()return 10 end}
person.fn(person.target,table.unpack(person.args))
assert(counts.exit==2 and counts.stage==3 and counts.release==3 and p.vehicle==nil)
assert(Pure.animals==A)""");p.write_text(s,encoding='utf-8')
