from pathlib import Path
import json,shutil,hashlib
root=Path.cwd();release=root/'work/vehicle-release-0.7.1';base=Path(r'C:\Users\zbjgr\Zomboid').resolve()
workshop=next(p for p in (base/'Workshop').iterdir() if 'Vehicle' in p.name).resolve()
upload=(workshop/'Contents/mods/UMTSPVehicleBridge').resolve();local=(base/'mods/UMTSPVehicleBridge').resolve()
assert upload.parent==workshop/'Contents/mods' and local.parent==base/'mods' and upload.name==local.name=='UMTSPVehicleBridge'
backup=root/'work/vehicle-before-0.7.1';assert not backup.exists();backup.mkdir()
art=hashlib.sha256((workshop/'preview.png').read_bytes()).hexdigest();metadata=(workshop/'workshop.txt').read_bytes()
for target,name in [(upload,'upload-mod'),(local,'local-mod')]:
 shutil.move(str(target),str(backup/name));shutil.copytree(release,target)
 for p in release.rglob('*'):
  if p.is_file():assert p.read_bytes()==(target/p.relative_to(release)).read_bytes()
assert art==hashlib.sha256((workshop/'preview.png').read_bytes()).hexdigest() and metadata==(workshop/'workshop.txt').read_bytes()
out=root/'outputs/MapTeleportVehicle-0.7.1';out.mkdir()
for name in ['description-en.txt','description-zh.txt']:
 shutil.copy2(root/'outputs/MapTeleportVehicle-0.7.0'/name,out/name)
shutil.copytree(workshop,out/'Workshop');shutil.make_archive(str(root/'outputs/MapTeleportVehicle-0.7.1-upload'),'zip',out/'Workshop')
report={'version':'0.7.1','network_max_candidate_step':64,'actual_landing_requires_all_clients_ready':True,'failed_probe':'reduce cap to next smaller actual step before any movement','arrival_verification':'retained','single_player_remote_load':'unchanged','simulated_trip_tiles':700,'previous_committed_checkpoints':30,'new_committed_checkpoints':20,'real_multiplayer_game_test':'not performed','checks':['separate server and two clients','narrower passenger load window fallback','missing-client timeout without movement','passenger cancellation','driver-only initiation'],'backup':str(backup)}
(out/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('0.7.1 deployed and hash verified; name, artwork, descriptions and dependency-free packaging preserved.')
