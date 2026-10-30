from pathlib import Path
import shutil,hashlib,json
root=Path.cwd();release=root/'work/vehicle-release-0.9.0';out=root/'outputs/MapTeleportVehicle-0.9.0';out.mkdir(exist_ok=True)
en='''# Map Teleport – Vehicle & Trailer Add-on

WORLD-MAP TELEPORT
Adds independent teleport options to the B42.21 world-map right-click menu. Supports single-player and multiplayer.

MOD MENU COEXISTENCE
Map, navigation/GPS, route, destination, marker, teleport and cheat-menu options from other mods can appear together and remain separately selectable.

CHARACTERS & ANIMALS
Select Teleport Here to teleport yourself, carried animals and rope-led animals. Led animals are reattached on arrival. This option is also available while seated. After teleporting, the vehicle and other passengers remain at the original location.

VEHICLES & TRAILERS
Once the convoy is stationary, select Teleport Vehicle Here from inside the vehicle to teleport yourself, passengers, the current vehicle and its connected towing chain, including towed vehicles, trailers, animal trailers and animals inside them. Carried and rope-led animals travel with you.
Characters and passengers arrive outside the vehicles, with the vehicles and trailers parked on open ground right beside them. A temporary map marker shows the vehicle’s landing position without leaving multiple markers on the map.

Single-player uses direct teleport. Multiplayer first attempts direct teleport; when network or map conditions do not support it, segmented teleport is used to reach the destination. Press Esc to end a segmented transfer. In multiplayer, the driver initiates the transfer and the other passengers travel together.

Multiplayer has undergone initial testing. Players are welcome to test on different servers and under different network conditions and share their feedback.

VEHICLE MOD COMPATIBILITY
Supports vanilla and modded vehicles using the game's native vehicle, towing and in-vehicle animal systems.

BACKUP KEYBOARD SHORTCUT
Bind UMTSP: Teleport Here (World Map) under Options → Key Bindings → Universal Map Teleport. Unbound by default.

STANDALONE
Subscribe to and enable this mod only. No base mod, ZombieBuddy or other prerequisites are required. Multiplayer servers and clients must use the same mod version.
'''
cn='''# Map Teleport – Vehicle & Trailer Add-on

【地图右键传送】
面向 B42.21 单人及多人游戏，在世界地图右键菜单加入独立的传送选项。

【模组菜单共存】
其他地图、导航/GPS、路线、目的地、标记、传送及作弊菜单等选项可以同时显示、分别选择。

【人物与动物】
选择 Teleport Here，传送自己、随身携带及绳索牵引的动物，到达后恢复牵引。坐车时也能使用。传送后，车辆和其他乘客会留在原地。

【车辆与拖车】
车队停稳后，在车内选择 Teleport Vehicle Here，传送自己、乘客、当前车辆及相连的牵引车队，包括被牵引车辆、拖车、动物拖车和车内动物，携带及绳索牵引的动物随行。
人物与乘客一并到达传送点并处于下车状态，车辆及拖车停放在身边的空地。地图显示车辆落点临时标记，不会在地图上留下多个标记。

单人直接传送；多人联机时优先尝试直接传送，网络或地图不支持时采用分段传送，同样可到达目的地，分段传送时按 Esc 结束传送。多人游戏由驾驶员发起，其他乘客一同传送。

多人功能完成初步测试，欢迎在不同服务器和网络环境中测试并反馈。

【车辆模组兼容】
支持原版及采用游戏原生车辆、牵引和车内动物机制的模组车辆。

【备用键盘快捷键】
在 Options → Key Bindings → Universal Map Teleport 中绑定 UMTSP: Teleport Here (World Map)，默认未绑定。

【独立使用】
仅需订阅并启用本模组，无需基础模组、ZombieBuddy 或其他前置。多人服务器与客户端须安装相同版本。
'''
for name,content in [('description-en.txt',en),('description-zh.txt',cn)]: (out/name).write_text(content,encoding='utf-8')
(release/'README.md').write_text(en+'\n---\n\n'+cn,encoding='utf-8')
info=release/'42/mod.info';text=info.read_text(encoding='utf-8-sig').replace('Disconnect trailers before vehicle teleport.','Includes connected towing chains and trailers.')
info.write_text(text,encoding='utf-8')
base=Path(r'C:\Users\zbjgr\Zomboid').resolve();workshop=next(p for p in (base/'Workshop').iterdir() if 'Vehicle' in p.name).resolve()
lines=(workshop/'workshop.txt').read_text(encoding='utf-8-sig').splitlines();meta=[l for l in lines if not l.startswith('description=')]
assert 'id=3822887136' in meta
meta+=['description='+line for line in (en+'\n'+cn).splitlines()]
metadata='\n'.join(meta)+'\n';(out/'workshop.txt').write_text(metadata,encoding='utf-8')
upload=(workshop/'Contents/mods/UMTSPVehicleBridge').resolve();local=(base/'mods/UMTSPVehicleBridge').resolve()
assert upload.parent==workshop/'Contents/mods' and local.parent==base/'mods' and upload.name==local.name=='UMTSPVehicleBridge'
backup=root/'work/vehicle-before-0.9.0';assert not backup.exists();backup.mkdir();shutil.copy2(workshop/'workshop.txt',backup/'workshop.txt')
art=hashlib.sha256((workshop/'preview.png').read_bytes()).hexdigest()
for target,name in [(upload,'upload-mod'),(local,'local-mod')]:
 shutil.move(str(target),str(backup/name));shutil.copytree(release,target)
 for p in release.rglob('*'):
  if p.is_file():assert p.read_bytes()==(target/p.relative_to(release)).read_bytes()
shutil.copy2(out/'workshop.txt',workshop/'workshop.txt')
assert art==hashlib.sha256((workshop/'preview.png').read_bytes()).hexdigest()
shutil.copytree(workshop,out/'Workshop');shutil.make_archive(str(root/'outputs/MapTeleportVehicle-0.9.0-upload'),'zip',out/'Workshop')
(out/'deployment.json').write_text(json.dumps({'version':'0.9.0','installed':str(local),'workshop_upload_folder':str(workshop),'backup':str(backup),'workshop_id':'3822887136','artwork_preserved':True,'tests':'isolated Lua regression and three-body towing tests; in-game convoy verification pending','steam_upload_status':'pending UI upload'},ensure_ascii=False,indent=2),encoding='utf-8')
print('Deployed 0.9.0 local and Workshop staging; artwork and Workshop ID preserved; no prerequisites. Steam upload pending.')
