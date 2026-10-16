"""Selectors for dated person records and explicitly scoped statistical tables.

All results are expressions over source cells. An unqualified age in a table
with Birth and Admission means elapsed age at that row's admission event.
"""
import re,datetime
from .workbook import norm,clean,number
from .semantics import ref,op,num,unique_col
from .expressions import inferred_format

def plan(book,query):
    q=norm(query);plans=[]
    for s in book.sheets:
        p=person(s,query)
        if p is None:p=statistics(s,query)
        if p is not None:plans.append(p)
    return plans[0] if len(plans)==1 else None

def person(s,query):
    q=norm(query)
    if not ('youngest' in q or 'oldest' in q):return None
    h={}
    for (r,c),v in s.cells.items():
        if norm(v) in ('birth','admission','last','score'):
            key=norm(v)
            if key in h:return None
            h[key]=(r,c)
    if not all(k in h for k in ('birth','admission','score')):return None
    # An explicit alternative reference date needs another selector.
    if re.search(r'\b(today|current|now|as of)\b',q):return None
    rows=[r for r in range(max(r for r,c in h.values())+1,s.rows+1) if all(isinstance(s.value(r,h[k][1]),(datetime.date,datetime.datetime)) for k in ('birth','admission'))]
    if not rows:return None
    words={'first':1,'second':2,'third':3,'fourth':4,'fifth':5,'two':2,'three':3,'four':4,'five':5,'ten':10}
    n=next((v for k,v in words.items() if re.search(r'\b'+k+r'\b',q)),None)
    if n is None:
        m=re.search(r'\b(\d+)\s+(?:youngest|oldest)',q);n=int(m[1]) if m else 1
    if not 1<=n<=len(rows):return None
    target='last' if 'last name' in q else 'score' if 'score' in q else None
    if target not in h:return None
    ages=[(s.value(r,h['admission'][1])-s.value(r,h['birth'][1])).days for r in rows]
    order=sorted(ages,reverse='oldest' in q)
    if n<len(order) and order[n-1]==order[n]:return None
    if not 'among' in q and order.count(order[n-1])>1:return None
    items=[{'label':ref(s,r,h[target][1]),'result':ref(s,r,h[target][1]),'value':op('days_between',ref(s,r,h['birth'][1]),ref(s,r,h['admission'][1]))} for r in rows]
    e={'op':'top_values' if 'among' in q else 'pick','items':items,'n':n,'descending':'oldest' in q}
    if 'among' in q:
        if 'highest score' in q:e=op('max',e)
        elif 'lowest score' in q:e=op('min',e)
        else:return None
    return {'expression':e,'format':inferred_format(query)}

def statistics(s,query):
    q=norm(query);fmt=inferred_format(query)
    def result(e):return {'expression':e,'format':fmt}
    if 'year to date' in q and ('greater than' in q or 'less than' in q):
        family='fiscal year to date' if 'fiscal year to date' in q else 'calendar year to date' if 'calendar year to date' in q else None
        years=re.findall(r'\b(?:19|20)\d{2}\b',q)
        if not family or len(years)!=2:return None
        candidates=[]
        for r in range(1,s.rows+1):
            label=norm(s.value(r,1))
            metric='agricultural exports' if 'agricultural export' in q else 'agricultural imports' if 'agricultural import' in q else None
            if label!=metric:continue
            # Nearest preceding year row defines this table's header block.
            yr=next((rr for rr in range(r-1,0,-1) if sum(bool(re.fullmatch(r'(?:19|20)\d{2}',clean(s.value(rr,c)))) for c in range(2,s.cols+1))>=2),None)
            if yr is None:continue
            cols=[]
            for y in years:
                hits=[c for c in range(2,s.cols+1) if clean(s.value(yr,c))==y and any(norm(s.expanded(rr,c))==family for rr in range(max(1,yr-3),yr))]
                if len(hits)!=1:break
                cols.append(hits[0])
            if len(cols)==2:candidates.append(op('lt' if 'less than' in q else 'gt',*[ref(s,r,c) for c in cols]))
        if len(candidates)==1:return result(candidates[0])
    if 'all categories' in q and 'absolute' in q and 'unadjusted percent change' in q:
        dates=re.findall(r'\b(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep|oct|nov(?:ember)?|dec(?:ember)?)\s+((?:19|20)\d{2})',q)
        if len(dates)!=2:return None
        lc=next((c for (r,c),v in s.cells.items() if norm(v)=='expenditure category'),None)
        if lc is None:return None
        cols=[]
        for c in range(1,s.cols+1):
            for r in range(1,s.rows+1):
                if norm(s.value(r,c))!='unadjusted percent change':continue
                h=norm(s.expanded(r+1,c))
                expected=' '.join(x for pair in dates for x in pair)
                if h==expected:cols.append(c)
        if len(cols)!=1:return None
        c=cols[0];rows=[r for r in range(1,s.rows+1) if clean(s.value(r,lc)) and num(s.value(r,c)) is not None]
        if not rows:return None
        values=[abs(number(s.value(r,c))) for r in rows]
        if values.count(max(values))!=1:return None
        return result({'op':'argmax','items':[{'label':ref(s,r,lc),'value':op('abs',ref(s,r,c))} for r in rows]})
    if 'number of persons at work' in q and 'hours' in q:
        m=re.search(r'\b(\d+) to (\d+) hours',q)
        if not m:return None
        rows=[r for r in range(1,s.rows+1) if norm(s.value(r,1))==f'{m[1]} to {m[2]} hours']
        if len(rows)!=1:return None
        r=rows[0];industry='Nonagricultural industries' if 'nonagricultural' in q else 'Agriculture and related industries' if re.search(r'\bagriculture\b',q) else 'All industries'
        c=unique_col(s,['Persons at work',industry],r)
        if c is not None:return result(ref(s,r,c))
    if 'average hours' in q and 'men and women' in q:
        starts=[r for r in range(1,s.rows+1) if norm(s.value(r,1))=='marital status']
        if len(starts)!=1:return None
        a=starts[0];c=unique_col(s,['Average hours','Total at work'],a)
        if c is None:return None
        group=None;hits={}
        for r in range(a+1,s.rows+1):
            label=norm(s.value(r,1))
            if label.startswith('men '):group='men'
            elif label.startswith('women '):group='women'
            elif group and label and all(t in q for t in label.split()) and num(s.value(r,c)) is not None:
                if group in hits:return None
                hits[group]=r
        if set(hits)=={'men','women'}:return result(op('list',*[ref(s,hits[g],c) for g in ('men','women')]))
    return None
