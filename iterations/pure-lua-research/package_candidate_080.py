from pathlib import Path
import shutil,json,hashlib
root=Path.cwd();candidate=root/'work/vehicle-candidate-0.8.0';out=root/'outputs/MapTeleportVehicle-0.8.0-candidate';out.mkdir()
package=out/'Contents/mods/UMTSPVehicleBridge';package.parent.mkdir(parents=True);shutil.copytree(candidate,package)
base=Path(r'C:\Users\zbjgr\Zomboid');workshop=next(p for p in (base/'Workshop').iterdir() if 'Vehicle' in p.name)
shutil.copy2(workshop/'preview.png',out/'preview.png')
(out/'README-验证范围.txt').write_text('0.8.0 联网远端加载候选，尚未覆盖正式0.7.1。\n至少两名同车玩家且所有客户端有空闲区块槽时：一名乘客保留服务器起点，其他人先加载目的地；服务器移车后最后一名乘客抵达并确认。\n不满足条件时继续使用0.7.1的自适应分段流程。单人沿用已验证的0.7.x远端流程。\n独立模拟：一个服务器、两个具有独立加载窗口的客户端，约7200格一次实际车辆提交；取消返回、部分服务器写入失败返回、备用槽不可用时回退通过。\n尚未验证：真实游戏联机、网络丢包/重排、起点留守玩家断线、原生反作弊与区块下载竞争。因此不作为已验证正式版发布。\n正式本机和上传目录仍是0.7.1，没有被这个候选包覆盖。\n',encoding='utf-8')
report={'candidate_version':'0.8.0','default_installed_version':'0.7.1','formal_files_overwritten':False,'remote_mp_conditions':['at least two seated network players','all clients have spare source chunk slot','safe source landing','destination scout and source anchor both retained until server vehicle commit'],'independent_simulation_trip_tiles':7200,'actual_vehicle_commits':1,'checks':['source retention across independent client map unloads','all passenger arrival acknowledgements','native-state readback in client model','pin release after stable arrival','cancellation while destination loads','partial server write rollback','normal segmented fallback without chunk-slot capability'],'real_multiplayer_game_test':'not performed','remaining_validation':['real server/client chunk streaming','loss/reordering','anchor player disconnect','native anti-cheat interaction']}
(out/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
shutil.make_archive(str(root/'outputs/MapTeleportVehicle-0.8.0-candidate'),'zip',out)
info=(base/'mods/UMTSPVehicleBridge/42/mod.info').read_text(encoding='utf-8');assert 'modversion=0.7.1' in info
print('Candidate packaged separately. Installed and Workshop versions remain 0.7.1.')
