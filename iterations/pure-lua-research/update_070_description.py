from pathlib import Path
import shutil
base=Path(r'C:\Users\zbjgr\Zomboid');workshop=next(p for p in (base/'Workshop').iterdir() if 'Vehicle' in p.name)
root=Path.cwd();out=root/'outputs/MapTeleportVehicle-0.7.0'
cn_old='远距离自动加载所需区域，可按 Esc 在当前停靠点结束。'
cn_new='单人远距离传送会先加载目的地区域，再直接传车；多人采用分段传送，可按 Esc 在当前停靠点结束。'
en_old='Long-distance travel automatically loads the required areas. Press Esc to end at the current checkpoint.'
en_new='In single-player, long-distance vehicle teleport loads the destination area before moving the vehicle directly. Multiplayer transfers use successive checkpoints; press Esc to end at the current checkpoint.'
paths=[workshop/'workshop.txt',workshop/'Contents/mods/UMTSPVehicleBridge/README.md',base/'mods/UMTSPVehicleBridge/README.md',root/'work/vehicle-release-0.7.0/README.md',out/'description-en.txt',out/'description-zh.txt',out/'workshop.txt',out/'Workshop/workshop.txt',out/'Workshop/Contents/mods/UMTSPVehicleBridge/README.md']
for p in paths:
 text=p.read_text(encoding='utf-8-sig')
 assert cn_old in text or en_old in text,str(p)
 p.write_text(text.replace(cn_old,cn_new).replace(en_old,en_new),encoding='utf-8')
shutil.make_archive(str(root/'outputs/MapTeleportVehicle-0.7.0-upload'),'zip',out/'Workshop')
print('Updated bilingual descriptions in source, local mod, Workshop upload folder and packaged copy.')
