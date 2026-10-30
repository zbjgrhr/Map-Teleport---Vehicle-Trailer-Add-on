from pathlib import Path
p=Path('work/vehicle-release-0.6.3/42/media/lua/shared/UMV_Vehicle.lua');s=p.read_text();s=s.replace('        if best then return unpack(best) end\n    end\n    if best then return unpack(best) end','    end\n    if best then return unpack(best) end',1);p.write_text(s,encoding='utf-8')
s=Path('work/pure-lua-research/deploy_062.py').read_text(encoding='utf-8-sig').replace('0.6.2','0.6.3').replace('SP_max_candidate_step\':128','SP_max_candidate_step\':512').replace("'wide_window_simulation_steps_before':38,'wide_window_simulation_steps_after':29","'broad_window_simulation_steps':8")
exec(compile(s,'deploy-063','exec'))
