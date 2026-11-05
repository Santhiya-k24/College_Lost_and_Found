"""Transparent lexical demo and optional real neural embedding retrieval."""
import re
from functools import lru_cache

ALIASES={'navy':'blue','flask':'bottle','earphones':'earbuds','backpack':'bag','reading':'library'}
STOP={'a','an','the','i','my','lost','found','near','at','in','on','with','of','and','room'}
def tokens(text):
    return {ALIASES.get(w,w) for w in re.findall(r'[a-z0-9]+',text.lower()) if w not in STOP}

def text(row):
    return ' '.join(row[k] for k in ['title','category','description','location'])

@lru_cache(maxsize=1)
def encoder():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

def search(query, rows, mode='Demo', limit=5, minimum=0.15):
    if not rows or not query.strip(): return []
    if mode=='Semantic':
        import numpy as np
        import faiss
        model=encoder()
        vectors=np.asarray(model.encode([text(r) for r in rows],normalize_embeddings=True),dtype='float32')
        q=np.asarray(model.encode([query],normalize_embeddings=True),dtype='float32')
        index=faiss.IndexFlatIP(vectors.shape[1]); index.add(vectors)
        scores,indices=index.search(q,min(limit,len(rows)))
        results=[(rows[int(i)],float(s)) for s,i in zip(scores[0],indices[0])]
    else:
        q=tokens(query)
        results=[]
        for r in rows:
            t=tokens(text(r)); score=len(q&t)/max(len(q|t),1)
            results.append((r,score))
        results=sorted(results,key=lambda pair:pair[1],reverse=True)[:limit]
    return [(r,round(s,3)) for r,s in results if s>=minimum]
