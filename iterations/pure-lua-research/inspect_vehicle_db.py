import sqlite3
from pathlib import Path
p=Path(r'C:\Users\zbjgr\Zomboid\Saves\Sandbox\2026-10-22_15-11-59\vehicles.db')
c=sqlite3.connect(p.as_uri()+'?mode=ro',uri=True)
print(c.execute("select name from sqlite_master where type='table'").fetchall())
print(c.execute('pragma table_info(vehicles)').fetchall())
print(c.execute('select id,wx,wy,x,y,length(data) from vehicles where id=13').fetchall())
c.close()
