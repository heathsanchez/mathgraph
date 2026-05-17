#!/usr/bin/env python
from __future__ import annotations
import sys
from pathlib import Path

try:
    from _bootstrap import ensure_repo_root_on_path
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
else:
    ensure_repo_root_on_path(__file__)

import argparse,json,sys
from pathlib import Path
from mathgraph.api_service import *
from mathgraph.lawbook import LawbookEntry
def main(argv=None):
 p=argparse.ArgumentParser(); p.add_argument("--route",default="health"); p.add_argument("--payload-json"); p.add_argument("--input-text",action="append",default=[]); p.add_argument("--query"); p.add_argument("--source"); p.add_argument("--target"); p.add_argument("--lawbook-entry-json",action="append",default=[]); p.add_argument("--lawbook-entries-jsonl"); p.add_argument("--out-response-json"); p.add_argument("--out-health-json"); p.add_argument("--serve",action="store_true"); p.add_argument("--host",default="127.0.0.1"); p.add_argument("--port",type=int,default=8765); p.add_argument("--fail-on-critical",action="store_true"); a=p.parse_args(argv)
 entries=[LawbookEntry.from_json(Path(x).read_text()) for x in a.lawbook_entry_json]+_jl(a.lawbook_entries_jsonl,LawbookEntry); state=ApiServiceState(accepted_lawbook_entries=entries)
 if a.serve:
  srv=serve_localhost(a.host,a.port,state); srv.serve_forever(); return 0
 payload=json.loads(Path(a.payload_json).read_text()) if a.payload_json else {}; 
 if a.input_text: payload["texts"]=a.input_text
 if a.query: payload["query_text"]=a.query
 if a.source: payload["source"]=a.source
 if a.target: payload["target"]=a.target
 route=ApiRoute[a.route.upper().replace("-","_")] if a.route.upper().replace("-","_") in ApiRoute.__members__ else ApiRoute.UNKNOWN
 resp=MathGraphLocalClient(state).request(ApiRequest(make_api_request_id(route.value,payload),route,payload=payload))
 if a.out_response_json: Path(a.out_response_json).write_text(resp.to_json())
 if a.out_health_json and resp.health: Path(a.out_health_json).write_text(resp.health.to_json())
 if not a.out_response_json and not a.out_health_json: sys.stdout.write(resp.to_json()+"\n")
 return 1 if a.fail_on_critical and audit_api_response(resp) else 0
def _jl(p,c):
 if not p:return []
 return [c.from_dict(json.loads(x)) for x in Path(p).read_text().splitlines() if x.strip()]
if __name__=="__main__": raise SystemExit(main())
