#!/usr/bin/env python3
"""V127 cache-only transcript archive schema/path audit.

Discovery-only. No labels and no model fitting. Inspects every CSV member name and
header in the frozen transcript ZIP to determine whether process/provider/schema
metadata exists below the loader abstraction. Also inspects a deterministic small
sample for role and non-content field vocabularies. No transcript corpus mutation.
"""
from __future__ import annotations
import argparse, csv, io, json, re, zipfile, hashlib
from collections import Counter, defaultdict
from pathlib import PurePosixPath, Path

REQUIRED=("session_id","utterance_id","role","content","timestamp")

def stable(s): return hashlib.sha256(s.encode()).hexdigest()

def shape(v):
    s=str(v or '')
    s=re.sub(r'[0-9]','#',s); s=re.sub(r'[A-Fa-f]','a',s)
    return s[:80]

def main(a):
    z=zipfile.ZipFile(a.archive)
    members=[n for n in z.namelist() if n.lower().endswith('.csv') and not n.endswith('/')]
    headers=Counter(); path_depth=Counter(); topdirs=Counter(); second=Counter(); extras=Counter(); bad=[]
    member_records=[]
    for n in members:
        p=PurePosixPath(n); path_depth[len(p.parts)]+=1
        if p.parts: topdirs[p.parts[0]]+=1
        if len(p.parts)>1: second['/'.join(p.parts[:2])]+=1
        try:
            with z.open(n) as f:
                first=io.TextIOWrapper(f,encoding='utf-8-sig',newline='').readline()
            h=tuple(next(csv.reader([first]))) if first else tuple()
        except Exception as e:
            bad.append({'member':n,'error':repr(e)}); continue
        headers[h]+=1
        for c in h:
            if c not in REQUIRED: extras[c]+=1
        member_records.append((stable(n),n,h))
    member_records.sort()
    sample=member_records[:min(a.sample,len(member_records))]
    role_values=Counter(); noncontent_values=defaultdict(Counter); timestamp_shapes=Counter(); utterance_shapes=Counter(); sid_shapes=Counter()
    sampled_rows=0
    for _,n,h in sample:
        try:
            with z.open(n) as f:
                t=io.TextIOWrapper(f,encoding='utf-8-sig',newline='')
                r=csv.DictReader(t)
                for j,row in enumerate(r):
                    sampled_rows+=1
                    role_values[str(row.get('role',''))]+=1
                    timestamp_shapes[shape(row.get('timestamp',''))]+=1
                    utterance_shapes[shape(row.get('utterance_id',''))]+=1
                    sid_shapes[shape(row.get('session_id',''))]+=1
                    for c in h:
                        if c not in ('content',):
                            v=str(row.get(c,''))
                            if len(noncontent_values[c])<200 or v in noncontent_values[c]: noncontent_values[c][v]+=1
                    if j+1>=a.rows_per_file: break
        except Exception as e:
            bad.append({'member':n,'sample_error':repr(e)})
    out={
      'protocol':'V127_TRANSCRIPT_SCHEMA_PATH_AUDIT','archive':str(a.archive),
      'csv_members':len(members),'bad_members':bad[:20],
      'header_signatures':[{'columns':list(k),'count':v,'missing_required':sorted(set(REQUIRED)-set(k)),'extra_columns':sorted(set(k)-set(REQUIRED))} for k,v in headers.most_common()],
      'extra_column_presence':dict(extras.most_common()),
      'path_depths':dict(path_depth),'top_level_paths':topdirs.most_common(30),'second_level_paths':second.most_common(30),
      'sample':{'files':len(sample),'rows':sampled_rows,'roles':role_values.most_common(30),
                'timestamp_shapes':timestamp_shapes.most_common(20),'utterance_id_shapes':utterance_shapes.most_common(20),'session_id_shapes':sid_shapes.most_common(20),
                'noncontent_unique_counts':{c:len(v) for c,v in noncontent_values.items()},
                'noncontent_top_values':{c:v.most_common(20) for c,v in noncontent_values.items() if c not in ('content',)}},
      'decision':{}
    }
    any_extra=bool(extras); schema_variants=len(headers)>1; path_variants=len(second)>1 or len(topdirs)>1
    if any_extra:
        verdict='EXPLICIT_EXTRA_METADATA_PRESENT'
    elif schema_variants:
        verdict='SCHEMA_VARIANTS_PRESENT'
    elif path_variants:
        verdict='PATH_FAMILY_PRESENT'
    else:
        verdict='NO_EXPLICIT_PROVIDER_SCHEMA_CHANNEL'
    out['decision']={'verdict':verdict,'any_extra_columns':any_extra,'header_signature_count':len(headers),'top_level_path_count':len(topdirs),'second_level_path_count':len(second)}
    Path(a.out).write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--archive',required=True); p.add_argument('--sample',type=int,default=256); p.add_argument('--rows-per-file',type=int,default=20); p.add_argument('--out',required=True); main(p.parse_args())
