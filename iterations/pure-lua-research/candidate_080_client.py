from pathlib import Path
p=Path('work/vehicle-candidate-0.8.0/42/media/lua/client/UMV_NetworkClient.lua');s=p.read_text()
s=s.replace('local N={session=nil,pending={}}','local N={session=nil,pending={},cleanup=nil}')
s=s.replace('    actor:setBlockMovement(guard and guard.wasBlocked==true)','''    actor:setBlockMovement(guard and guard.wasBlocked==true)
    if guard and guard.god~=nil then actor:setGodMod(guard.god) end
    if guard and guard.ghost~=nil then actor:setGhostMode(guard.ghost) end''',1)
s=s.replace('    v:setPhysicsActive(true,true);v:setWorldTransform(t)','''    v:setWorldTransform(t)
    v:checkSurroundingChunks()
    v:setPhysicsActive(true,true);v:setWorldTransform(t)''',1)
s=s.replace('    unfreeze(s.player,s.guard)\n    P.status=', '''    if s.sourcePin then
        N.cleanup={map=s.sourcePin,args=args,stable=0};s.sourcePin=nil
    end
    unfreeze(s.player,s.guard)
    P.status=''',1)
a=s.index('local function command(module,action,args)')
helpers='''local function pinAvailable(actor)
    if type(getNumActivePlayers)~="function" or getNumActivePlayers()~=1 or
        type(actor.getPlayerNum)~="function" or getSpecificPlayer(3) or
        type(getCell().getChunkMap)~="function" then return nil end
    local main=getCell():getChunkMap(actor:getPlayerNum());local map=getCell():getChunkMap(3)
    if not main or not map or type(map.copy)~="function" or type(map.Unload)~="function" then return nil end
    for x=0,math.floor(main:getWidthInTiles()/8)-1 do for y=0,math.floor(main:getWidthInTiles()/8)-1 do
        if map:getChunk(x,y) then return nil end
    end end
    return map,main
end
local function protectScout(s)
    if type(s.player.isGodMod)=="function" and s.guard.god==nil then
        s.guard.god=s.player:isGodMod();s.player:setGodMod(true)
    end
    if type(s.player.isGhostMode)=="function" and s.guard.ghost==nil then
        s.guard.ghost=s.player:isGhostMode();s.player:setGhostMode(true)
    end
end
'''
s=s[:a]+helpers+s[a:]
s=s.replace('send("ready",{token=s.token,version="0.8.0"})','send("ready",{token=s.token,version="0.8.0",remoteCap=pinAvailable(s.player)~=nil})',1)
s=s.replace('    elseif action=="probe" then','''    elseif action=="pin" then
        local map,main=pinAvailable(s.player)
        if map then
            s.sourcePin=map;s.mainMap=main
            local ok=pcall(function()map:copy(main)end)
            send("pinned",{token=s.token,ready=ok})
        else send("pinned",{token=s.token,ready=false}) end
    elseif action=="releasePin" then
        if s.sourcePin then s.sourcePin:Unload();s.sourcePin=nil end
    elseif action=="scout" then
        protectScout(s);detach(s.player)
        s.player:teleportTo(args.x,args.y,0);s.mainMap:ProcessChunkPos(s.player)
        s.scout=args;P.status="Loading destination; source protected by passenger..."
    elseif action=="probe" then''',1)
s=s.replace('        s.sequence=args.sequence;s.move=args;s.settle=0','        s.sequence=args.sequence;s.move=args;s.settle=0;s.moveStarted=getTimestampMs();s.remoteMirrorDone=false;s.scout=nil',1)
s=s.replace('        detach(s.player);s.player:teleportTo(args.playerX,args.playerY,0)\n        P.progress=', '''        if args.remote then protectScout(s) end
        detach(s.player);s.player:teleportTo(args.playerX,args.playerY,0)
        if args.remote and s.mainMap then s.mainMap:ProcessChunkPos(s.player) end
        P.progress=''',1)
s=s.replace('        if s.move then\n            s.settle=s.settle+1','''        if s.scout then
            local a=s.scout;local loaded=true
            for dx=-8,8,8 do for dy=-8,8,8 do
                if not getCell():getGridSquare(math.floor(a.x+dx),math.floor(a.y+dy),0) then loaded=false end
            end end
            if loaded then send("scouted",{token=s.token});s.scout=nil end
        end
        if s.move then
            if s.move.remote and not s.remoteMirrorDone then
                local ok,applied=pcall(mirror,s.move)
                if ok and applied then s.remoteMirrorDone=true;s.settle=0 end
                if getTimestampMs()-s.moveStarted>30000 then
                    send("arrived",{token=s.token,sequence=s.move.sequence,ready=false});s.move=nil
                end
            end
            if s.move and (not s.move.remote or s.remoteMirrorDone) then
            s.settle=s.settle+1''',1)
s=s.replace('                s.move=nil\n            end\n        end\n    end\n    tick=', '                s.move=nil\n            end\n            end\n        end\n    end\n    if N.cleanup then\n        local c=N.cleanup;local a=c.args\n        local v=findVehicle(a)\n        if v and math.abs(v:getX()-a.x)<2 and math.abs(v:getY()-a.y)<2 and getCell():getGridSquare(math.floor(a.x),math.floor(a.y),0) then\n            c.stable=c.stable+1\n            if c.stable>=8 then c.map:Unload();N.cleanup=nil end\n        else\n            c.stable=0;pcall(mirror,a)\n        end\n    end\n    tick=',1)
p.write_text(s,encoding='utf-8')
