from pathlib import Path
p=Path('work/vehicle-release-0.6.1/42/media/lua/server/UMV_NetworkServer.lua');s=p.read_text(encoding='utf-8-sig')
s=s.replace('    s.phase="plan";s.changed=now()\nend','''    for i,m in ipairs(s.occupants) do
        send(m.actor,"begin",{token=s.token,playerX=exits[i].x,playerY=exits[i].y})
    end
    s.phase="lease";s.changed=now()
end''',1)
s=s.replace('if action=="ready" and s.phase=="prepare" then m.ready=true;return end','''if action=="ready" and s.phase=="prepare" and args.version=="0.6.1" then m.ready=true;return end
    if action=="leased" and s.phase=="lease" then m.leased=true;return end''')
s=s.replace('    if s.phase=="probe" then\n        if not all', '    if s.phase=="lease" then if all(s,"leased") then s.phase="plan";s.changed=now() end;return end\n    if s.phase=="probe" then\n        if not all')
p.write_text(s,encoding='utf-8')
