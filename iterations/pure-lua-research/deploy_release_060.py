from pathlib import Path
import json,shutil,hashlib,datetime
root=Path.cwd();meta=json.loads((root/'work/vehicle-release-paths.json').read_text(encoding='utf-8'))
workshop=Path(meta['workshop']).resolve();source=Path(meta['source']).resolve()
base=Path(r'C:\Users\zbjgr\Zomboid').resolve();upload=(workshop/'Contents/mods/UMTSPVehicleBridge').resolve();local=(base/'mods/UMTSPVehicleBridge').resolve()
assert workshop.parent==base/'Workshop'
assert upload.parent==workshop/'Contents/mods' and upload.name=='UMTSPVehicleBridge'
assert local.parent==base/'mods' and local.name=='UMTSPVehicleBridge'
backup=root/'work/vehicle-before-0.6.0';assert not backup.exists(),'Backup exists; inspect before retry'
backup.mkdir()
shutil.copy2(workshop/'workshop.txt',backup/'workshop.txt')
previewHash=hashlib.sha256((workshop/'preview.png').read_bytes()).hexdigest()
for current,name in [(upload,'upload-mod'),(local,'local-mod')]:
 assert current.is_dir()
 shutil.move(str(current),str(backup/name))
 shutil.copytree(source,current)
shutil.copy2(root/'outputs/MapTeleportVehicle-0.6.0/workshop.txt',workshop/'workshop.txt')
assert hashlib.sha256((workshop/'preview.png').read_bytes()).hexdigest()==previewHash
for target in [upload,local]:
 files=list(target.rglob('*'))
 assert not any(p.suffix=='.jar' for p in files)
 info=(target/'42/mod.info').read_text(encoding='utf-8')
 assert '\nrequire=' not in info and 'javaJarFile=' not in info
 assert 'id=UMTSPVehicleBridge' in info and 'modversion=0.6.0' in info
 for p in source.rglob('*'):
  if p.is_file():assert (target/p.relative_to(source)).read_bytes()==p.read_bytes(),str(p)
 for p in (target/'42/media/lua').rglob('*.lua'):
  assert '[Pure Lua Test]' not in p.read_text(encoding='utf-8')
package=root/'outputs/MapTeleportVehicle-0.6.0/Workshop'
shutil.copytree(workshop,package)
shutil.make_archive(str(root/'outputs/MapTeleportVehicle-0.6.0-upload'),'zip',package)
report={'version':'0.6.0','workshop_id':'3822887136','title':'Map Teleport – Vehicle & Trailer Add-on','upload':str(upload),'local':str(local),'preview_sha256':previewHash,'dependencies':[],'jars':0,'max_candidate_step':96,'game_test':'pending','steam_required_items':'remove manually after update','backup':str(backup)}
(root/'outputs/MapTeleportVehicle-0.6.0/deployment.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
