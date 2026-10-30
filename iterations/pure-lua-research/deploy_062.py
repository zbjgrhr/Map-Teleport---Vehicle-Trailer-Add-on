from pathlib import Path
import shutil,hashlib,json
root=Path.cwd();base=Path(r'C:\Users\zbjgr\Zomboid').resolve();source=root/'work/vehicle-release-0.6.2'
workshop=next(p for p in (base/'Workshop').iterdir() if 'Vehicle' in p.name).resolve()
upload=(workshop/'Contents/mods/UMTSPVehicleBridge').resolve();local=(base/'mods/UMTSPVehicleBridge').resolve()
assert upload.parent==workshop/'Contents/mods' and local.parent==base/'mods'
assert upload.name==local.name=='UMTSPVehicleBridge'
backup=root/'work/vehicle-before-0.6.2';assert not backup.exists();backup.mkdir()
art=hashlib.sha256((workshop/'preview.png').read_bytes()).hexdigest()
metadata=(workshop/'workshop.txt').read_bytes()
for target,name in [(upload,'upload-mod'),(local,'local-mod')]:
 shutil.move(str(target),str(backup/name));shutil.copytree(source,target)
 for p in source.rglob('*'):
  if p.is_file():assert p.read_bytes()==(target/p.relative_to(source)).read_bytes()
assert metadata==(workshop/'workshop.txt').read_bytes()
assert art==hashlib.sha256((workshop/'preview.png').read_bytes()).hexdigest()
out=root/'outputs/MapTeleportVehicle-0.6.2';out.mkdir()
for name in ['description-en.txt','description-zh.txt']:
 shutil.copy2(root/'outputs/MapTeleportVehicle-0.6.1'/name,out/name)
shutil.copytree(workshop,out/'Workshop')
shutil.make_archive(str(root/'outputs/MapTeleportVehicle-0.6.2-upload'),'zip',out/'Workshop')
(out/'deployment.json').write_text(json.dumps({'version':'0.6.2','SP_max_candidate_step':128,'MP_max_candidate_step':24,'description_and_artwork_preserved':True,'real_game_validation':'pending','wide_window_simulation_steps_before':38,'wide_window_simulation_steps_after':29},indent=2),encoding='utf-8')
print('Deployed 0.6.2 to local and Workshop upload folders. Descriptions and artwork preserved.')
