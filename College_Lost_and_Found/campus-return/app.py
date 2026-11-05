import os
import hmac
from datetime import date
import streamlit as st
from core import connect,add_report,public_reports,claim,track,decide,seed,CATEGORIES
from matching import search

st.set_page_config(page_title='Campus Return',page_icon='🔎',layout='wide')
st.markdown('''<style>.stApp{background:#f7f9fc} h1,h2,h3{color:#15354b} div[data-testid="stMetric"]{background:white;border-radius:12px;padding:16px;border:1px solid #e1e7ef}</style>''',unsafe_allow_html=True)
st.caption('CAMPUS RETURN / LOST & FOUND')
st.title('A small detail. A happy reunion.')
st.write('Report an item, find possible matches, and let staff verify the handover.')
@st.cache_resource
def db_path(): return os.getenv('DATABASE_PATH','data/campus.db')
c=connect(db_path())
with st.sidebar:
    st.header('Workspace')
    mode=st.selectbox('Matching engine',['Demo','Semantic'])
    st.caption('Demo: offline keyword matching with a small synonym list. Semantic: neural embeddings + FAISS; installs and model download required.')
    llm=st.toggle('Enable local LLM',value=False)
    st.caption('Requires Ollama + AI dependencies. Public descriptions are sent to the configured Ollama server. Private details and contacts are excluded.')
    if st.button('Load fictional sample reports'):
        st.info('Sample reports loaded.' if seed(c) else 'Database already has reports; no samples added.')
rows=public_reports(c)
a,b,d=st.columns(3)
a.metric('Open found items',sum(r['kind']=='Found' for r in rows))
b.metric('Open lost reports',sum(r['kind']=='Lost' for r in rows))
d.metric('Returned items',c.execute("SELECT count(*) FROM reports WHERE status='Returned'").fetchone()[0])
find,report,tracking,staff=st.tabs(['Find a match','Report an item','Track a claim','Staff desk'])
with find:
    st.subheader('Describe what you lost')
    query=st.text_area('Description',placeholder='Blue water bottle near the library',max_chars=2000)
    cat=st.selectbox('Category',['All']+CATEGORIES)
    threshold=st.slider('Minimum similarity (not ownership probability)',0.0,1.0,0.15,0.05)
    if llm and st.button('Help me add missing details'):
        if query.strip():
            try:
                from assistant import clarify
                info=clarify(query)
                st.json({k:v for k,v in info.items() if k!='questions'})
                for q in info['questions'][:3]: st.write('• '+q)
            except Exception:
                st.error('LLM unavailable. Check Ollama, model and AI dependencies. You can still search normally.')
    matches=[]
    if query.strip():
        try:
            with st.spinner('Finding possible matches…'):
                matches=search(query,public_reports(c,'Found',cat),mode,minimum=threshold)
        except Exception:
            st.error('Semantic engine unavailable. Install AI dependencies and allow the first model download, or select Demo.')
        if not matches: st.info('No matches above the selected threshold. Try a broader description or submit a lost report.')
        for r,score in matches:
            with st.container(border=True):
                st.subheader(r['title'])
                st.caption(f"Report {r['id']} · {r['category']} · {r['location']} · {r['event_date']}")
                st.write(r['description'])
                st.write(f'Similarity score: {score:.3f} · Suggested match only')
                with st.expander('Request staff verification'):
                    st.caption('Describe a hidden identifying detail. Do not enter passwords, PINs or identity document numbers.')
                    with st.form('claim_'+r['id']):
                        name=st.text_input('Your name',max_chars=100)
                        contact=st.text_input('Your email or phone',max_chars=200)
                        evidence=st.text_area('Identifying detail and ownership evidence',max_chars=2000)
                        if st.form_submit_button('Submit claim'):
                            try:
                                token=claim(c,r['id'],name,contact,evidence)
                                st.success('Claim submitted. Keep this private tracking token; it is shown only here.')
                                st.code(token)
                            except ValueError as e: st.error(str(e))
        if llm and matches and st.button('Explain these possible matches'):
            try:
                from assistant import explain
                st.write(explain(query,matches))
                st.caption('LLM explanation may be inaccurate. Check report details; staff decide ownership.')
            except Exception: st.error('LLM unavailable. Matching results above remain usable.')
with report:
    st.subheader('Record a lost or found item')
    st.info('Public description: general appearance only. Put stickers, engravings and other distinguishing marks in the private field.')
    with st.form('report',clear_on_submit=True):
        kind=st.radio('Report type',['Lost','Found'],horizontal=True)
        title=st.text_input('Short title',max_chars=120)
        category=st.selectbox('Item category',CATEGORIES)
        description=st.text_area('Public description',max_chars=2000)
        location=st.text_input('Location',max_chars=200)
        when=st.date_input('Date lost / found',max_value=date.today())
        detail=st.text_area('Private identifying detail (staff only)',max_chars=2000)
        contact=st.text_input('Your contact (staff only)',max_chars=200)
        if st.form_submit_button('Save report'):
            try:
                rid=add_report(c,kind,title,category,description,location,when.isoformat(),detail,contact)
                st.success('Saved report '+rid)
            except ValueError as e: st.error(str(e))
with tracking:
    token=st.text_input('Private claim tracking token',type='password')
    if st.button('Check status'):
        result=track(c,token)
        if result:
            st.write(result['title']);st.info(result['status']);st.write(result['note'])
        else: st.warning('Token not recognised.')
with staff:
    st.subheader('Staff review')
    password=os.getenv('STAFF_PASSWORD','')
    if len(password)<12:
        st.warning('Staff review disabled. Configure STAFF_PASSWORD with at least 12 characters, then restart.')
    else:
        entered=st.text_input('Staff password',type='password')
        if entered and hmac.compare_digest(entered.encode(),password.encode()):
            st.caption('Compare evidence independently before approval. Approval marks the item returned and closes competing pending claims. Arrange physical handover before confirming.')
            pending=c.execute("SELECT claims.*,reports.title,reports.private_detail,reports.contact AS finder_contact FROM claims JOIN reports ON reports.id=claims.report_id WHERE claims.status='Pending'").fetchall()
            if not pending: st.info('No pending claims.')
            for row in pending:
                r=dict(row)
                with st.expander(r['title']+' / '+r['id']):
                    for label,key in [('Claimant','name'),('Contact','contact'),('Claim evidence','evidence'),('Recorded private detail','private_detail'),('Finder contact','finder_contact')]:
                        st.write(label+':');st.text(r[key])
                    with st.form('review_'+r['id']):
                        note=st.text_area('Message to claimant',max_chars=2000)
                        action=st.radio('Decision',['Reject','Approve and mark returned'])
                        confirmed=st.checkbox('I checked the evidence and confirmed the handover if approving')
                        if st.form_submit_button('Record decision'):
                            if not confirmed: st.warning('Confirm your review first.')
                            else:
                                try: decide(c,r['id'],action.startswith('Approve'),note);st.rerun()
                                except ValueError as e: st.error(str(e))
        elif entered: st.error('Incorrect password.')
c.close()
