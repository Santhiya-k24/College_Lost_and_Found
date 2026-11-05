import unittest
import tempfile
from pathlib import Path
from core import connect,add_report,public_reports,claim,track,decide,seed
from matching import search

class Workflow(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.c=connect(str(Path(self.tmp.name)/'test.db'))
        self.rid=add_report(self.c,'Found','Navy flask','Bottle','Blue insulated water bottle','Library','2026-11-05','SECRET star sticker','PRIVATE@example.com')
    def tearDown(self):
        self.c.close();self.tmp.cleanup()
    def test_public_projection_and_search_privacy(self):
        rows=public_reports(self.c,'Found')
        self.assertNotIn('private_detail',rows[0]);self.assertNotIn('contact',rows[0])
        self.assertEqual(search('navy flask library',rows)[0][0]['id'],self.rid)
        self.assertEqual(search('SECRET',rows),[])
    def test_claim_tracking_and_competing_claims(self):
        a=claim(self.c,self.rid,'A','a@example.com','star sticker')
        b=claim(self.c,self.rid,'B','b@example.com','red mark')
        self.assertEqual(track(self.c,a)['status'],'Pending')
        cid=self.c.execute('SELECT id FROM claims WHERE name=?',('A',)).fetchone()[0]
        decide(self.c,cid,True,'Collected at desk')
        self.assertEqual(track(self.c,a)['status'],'Approved')
        self.assertEqual(track(self.c,b)['status'],'Closed')
        self.assertEqual(public_reports(self.c),[])
        with self.assertRaises(ValueError):claim(self.c,self.rid,'C','c','detail')
        with self.assertRaises(ValueError):decide(self.c,cid,True,'again')
        self.assertIsNone(track(self.c,'bad token'))
    def test_rejection_keeps_item_open(self):
        t=claim(self.c,self.rid,'A','a','detail')
        cid=self.c.execute('SELECT id FROM claims').fetchone()[0]
        decide(self.c,cid,False,'Please provide more evidence')
        self.assertEqual(track(self.c,t)['status'],'Rejected')
        self.assertEqual(len(public_reports(self.c)),1)
    def test_validation_and_filters(self):
        with self.assertRaises(ValueError):claim(self.c,self.rid,'','a','d')
        with self.assertRaises(ValueError):add_report(self.c,'bad','x','Bottle','d','l','date','p','c')
        self.assertEqual(public_reports(self.c,'Lost'),[])
        self.assertEqual(public_reports(self.c,'Found','Keys'),[])
        self.assertFalse(seed(self.c))
    def test_sql_injection_is_data(self):
        claim(self.c,self.rid,"'; DROP TABLE reports;--",'a','evidence')
        self.assertEqual(len(public_reports(self.c)),1)
    def test_no_results(self):
        self.assertEqual(search('anything',[]),[])
        self.assertEqual(search('',public_reports(self.c)),[])

if __name__=='__main__':unittest.main()
