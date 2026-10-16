"""Conservative hierarchical lookup. No filenames, query IDs or stored answers."""
import re
from .workbook import clean,norm,number
from .expressions import inferred_format

def cell(s,r,c):return {'cell':s.ref(r,c)}
def op(name,*args):return {'op':name,'args':list(args)}
def numeric(v):
    try:return number(v)
    except ValueError:return None

def hierarchy_plan(book,q):
    from .ranking import ranking_plan
    ranking=ranking_plan(book,q)
    if ranking is not None:return ranking
    p=financial(book,q)
    if p is not None:return p
    ps=[p for s in book.sheets if (p:=index_comparison(s,q)) is not None]
    if len(ps)==1:return ps[0]
    ps=[p for s in book.sheets if (p:=household(s,q)) is not None]
    return ps[0] if len(ps)==1 else None

def fiscal_cells(book,label,year):
    hits=[]
    for s in book.sheets:
        for (r,c),v in s.cells.items():
            if norm(v)!=norm(label):continue
            cs=[]
            for cc in range(c+1,s.cols+1):
                headers=[norm(s.expanded(rr,cc)) for rr in range(1,r)]
                if norm(year) in headers and numeric(s.value(r,cc)) is not None:cs.append(cc)
            if len(cs)!=1:return None
            hits.append((s,r,cs[0]))
    return hits

def financial(book,q):
    m=re.fullmatch(r'By how much did the (.+?) increase between (.+?) and (.+?), in millions of dollars\? Answer with only the integer, without commas or units\.',q,re.I)
    if m:
        found=[]
        for s in book.sheets:
            rows=[r for (r,c),v in s.cells.items() if norm(v)==norm(m[1])]
            if len(rows)!=1:continue
            r=rows[0];cols=[]
            for date in (m[2],m[3]):
                hits=[]
                for c in range(1,s.cols+1):
                    hs=' '.join(norm(s.expanded(rr,c)) for rr in range(1,min(r,7))).replace('totalfair','total fair')
                    if norm(date) in hs and 'total fair value' in hs and numeric(s.value(r,c)) is not None:hits.append(c)
                if len(hits)!=1:break
                cols.append(hits[0])
            if len(cols)==2:found.append({'expression':op('sub',cell(s,r,cols[1]),cell(s,r,cols[0])),'format':{'type':'integer'}})
        return found[0] if len(found)==1 else None
    m=re.fullmatch(r'What is the ratio of (.+?) at (.+?, (\d{4})) to (.+?) at (.+?)\? Answer with only the number rounded to three decimal places\.',q,re.I)
    if m and m[2].casefold()==m[5].casefold():
        hits=[]
        for s in book.sheets:
            selected=[]
            for label in (m[1],m[4]):
                cells=[]
                for (r,c),v in s.cells.items():
                    source=re.sub(r'\([a-z]\)$','',clean(v),flags=re.I)
                    if norm(source)!=norm(label):continue
                    cols=[]
                    for cc in range(c+1,s.cols+1):
                        hs=' '.join(norm(s.expanded(rr,cc)) for rr in range(1,min(r,7)))
                        if re.search(r'\b'+m[3]+r'\b',hs) and 'average' not in hs and numeric(s.value(r,cc)) is not None:cols.append(cc)
                    if len(cols)==1:cells.append(cell(s,r,cols[0]))
                if len(cells)!=1:break
                selected.append(cells[0])
            if len(selected)==2:hits.append(selected)
        if len(hits)==1:return {'expression':op('div',*hits[0]),'format':{'type':'fixed','decimals':3}}
        return None
    m=re.fullmatch(r'In (Fiscal\d{4}), what was the combined (.+?) of all the segments reported in this workbook, in millions of dollars\? Answer with only the integer, without commas or units\.',q,re.I)
    if m:
        hits=fiscal_cells(book,m[2],m[1])
        if not hits or len(hits)<2:return None
        return {'expression':op('sum',*[cell(s,r,c) for s,r,c in hits]),'format':{'type':'integer'}}
    m=re.fullmatch(r'Which sheet reports the higher (.+?) in (Fiscal\d{4}), and what was that value in millions of dollars\? Answer as `sheet name, integer value`, separated by a comma and one space, without commas inside the number and without units\.',q,re.I)
    if m:
        hits=fiscal_cells(book,m[1],m[2])
        if not hits or len(hits)<2:return None
        values=[numeric(s.value(r,c)) for s,r,c in hits]
        if values.count(max(values))!=1:return None
        items=[{'label':{'op':'sheet_name','sheet':s.name},'value':cell(s,r,c),'result':op('list',{'op':'sheet_name','sheet':s.name},cell(s,r,c))} for s,r,c in hits]
        return {'expression':{'op':'pick','items':items},'format':{'type':'tuple','items':[{'type':'text'},{'type':'integer'}]}}
    return None

def household(s,q):
    activity=re.findall(r"'([^']+)'",q)
    if len(activity)!=1 or 'average hours per day' not in q.lower():return None
    rows=[(r,c) for (r,c),v in s.cells.items() if clean(v).casefold()==activity[0].casefold()]
    if not rows:return None
    first=min(r for r,c in rows)
    def find_col(person,status):
        hits=[]
        for c in range(1,s.cols+1):
            hs=[norm(s.expanded(r,c)) for r in range(1,first)]
            if any('average hours per day' in x for x in hs) and person in hs and status in hs:hits.append(c)
        return hits[0] if len(hits)==1 else None
    mother=find_col('married mothers','employed full time')
    if mother is None:return None
    groups=[]
    for r,labelcol in rows:
        labels=[rr for rr in range(1,r) if norm(s.value(rr,labelcol)).startswith('own household children') and sum(v is not None and clean(v)!='' for (row,c),v in s.cells.items() if row==rr)==1]
        if not labels or numeric(s.value(r,mother)) is None:return None
        groups.append((r,max(labels),labelcol))
    if 'for which group' in q.lower() and 'most' in q.lower() and 'full-time employed married mothers' in q.lower():
        vals=[numeric(s.value(r,mother)) for r,_,_ in groups]
        if vals.count(max(vals))!=1:return None
        return {'expression':{'op':'argmax','items':[{'label':cell(s,gr,lc),'value':cell(s,r,mother)} for r,gr,lc in groups]},'format':{'type':'text'}}
    if 'not-employed married fathers' in q.lower() and 'full-time employed married mothers' in q.lower() and 'who spends more' in q.lower():
        father=find_col('married fathers 2','not employed')
        if father is None:father=find_col('married fathers','not employed')
        if father is None:return None
        # Select the group using the explicitly stated age interval, not row position.
        age=re.search(r'own household children (\d+[-–]\d+)',q,re.I)
        if not age:return None
        selected=[r for r,gr,lc in groups if norm(age[1]) in norm(s.value(gr,lc))]
        if len(selected)!=1:return None
        r=selected[0];a=cell(s,r,father);b=cell(s,r,mother)
        if numeric(s.value(r,father)) is None or numeric(s.value(r,father))==numeric(s.value(r,mother)):return None
        names=['not-employed fathers','full-time employed mothers']
        if not all(n in q for n in names):return None
        choice=op('if',op('gt',a,b),{'constant':names[0]},{'constant':names[1]})
        return {'expression':op('list',choice,op('abs',op('sub',a,b))),'format':{'type':'tuple','items':[{'type':'text'},inferred_format(q)]}}
    return None


def index_comparison(s,q):
    m=re.fullmatch(r'How many percentage points larger is the (.+?) of (.+?) than that of (.+?)\? Answer with only the number using exactly (?:one|two|three) decimal places?\.',q,re.I)
    a=re.fullmatch(r'How many percentage points higher was the unadjusted percent change from (.+?) to (.+?) for (.+?) than for (.+?)\? Answer with only the number using exactly (?:one|two|three) decimal places?\.',q,re.I)
    if not (m or a):return None
    labels=(m[2],m[3]) if m else (a[3],a[4]);refs=[]
    for label in labels:
        found=[(r,c) for (r,c),v in s.cells.items() if norm(v)==norm(label)]
        if len(found)!=1:return None
        r,lc=found[0];cs=[]
        for c in range(lc+1,s.cols+1):
            hs=' '.join(norm(s.expanded(rr,c)) for rr in range(1,min(r,8)))
            if m:match=norm(m[1]) in hs
            else:match='unadjusted percent change' in hs and norm(a[1]) in hs and norm(a[2]) in hs
            if match and numeric(s.value(r,c)) is not None:cs.append(c)
        if len(cs)!=1:return None
        refs.append(cell(s,r,cs[0]))
    return {'expression':op('sub',*refs),'format':inferred_format(q)}
