from pathlib import Path
import shutil
root=Path('work/vehicle-release-0.7.0');assert not root.exists();shutil.copytree('work/vehicle-release-0.6.3',root)
for p in root.rglob('*'):
 if p.is_file() and p.suffix in ('.lua','.md','.info'):
  s=p.read_text(encoding='utf-8-sig').replace('0.6.3','0.7.0')
  p.write_text(s,encoding='utf-8')
p=root/'42/media/lua/shared/UMV_Vehicle.lua';s=p.read_text()
s=s.replace('function P.stop(message,success)\n','function P.stop(message,success)\n    if P.session and P.session.remote then return P.remoteCancel(message) end\n',1)
s=s.replace('    if not s or s.network then return end','    if not s or s.network or s.remote then return end',1)
s=s.replace('    if P.onStarted then\n        local shown,uiError=', '''    if P.remotePrepare then
        local ready,why=pcall(P.remotePrepare,s)
        if not ready then P.stop("Destination preparation failed: "..tostring(why));return false end
    end
    if P.onStarted then
        local shown,uiError=''',1)
p.write_text(s,encoding='utf-8')
p=root/'42/media/lua/client/UMV_Progress.lua';s=p.read_text().replace('require "UMV_NetworkClient"','require "UMV_NetworkClient"\nrequire "UMV_RemoteSP"');p.write_text(s,encoding='utf-8')
