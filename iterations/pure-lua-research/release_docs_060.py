from pathlib import Path
import json
root=Path.cwd();dest=root/'work/vehicle-release-0.6.0';out=root/'outputs/MapTeleportVehicle-0.6.0';out.mkdir(parents=True,exist_ok=True)
cn='''# Map Teleport – Vehicle & Trailer Add-on

【地图右键传送】
面向 B42.21，在世界地图右键菜单加入独立的传送选项。人物传送支持单人及多人游戏；车辆传送目前支持单人存档，包括同车乘客和 NPC。

【模组菜单共存】
其他地图、导航/GPS、路线、目的地、标记、传送及作弊菜单等选项可以同时显示、分别选择。

【人物与动物】
选择 Teleport Here，传送自己、随身携带及绳索牵引的动物，到达后恢复牵引。坐车时也能使用，车辆和其他乘客留在原地。

【车辆传送】
坐在停稳的车内选择 Teleport Vehicle Here，传送当前车辆、自己及同车乘客，携带和牵引的动物随行。到达后人物与乘客下车，车辆停放在目的地附近的空地。
远距离自动分段加载，可按 Esc 在当前停靠点结束。

【车辆临时标记】
传车后，地图显示车辆落点的方向盘标记；下次传车时刷新，不会留下多个标记，也不随车辆移动。

【适用范围】
使用游戏原生车辆机制的原版及模组车辆。当前版本传车前请断开拖车；联网传车和完整牵引车队暂未开放。

【备用键盘快捷键】
在 Options → Key Bindings → Universal Map Teleport 中绑定 UMTSP: Teleport Here (World Map)，默认未绑定。打开地图，鼠标指向目的地后按键；坐车时可选择传人或传车。

【独立使用】
仅需订阅并启用本模组，无需基础模组、ZombieBuddy 或其他前置。
'''
en='''# Map Teleport – Vehicle & Trailer Add-on

WORLD-MAP TELEPORT
Adds independent teleport options to the B42.21 world-map right-click menu. Character teleport supports single-player and multiplayer. Vehicle teleport currently supports single-player saves, including seated passengers and NPCs.

MOD MENU COEXISTENCE
Map, navigation/GPS, route, destination, marker, teleport and cheat-menu options from other mods can appear together and remain separately selectable.

CHARACTERS & ANIMALS
Select Teleport Here to teleport yourself, carried animals and rope-led animals. Led animals are reattached on arrival. You can also use it while seated; the vehicle and other passengers stay behind.

VEHICLE TELEPORT
While seated in a stationary vehicle, select Teleport Vehicle Here to move the vehicle, yourself and its passengers, together with carried and rope-led animals. Characters exit on arrival, and the vehicle is placed on open ground near the destination.
Long-distance travel automatically loads successive areas. Press Esc to end at the current checkpoint.

TEMPORARY VEHICLE MARKER
A steering-wheel marker shows the vehicle's landing position. The next vehicle teleport replaces it, so markers do not accumulate. It does not follow the vehicle.

SUPPORTED SCOPE
For vanilla and modded vehicles using the game's native vehicle system. Disconnect trailers before vehicle teleport in this version. Network vehicle teleport and complete towing chains are not yet available.

BACKUP KEYBOARD SHORTCUT
Bind UMTSP: Teleport Here (World Map) under Options → Key Bindings → Universal Map Teleport. Open the map, point at your destination and press the key. While seated, choose character or vehicle teleport. Unbound by default.

STANDALONE
Subscribe to and enable this mod only. No base mod, ZombieBuddy or other prerequisites are required.
'''
reply="I've updated the vehicle mod to work as a standalone mod. Vehicle teleport no longer requires ZombieBuddy, the base mod, or any other external dependency. Once the update is live, just update and enable the vehicle mod, then restart the game. Please note that vehicle teleport currently supports single-player saves, including seated NPC passengers."
for name,content in [('description-zh.txt',cn),('description-en.txt',en),('comment-reply-en.txt',reply)]: (out/name).write_text(content,encoding='utf-8')
(dest/'README.md').write_text(cn+'\n---\n\n'+en,encoding='utf-8')
workshop=Path(json.loads((root/'work/vehicle-release-paths.json').read_text(encoding='utf-8'))['workshop'])
old=(workshop/'workshop.txt').read_text(encoding='utf-8-sig').splitlines()
meta=[l for l in old if not l.startswith(('description=','tags='))]
meta+=[ 'description='+line for line in (en+'\n'+cn).splitlines() ]
meta+=['tags=Build 42;Animals;Map;Vehicles']
(out/'workshop.txt').write_text('\n'.join(meta)+'\n',encoding='utf-8')
(out/'upload-notes.txt').write_text('0.6.0: 独立 Lua 车辆版，最多尝试 96 格自适应步长；沿用 Workshop ID 3822887136、原名称和原配图。\n上传后在 Steam 必需物品中删除 Map Teleport – Right-Click Rescue 与 ZombieBuddy。\n本机验证仅启用正式车辆版 UMTSPVehicleBridge，关闭旧 Pure Lua Vehicle Test。\n联网传车及牵引车队尚未实现，已在中英文说明中注明。\n',encoding='utf-8')
print('Prepared bilingual descriptions and workshop metadata')
