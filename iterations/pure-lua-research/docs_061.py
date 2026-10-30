from pathlib import Path
import shutil
root=Path.cwd();release=root/'work/vehicle-release-0.6.1';out=root/'outputs/MapTeleportVehicle-0.6.1';out.mkdir(exist_ok=True)
cn=(root/'outputs/MapTeleportVehicle-0.6.0/description-zh.txt').read_text(encoding='utf-8')
en=(root/'outputs/MapTeleportVehicle-0.6.0/description-en.txt').read_text(encoding='utf-8')
cn=cn.replace('人物传送支持单人及多人游戏；车辆传送目前支持单人存档，包括同车乘客和 NPC。','支持单人及多人游戏，可传送人物、动物、车辆及同车乘客。')
cn=cn.replace('车辆停放在目的地附近的空地。','车辆停放在身边的空地，地图显示车辆落点临时标记，不会在地图上留下多个标记。')
cn=cn.replace('远距离自动分段加载，可按 Esc 在当前停靠点结束。','远距离自动分段加载，可按 Esc 在当前停靠点结束。多人游戏由驾驶员发起，其他乘客一同传送。')
a=cn.index('【车辆临时标记】');b=cn.index('【适用范围】',a);cn=cn[:a]+cn[b:]
cn=cn.replace('当前版本传车前请断开拖车；联网传车和完整牵引车队暂未开放。','当前版本传车前请断开拖车，完整牵引车队暂未开放。')
cn=cn.replace('仅需订阅并启用本模组，无需基础模组、ZombieBuddy 或其他前置。','仅需订阅并启用本模组，无需基础模组、ZombieBuddy 或其他前置。多人服务器与客户端须安装相同版本。')
en=en.replace('Character teleport supports single-player and multiplayer. Vehicle teleport currently supports single-player saves, including seated passengers and NPCs.','Supports single-player and multiplayer teleport for characters, animals, vehicles and seated passengers.')
en=en.replace('the vehicle is placed on open ground near the destination.','the vehicle is placed on open ground right beside them. A temporary map marker shows the vehicle’s landing position without leaving multiple markers on the map.')
en=en.replace('Press Esc to end at the current checkpoint.','Press Esc to end at the current checkpoint. In multiplayer, the driver initiates the transfer and the other passengers travel together.')
a=en.index('TEMPORARY VEHICLE MARKER');b=en.index('SUPPORTED SCOPE',a);en=en[:a]+en[b:]
en=en.replace('Network vehicle teleport and complete towing chains are not yet available.','Complete towing chains are not yet available.')
en=en.replace('No base mod, ZombieBuddy or other prerequisites are required.','No base mod, ZombieBuddy or other prerequisites are required. Multiplayer servers and clients must use the same mod version.')
for name,body in [('description-zh.txt',cn),('description-en.txt',en)]: (out/name).write_text(body,encoding='utf-8')
(release/'README.md').write_text(en+'\n---\n\n'+cn,encoding='utf-8')
p=release/'42/mod.info';s=p.read_text(encoding='utf-8');s=s[:s.index('description=')]+'''description=Standalone B42.21 world-map character, animal and vehicle teleport for single-player and multiplayer. Includes seated passengers, long-distance streaming and a temporary vehicle marker. No base mod or ZombieBuddy required. Disconnect trailers before vehicle teleport. Multiplayer servers and clients must use the same version.
''';p.write_text(s,encoding='utf-8')
old=(root/'outputs/MapTeleportVehicle-0.6.0/workshop.txt').read_text(encoding='utf-8').splitlines()
meta=[line for line in old if not line.startswith(('description=','tags='))]
meta+=['description='+line for line in (en+'\n'+cn).splitlines()];meta+=['tags=Build 42;Animals;Map;Multiplayer;Vehicles']
(out/'workshop.txt').write_text('\n'.join(meta)+'\n',encoding='utf-8')
(out/'upload-notes.txt').write_text('0.6.1 已实现多人传车流程，并通过一服务器两客户端独立模拟；尚未进行真实双人联机验证。请先验证近距离、远距离、乘客取消、车辆开走及离开区域后返回，再上传。\n多人须服务器和所有客户端安装0.6.1，由驾驶员发起。单人仍使用96格自适应步长；多人使用24格上限并逐段确认。\n更新后请从Steam必需物品中移除基础模组与ZombieBuddy。\n',encoding='utf-8')
print('Updated descriptions: multiplayer, vehicle beside characters, temporary marker merged into vehicle section')
