import os
import tempfile
import unittest
from streamlit.testing.v1 import AppTest

class UI(unittest.TestCase):
    def test_demo_search_and_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.environ['DATABASE_PATH']=tmp+'/ui.db'
            os.environ['STAFF_PASSWORD']='test-password-only-123'
            at=AppTest.from_file(os.path.abspath('app.py')).run(timeout=20)
            self.assertEqual(len(at.exception),0)
            next(b for b in at.button if b.label=='Load fictional sample reports').click().run()
            self.assertEqual(len(at.exception),0)
            next(t for t in at.text_area if t.label=='Description').set_value('blue water bottle near library').run()
            self.assertEqual(len(at.exception),0)
            self.assertTrue(any(x.value=='Navy flask' for x in at.subheader))
            next(t for t in at.text_input if t.label=='Your name').set_value('Test Student')
            next(t for t in at.text_input if t.label=='Your email or phone').set_value('demo@example.com')
            next(t for t in at.text_area if t.label=='Identifying detail and ownership evidence').set_value('star sticker beneath base')
            next(b for b in at.button if b.label=='Submit claim').click().run()
            self.assertEqual(len(at.exception),0)
            self.assertTrue(any('Claim submitted' in x.value for x in at.success))
            next(t for t in at.text_input if t.label=='Staff password').set_value('test-password-only-123').run()
            self.assertEqual(len(at.exception),0)
            self.assertTrue(any('star sticker beneath base' in x.value for x in at.text))

if __name__=='__main__':unittest.main()
