from pathlib import Path
import sqlite3, hashlib, json, math
p=Path(r'C:\Users\zbjgr\Zomboid\Saves\Sandbox\2026-10-22_15-11-59\vehicles.db')
out=Path('outputs/vehicle-save-recovery-2026-10-22');out.mkdir(exist_ok=True)
backup=out/'vehicles-before-index-repair.db'
if backup.exists():raise RuntimeError('Backup already exists; refusing a repeat repair')
c=sqlite3.connect(p)
row=c.execute('select id,wx,wy,x,y,inMeta,data from vehicles where id=13').fetchone()
assert row and row[:6]==(13,0,0,11605.5,10293.5,0),row[:6] if row else None
with sqlite3.connect(backup) as b:c.backup(b)
sha=hashlib.sha256(row[6]).hexdigest()
expected=(math.floor(row[3]/8),math.floor(row[4]/8))
with c:
 n=c.execute('update vehicles set wx=?,wy=? where id=13 and wx=0 and wy=0 and x=11605.5 and y=10293.5',expected).rowcount
 assert n==1
updated=c.execute('select id,wx,wy,x,y,inMeta,data from vehicles where id=13').fetchone()
assert hashlib.sha256(updated[6]).hexdigest()==sha
assert c.execute('pragma quick_check').fetchone()[0]=='ok'
c.close()
report={'save':str(p.parent),'vehicle_sql_id':13,'before':list(row[:6]),'after':list(updated[:6]),'vehicle_blob_sha256_unchanged':sha,'backup':str(backup.resolve()),'scope':'Only wx and wy were repaired; no vehicle cloning, deletion, inventory or actor changes.'}
(out/'repair-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('Backed up database; repaired only vehicle 13 chunk index from (0,0) to',expected,'; vehicle blob unchanged; database integrity OK.')
