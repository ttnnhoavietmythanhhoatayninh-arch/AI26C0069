"""Hierarchy and subgroup rankings calculated from source cells, never query IDs."""
import re
from .workbook import clean,norm,number

def ref(s,r,c):return {'cell':s.ref(r,c)}
def op(name,*args):return {'op':name,'args':list(args)}
def num(v):
    try:return number(v)
    except ValueError:return None

def ranking_plan(book,q):
    plans=[]
    for s in book.sheets:
        for fn in (direct_children,subgroup_increase):
            plan=fn(s,q)
            if plan is not None:plans.append(plan)
    return plans[0] if len(plans)==1 else None

def direct_children(s,q):
    m=re.fullmatch(r'Rank the categories directly under [“"\'](.+?)[”"\'] by their unadjusted percent change to (.+?) from (.+?), from (highest to lowest|lowest to highest)\. Answer with the category names in that order, separated by a comma and one space, without numbering\.',q,re.I)
    if not m:return None
    parents=[(r,c) for (r,c),v in s.cells.items() if norm(v)==norm(m[1])]
    levels=[(r,c) for (r,c),v in s.cells.items() if norm(v)=='indent level']
    if len(parents)!=1 or len(levels)!=1:return None
    pr,lc=parents[0];hr,ic=levels[0];depth=num(s.value(pr,ic))
    if depth is None:return None
    first=next((r for r in range(hr+1,s.rows+1) if num(s.value(r,ic)) is not None),pr)
    cols=[]
    for c in range(1,s.cols+1):
        hs=' '.join(norm(s.expanded(r,c)) for r in range(1,first))
        if 'unadjusted percent change' in hs and norm(m[2]) in hs and norm(m[3]) in hs:cols.append(c)
    if len(cols)!=1:return None
    vc=cols[0];rows=[]
    for r in range(pr+1,s.rows+1):
        level=num(s.value(r,ic))
        if level is None:continue
        if level<=depth:break
        if level==depth+1:
            if num(s.value(r,vc)) is None or not clean(s.value(r,lc)):return None
            rows.append(r)
    if not rows:return None
    return {'expression':{'op':'rank_labels','descending':m[4].lower()=='highest to lowest',
                          'items':[{'label':ref(s,r,lc),'value':ref(s,r,vc)} for r in rows]},'format':{'type':'text'}}

def subgroup_increase(s,q):
    m=re.fullmatch(r'Among (.+?) (women|men) aged (\d+) years and over, which group had the largest increase in the number of unemployed people from (\d{4}) to (\d{4}), and by how many thousand\? Answer as `group, increase`, separated by a comma and one space, with the increase as an integer\.',q,re.I)
    if not m:return None
    labels=[clean(x) for x in re.split(r',\s*|\s+and\s+',m[1]) if clean(x)]
    if len(labels)<2 or len({norm(x) for x in labels})!=len(labels):return None
    target=norm(f'{m[2]} {m[3]} years and over')
    sections=[(r,c) for (r,c),v in s.cells.items() if norm(v)==target]
    if len(sections)!=1:return None
    start,lc=sections[0];end=s.rows+1
    for r in range(start+1,s.rows+1):
        label=norm(s.value(r,lc))
        if re.match(r'^(?:men|women|both sexes)\b',label) or label=='total':end=r;break
    rows=[r for r in range(start+1,end) if norm(s.value(r,lc))=='unemployed']
    if len(rows)!=1:return None
    r=rows[0];items=[];changes=[]
    for label in labels:
        anchors=[(rr,c) for (rr,c),v in s.cells.items() if rr<start and norm(v)==norm(label)]
        if len(anchors)!=1:return None
        cols=[]
        for year in (m[4],m[5]):
            hits=[]
            for c in range(lc+1,s.cols+1):
                hs=[norm(s.expanded(rr,c)) for rr in range(1,start)]
                if norm(label) in hs and year in hs:hits.append(c)
            if len(hits)!=1 or num(s.value(r,hits[0])) is None:return None
            cols.append(hits[0])
        delta=op('sub',ref(s,r,cols[1]),ref(s,r,cols[0]))
        changes.append(num(s.value(r,cols[1]))-num(s.value(r,cols[0])))
        ar,ac=anchors[0];source_label=ref(s,ar,ac)
        items.append({'label':source_label,'value':delta,'result':op('list',source_label,delta)})
    if max(changes)<=0 or changes.count(max(changes))!=1:return None
    return {'expression':{'op':'pick','items':items,'descending':True},'format':{'type':'tuple','items':[{'type':'text'},{'type':'integer'}]}}
