from pathlib import Path
import shutil,json
root=Path.cwd();src=root/'work/pure-lua-vehicle-test';dest=root/'work/vehicle-release-0.6.0'
assert not dest.exists(),'Release staging already exists'
shutil.copytree(src,dest)
renames={'PLVT_Core':'UMV_Vehicle','PLVT_Main':'UMV_Progress','UMTSP_Main':'UMV_Main','UMTSP_Config':'UMV_Config','UMTSP_Animals':'UMV_Animals','UMTSP_PersonSeat':'UMV_PersonSeat','UMTSP_Server':'UMV_Server'}
for p in list((dest/'42/media/lua').rglob('*.lua')):
 s=p.read_text(encoding='utf-8-sig')
 for old,new in renames.items():s=s.replace(old,new)
 s=s.replace('[PureLuaVehicleTest]','[MapTeleportVehicle]').replace('[Lua Test]','[UMT]')
 s=s.replace('Teleport Vehicle Here [Pure Lua Test]','Teleport Vehicle Here')
 s=s.replace('PURE LUA VEHICLE TEST','VEHICLE TELEPORT').replace('Loaded 0.1.5;','Loaded 0.6.0;')
 s=s.replace('This experiment currently runs in single-player only','Vehicle teleport currently supports single-player saves')
 s=s.replace('Disable the Java vehicle add-on before testing the pure Lua version','Another vehicle bridge is active; restart after updating the vehicle mod')
 s=s.replace('First test: disconnect trailers and use one vehicle','Disconnect the trailer before teleporting this vehicle')
 s=s.replace('Vehicle is too large for this experiment','Vehicle size exceeds the supported landing search')
 s=s.replace('local MAX_STEP, STREAM_TIMEOUT, TRIP_TIMEOUT = 64,','local MAX_STEP, STREAM_TIMEOUT, TRIP_TIMEOUT = 96,')
 s=s.replace('ipairs({64,56,48,40,32,24,18,12,8})','ipairs({96,80,64,56,48,40,32,24,18,12,8})')
 s=s.replace('for radius=32,64,8 do','for radius=32,96,8 do')
 s=s.replace('"UMTSP"','"UMV"').replace('option.UMTSP','option.UMV').replace('vehicleOption.UMTSP','vehicleOption.UMV')
 s=s.replace('Vehicle transfer is unavailable. Approve the vehicle Java mod in ZombieBuddy and restart.','Vehicle transfer is unavailable; restart after updating the mod.')
 s=s.replace('Vehicle component is unavailable. Approve it in ZombieBuddy, or exit the vehicle for person-only teleport.','Vehicle component is unavailable; restart after updating the mod.')
 s=s.replace('-- Experimental SP vehicle travel through overlapping loaded areas.','-- Standalone SP vehicle travel through overlapping loaded areas.')
 s=s.replace('-- Server-authoritative teleport. Vehicle moves require the ZombieBuddy bridge.','-- Server-authoritative character and animal teleport.')
 new=p.with_name(renames.get(p.stem,p.stem)+'.lua');new.write_text(s,encoding='utf-8')
 if new!=p:p.unlink()
info='''name=Map Teleport – Vehicle & Trailer Add-on
id=UMTSPVehicleBridge
author=[IA] Introvert Arcade
modversion=0.6.0
versionMin=42.21
category=features
poster=poster.png
description=Standalone world-map character and animal teleport, with long-distance vehicle teleport and seated passengers in single-player saves. No base mod, ZombieBuddy or Java installation required. Disconnect trailers before vehicle teleport; network vehicle teleport is not supported in this version.
'''
(dest/'42/mod.info').write_text(info,encoding='utf-8')
workshop=next(p for p in Path(r'C:\Users\zbjgr\Zomboid\Workshop').iterdir() if 'Vehicle' in p.name)
shutil.copy2(workshop/'preview.png',dest/'42/poster.png')
(root/'work/vehicle-release-paths.json').write_text(json.dumps({'workshop':str(workshop),'source':str(dest)},ensure_ascii=False),encoding='utf-8')
print('Prepared',dest)
