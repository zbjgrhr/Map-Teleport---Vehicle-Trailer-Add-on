from pathlib import Path
import shutil,json,hashlib
root=Path.cwd();release=root/'work/vehicle-release-0.7.0';out=root/'outputs/MapTeleportVehicle-0.7.0';out.mkdir()
previous=root/'outputs/MapTeleportVehicle-0.6.2'
en=(previous/'description-en.txt').read_text(encoding='utf-8').replace('Long-distance travel automatically loads successive areas.','Long-distance travel automatically loads the required areas.')
cn=(previous/'description-zh.txt').read_text(encoding='utf-8').replace('远距离自动分段加载','远距离自动加载所需区域')
for name,content in [('description-en.txt',en),('description-zh.txt',cn)]: (out/name).write_text(content,encoding='utf-8')
(release/'README.md').write_text(en+'\n---\n\n'+cn,encoding='utf-8')
(out/'verification.txt').write_text('0.7.0：单人远端加载流程，先保留起点区块，加载目的地后移动原车辆。\n原生接口：游戏 Kahlua 的 chunkMap copy/getChunk/Unload/ProcessChunkPos 暴露检查通过。\n原生 DLL：空物理世界中释放未启用的2/3号槽后，0号物理场景仍可继续模拟。\n独立模拟：约7200格一次远距离移车；取消、无落点、部分写入失败返回；乘客和原动物模块联合检查通过。\n车辆身份与区块保存检查、人物状态恢复、区块引用释放检查通过。\n真实游戏：尚待验证，不能把模拟当作游戏内成功。\n联网：保留0.6.x的逐段同步流程，上限24格；本次未实现联网远端预加载。\n测试：单人先传到几千格外公路，观察Loading destination是否之后直接到达；下车后重新开车、离开再返回并重进存档，确认车辆状态和物品。日志前缀[MapTeleportVehicle/Remote]记录真实跳数、跳距、加载耗时。\n',encoding='utf-8')
base=Path(r'C:\Users\zbjgr\Zomboid').resolve();workshop=next(p for p in (base/'Workshop').iterdir() if 'Vehicle' in p.name).resolve()
meta=(workshop/'workshop.txt').read_text(encoding='utf-8').replace('Long-distance travel automatically loads successive areas.','Long-distance travel automatically loads the required areas.').replace('远距离自动分段加载','远距离自动加载所需区域')
(out/'workshop.txt').write_text(meta,encoding='utf-8')
upload=(workshop/'Contents/mods/UMTSPVehicleBridge').resolve();local=(base/'mods/UMTSPVehicleBridge').resolve()
assert upload.parent==workshop/'Contents/mods' and local.parent==base/'mods' and upload.name==local.name=='UMTSPVehicleBridge'
backup=root/'work/vehicle-before-0.7.0';assert not backup.exists();backup.mkdir()
shutil.copy2(workshop/'workshop.txt',backup/'workshop.txt')
art=hashlib.sha256((workshop/'preview.png').read_bytes()).hexdigest()
for target,name in [(upload,'upload-mod'),(local,'local-mod')]:
 shutil.move(str(target),str(backup/name));shutil.copytree(release,target)
 for p in release.rglob('*'):
  if p.is_file():assert p.read_bytes()==(target/p.relative_to(release)).read_bytes()
 assert not list(target.rglob('*.jar'))
shutil.copy2(out/'workshop.txt',workshop/'workshop.txt')
assert art==hashlib.sha256((workshop/'preview.png').read_bytes()).hexdigest()
shutil.copytree(workshop,out/'Workshop');shutil.make_archive(str(root/'outputs/MapTeleportVehicle-0.7.0-upload'),'zip',out/'Workshop')
(out/'deployment.json').write_text(json.dumps({'version':'0.7.0','local':str(local),'upload':str(upload),'backup':str(backup),'art_preserved':True,'SP_remote_load':'enabled when both spare native slots and a safe origin are available','MP_remote_load':'not implemented; existing synchronized steps retained','real_game_test':'pending','simulated_7200_tile_vehicle_jumps':1},ensure_ascii=False,indent=2),encoding='utf-8')
print('Deployed and hash-verified 0.7.0; previous 0.6.3 files archived. Single-player remote-load path enabled; MP unchanged; real-game test pending.')
