"""Storage and workflow. Only public columns enter search or LLM prompts."""
import sqlite3
import secrets
import hashlib
from pathlib import Path

PUBLIC = 'id,kind,title,category,description,location,event_date,status'
CATEGORIES = ['Bottle', 'Electronics', 'Keys', 'Bag', 'Book', 'Clothing', 'Other']

def connect(path='data/campus.db'):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(path, timeout=15)
    c.row_factory = sqlite3.Row
    c.execute('PRAGMA foreign_keys=ON')
    c.executescript('''
    CREATE TABLE IF NOT EXISTS reports (
      id TEXT PRIMARY KEY, kind TEXT NOT NULL, title TEXT NOT NULL,
      category TEXT NOT NULL, description TEXT NOT NULL, location TEXT NOT NULL,
      event_date TEXT NOT NULL, private_detail TEXT NOT NULL, contact TEXT NOT NULL,
      status TEXT NOT NULL DEFAULT 'Open');
    CREATE TABLE IF NOT EXISTS claims (
      id TEXT PRIMARY KEY, report_id TEXT NOT NULL REFERENCES reports(id),
      name TEXT NOT NULL, contact TEXT NOT NULL, evidence TEXT NOT NULL,
      token_hash TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'Pending',
      note TEXT NOT NULL DEFAULT '');
    ''')
    return c

def add_report(c, kind, title, category, description, location, event_date, private_detail, contact):
    if kind not in ['Lost','Found'] or category not in CATEGORIES:
        raise ValueError('Invalid report type or category')
    vals = [str(v).strip() for v in [title,description,location,event_date,private_detail,contact]]
    if any(not v for v in vals) or any(len(v)>2000 for v in vals):
        raise ValueError('Complete all fields (maximum 2000 characters each)')
    rid=secrets.token_hex(6)
    with c:
        c.execute('INSERT INTO reports VALUES (?,?,?,?,?,?,?,?,?,?)',
                  (rid,kind,vals[0],category,vals[1],vals[2],vals[3],vals[4],vals[5],'Open'))
    return rid

def public_reports(c, kind=None, category=None):
    sql=f'SELECT {PUBLIC} FROM reports WHERE status=?'
    args=['Open']
    if kind:
        sql+=' AND kind=?'; args.append(kind)
    if category and category!='All':
        sql+=' AND category=?'; args.append(category)
    return [dict(r) for r in c.execute(sql+' ORDER BY event_date DESC',args)]

def claim(c, report_id, name, contact, evidence):
    if any(not v.strip() or len(v)>2000 for v in [name,contact,evidence]):
        raise ValueError('Complete all claim fields (maximum 2000 characters)')
    token=secrets.token_urlsafe(24); cid=secrets.token_hex(6)
    with c:
        row=c.execute("SELECT id FROM reports WHERE id=? AND kind='Found' AND status='Open'",(report_id,)).fetchone()
        if not row: raise ValueError('This item is no longer available for claims')
        c.execute('INSERT INTO claims (id,report_id,name,contact,evidence,token_hash) VALUES (?,?,?,?,?,?)',
                  (cid,report_id,name.strip(),contact.strip(),evidence.strip(),hashlib.sha256(token.encode()).hexdigest()))
    return token

def track(c, token):
    row=c.execute('SELECT claims.status,claims.note,reports.title FROM claims JOIN reports ON reports.id=claims.report_id WHERE token_hash=?',
                  (hashlib.sha256(token.encode()).hexdigest(),)).fetchone()
    return dict(row) if row else None

def decide(c, claim_id, approve, note):
    with c:
        # Serialize competing staff decisions before checking current status.
        c.execute('BEGIN IMMEDIATE')
        row=c.execute('SELECT * FROM claims WHERE id=?',(claim_id,)).fetchone()
        if not row or row['status']!='Pending': raise ValueError('Claim already reviewed or missing')
        if approve:
            result=c.execute("UPDATE reports SET status='Returned' WHERE id=? AND status='Open'",(row['report_id'],))
            if result.rowcount!=1: raise ValueError('Item already returned')
            c.execute("UPDATE claims SET status='Closed',note='Another claim was approved.' WHERE report_id=? AND id!=? AND status='Pending'",(row['report_id'],claim_id))
        c.execute('UPDATE claims SET status=?,note=? WHERE id=?',('Approved' if approve else 'Rejected',note[:2000],claim_id))

def seed(c):
    if c.execute('SELECT COUNT(*) FROM reports').fetchone()[0]: return False
    samples=[('Navy flask','Bottle','Navy blue insulated water flask','Library reading room','star sticker beneath base'),('Black earbuds case','Electronics','Black wireless earphones in charging case','Canteen','initials inside lid'),('Silver keyring','Keys','Three keys on a silver ring','Sports ground','tiny green turtle charm'),('Grey backpack','Bag','Grey laptop bag with two compartments','Computer lab','red lining in front pocket')]
    for title,cat,desc,loc,detail in samples:
        add_report(c,'Found',title,cat,desc,loc,'2026-11-05',detail,'Demo staff desk')
    return True
