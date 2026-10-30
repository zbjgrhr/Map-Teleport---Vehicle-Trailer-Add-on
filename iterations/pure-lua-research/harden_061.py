from pathlib import Path
p=Path('work/vehicle-release-0.6.1/42/media/lua/server/UMV_NetworkServer.lua');s=p.read_text(encoding='utf-8-sig')
s=s.replace('local function send(actor,command,args) sendServerCommand(actor,MODULE,command,args) end','''local function send(actor,command,args)
    local ok,why=pcall(sendServerCommand,actor,MODULE,command,args)
    if not ok then log("client notification: "..tostring(why)) end
end''')
s=s.replace('x=s.vehicle:getX(),y=s.vehicle:getY(),success=success==true,reason=reason,mark=s.begun==true','x=s.vehicle:getX(),y=s.vehicle:getY(),playerX=m.actor:getX(),playerY=m.actor:getY(),success=success==true,reason=reason,mark=s.begun==true')
s=s.replace('        H.place(s,s.stepX,s.stepY,square)','''        local oldX,oldY=s.vehicle:getX(),s.vehicle:getY()
        local oldSquare=getCell():getGridSquare(math.floor(oldX),math.floor(oldY),0)
        local moved,why=pcall(H.place,s,s.stepX,s.stepY,square)
        if not moved then
            if identity(s) and oldSquare then
                local restored,reason=pcall(H.place,s,oldX,oldY,oldSquare)
                log("step rollback="..tostring(restored).." "..tostring(reason))
            end
            error(why)
        end''')
p.write_text(s,encoding='utf-8')
p=Path('work/vehicle-release-0.6.1/42/media/lua/client/UMV_NetworkClient.lua');s=p.read_text(encoding='utf-8-sig')
s=s.replace('local function stop(args)','local detach\nlocal function stop(args)')
s=s.replace('    unfreeze(s.player,s.guard)','''    if args.mark and args.playerX and args.playerY then
        pcall(mirror,args)
        detach(s.player)
        s.player:teleportTo(args.playerX,args.playerY,0)
    end
    unfreeze(s.player,s.guard)''',1)
s=s.replace('local function detach(actor)','detach=function(actor)')
s=s.replace('    if args.token~=s.token then return end\n    if action=="begin"','    if args.token~=s.token then return end\n    s.lastMessage=getTimestampMs()\n    if action=="begin"')
s=s.replace('    if s then\n        if not s.token','''    if s then
        if s.token and getTimestampMs()-(s.lastMessage or s.requested)>45000 then
            stop({reason="Connection to the transfer server was lost; check the current vehicle position"});return
        end
        if not s.token''')
p.write_text(s,encoding='utf-8')
