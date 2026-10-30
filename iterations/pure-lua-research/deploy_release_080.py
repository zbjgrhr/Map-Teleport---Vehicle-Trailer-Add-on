from pathlib import Path
import shutil,hashlib,json
root=Path.cwd();source=root/'work/vehicle-candidate-0.8.0';release=root/'work/vehicle-release-0.8.0';assert not release.exists();shutil.copytree(source,release)
out=root/'outputs/MapTeleportVehicle-0.8.0';out.mkdir()
prior=root/'outputs/MapTeleportVehicle-0.7.1'
en=(prior/'description-en.txt').read_text(encoding='utf-8');cn=(prior/'description-zh.txt').read_text(encoding='utf-8')
cn_old='单人远距离传送会先加载目的地区域，再直接传车；多人采用分段传送，可按 Esc 在当前停靠点结束。多人游戏由驾驶员发起，其他乘客一同传送。'
cn_new='单人远距离传送会先加载目的地区域，再直接传车；多人两人及以上同车时优先尝试直接传送，条件不足时采用分段传送。可按 Esc 结束传送。多人游戏由驾驶员发起，其他乘客一同传送。\n多人功能已进行初步测试，欢迎玩家在不同服务器和网络环境中测试并反馈。'
en_old='In single-player, long-distance vehicle teleport loads the destination area before moving the vehicle directly. Multiplayer transfers use successive checkpoints; press Esc to end at the current checkpoint. In multiplayer, the driver initiates the transfer and the other passengers travel together.'
en_new='In single-player, long-distance vehicle teleport loads the destination area before moving the vehicle directly. With two or more occupants, multiplayer transfers first attempt direct teleport and fall back to successive checkpoints when needed. Press Esc to end the transfer. In multiplayer, the driver initiates the transfer and the other passengers travel together.\nMultiplayer has undergone initial testing. Players are welcome to test on different servers and under different network conditions and share their feedback.'
assert cn_old in cn and en_old in en
cn=cn.replace(cn_old,cn_new);en=en.replace(en_old,en_new)
for name,content in [('description-en.txt',en),('description-zh.txt',cn)]: (out/name).write_text(content,encoding='utf-8')
(release/'README.md').write_text(en+'\n---\n\n'+cn,encoding='utf-8')
base=Path(r'C:\Users\zbjgr\Zomboid').resolve();workshop=next(p for p in (base/'Workshop').iterdir() if 'Vehicle' in p.name).resolve()
lines=(workshop/'workshop.txt').read_text(encoding='utf-8-sig').splitlines();meta=[l for l in lines if not l.startswith('description=')]
meta+=['description='+line for line in (en+'\n'+cn).splitlines()]
metadata='\n'.join(meta)+'\n';(out/'workshop.txt').write_text(metadata,encoding='utf-8')
upload=(workshop/'Contents/mods/UMTSPVehicleBridge').resolve();local=(base/'mods/UMTSPVehicleBridge').resolve()
assert upload.parent==workshop/'Contents/mods' and local.parent==base/'mods' and upload.name==local.name=='UMTSPVehicleBridge'
backup=root/'work/vehicle-before-0.8.0';assert not backup.exists();backup.mkdir();shutil.copy2(workshop/'workshop.txt',backup/'workshop.txt')
art=hashlib.sha256((workshop/'preview.png').read_bytes()).hexdigest()
for target,name in [(upload,'upload-mod'),(local,'local-mod')]:
 shutil.move(str(target),str(backup/name));shutil.copytree(release,target)
 for p in release.rglob('*'):
  if p.is_file():assert p.read_bytes()==(target/p.relative_to(release)).read_bytes()
shutil.copy2(out/'workshop.txt',workshop/'workshop.txt')
assert art==hashlib.sha256((workshop/'preview.png').read_bytes()).hexdigest()
shutil.copytree(workshop,out/'Workshop');shutil.make_archive(str(root/'outputs/MapTeleportVehicle-0.8.0-upload'),'zip',out/'Workshop')
(out/'deployment.json').write_text(json.dumps({'version':'0.8.0','installed':str(local),'workshop_upload_folder':str(workshop),'old_version_backup':str(backup),'workshop_id':'3822887136','artwork_preserved':True,'initial_testing_statement':'user-reported initial testing; automated checks are isolated simulations','steam_upload_status':'pending UI upload'},ensure_ascii=False,indent=2),encoding='utf-8')
print('0.8.0 deployed; bilingual description changes limited to long-distance multiplayer paragraph and initial-testing invitation.')
