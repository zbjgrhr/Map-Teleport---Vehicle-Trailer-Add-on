from pathlib import Path
c=Path('work/vehicle-release-0.9.0/42/media/lua/shared/UMV_Convoy.lua').read_text(encoding='utf-8-sig')
dep='\nConvoyModule=(function()\n'+c+'\nend)()\nrequire=function(name)if name=="UMV_Convoy" then return ConvoyModule end end\nfunction v:authorizationChanged()self.netID=-1 end\n'
# Run the complete prior SP far-load/animal fixture against this release.
s=Path('work/pure-lua-research/test_remote_070.py').read_text(encoding='utf-8-sig').replace('work/vehicle-release-0.7.0/42/media/lua','work/vehicle-release-0.9.0/42/media/lua')
s=s.replace('l.execute(fixture)','l.execute(fixture+'+repr(dep)+')')
exec(compile(s,'SP-090-regression','exec'))
# Run the prior multi-client remote-load scenarios with their independent chunk maps.
s=Path('work/pure-lua-research/test_remote_network_080.py').read_text(encoding='utf-8-sig').replace('work/vehicle-candidate-0.8.0','work/vehicle-release-0.9.0')
s=s.replace("namespace={'install_world':install_world}","cut=cut.replace('l.execute(fixture)',"+repr('l.execute(fixture+'+repr(dep)+')')+")\nnamespace={'install_world':install_world}")
exec(compile(s,'MP-090-regression','exec'))
