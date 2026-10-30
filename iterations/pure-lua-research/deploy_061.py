from pathlib import Path
import json,shutil,hashlib
root=Path.cwd();source=(root/'work/vehicle-release-0.6.1').resolve();base=Path(r'C:\Users\zbjgr\Zomboid').resolve()
workshop=next(p for p in (base/'Workshop').iterdir() if 'Vehicle' in p.name).resolve()
upload=(workshop/'Contents/mods/UMTSPVehicleBridge').resolve();local=(base/'mods/UMTSPVehicleBridge').resolve()
assert upload.parent==workshop/'Contents/mods' and local.parent==base/'mods'
assert upload.name==local.name=='UMTSPVehicleBridge'
backup=root/'work/vehicle-before-0.6.1';assert not backup.exists();backup.mkdir()
shutil.copy2(workshop/'workshop.txt',backup/'workshop.txt')
art=hashlib.sha256((workshop/'preview.png').read_bytes()).hexdigest()
for target,name in [(upload,'upload-mod'),(local,'local-mod')]:
 assert target.is_dir();shutil.move(str(target),str(backup/name));shutil.copytree(source,target)
shutil.copy2(root/'outputs/MapTeleportVehicle-0.6.1/workshop.txt',workshop/'workshop.txt')
for target in [upload,local]:
 for p in source.rglob('*'):
  if p.is_file():assert (target/p.relative_to(source)).read_bytes()==p.read_bytes(),str(p)
 assert not list(target.rglob('*.jar'))
 assert not (target/'42/media/lua/client/UMV_Vehicle.lua').exists()
 assert (target/'42/media/lua/shared/UMV_Vehicle.lua').exists()
 info=(target/'42/mod.info').read_text(encoding='utf-8');assert '\nrequire=' not in info and 'modversion=0.6.1' in info
assert hashlib.sha256((workshop/'preview.png').read_bytes()).hexdigest()==art
out=root/'outputs/MapTeleportVehicle-0.6.1';shutil.copytree(workshop,out/'Workshop')
shutil.make_archive(str(root/'outputs/MapTeleportVehicle-0.6.1-upload'),'zip',out/'Workshop')
report={'version':'0.6.1','mod_id':'UMTSPVehicleBridge','workshop_id':'3822887136','dependencies':[],'preview_preserved':True,'single_player_step_max':96,'network_step_max':24,'network_driver_initiated':True,'checks':['game Lua compiler','server + two client isolated simulations','missing client timeout with no movement','passenger cancellation','single-player person/animal and vehicle regression'],'real_multiplayer_game_test':'pending','backup':str(backup),'upload':str(upload),'local':str(local)}
(out/'deployment.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('Deployed and verified 0.6.1 in local and Workshop folders; title, workshop ID and artwork preserved; real MP game test pending.')
