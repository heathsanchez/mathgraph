#!/usr/bin/env python3
import json, sys, pathlib
ROOT=pathlib.Path(sys.argv[1]).resolve()
sys.path.insert(0,str(ROOT))
from judge.verify import verify_answer
DEFAULT_PROOF_POLICY={
 'allowed_axioms':['propext','Quot.sound','Classical.choice'],
 'allowed_declarations':['letFun'],
 'allowed_declaration_prefixes':['And.','Bool.','Classical.','Decidable.','Eq.','EquationLHS','EquationRHS','Goal','Exists.','False.','Fin.','Fintype.','Function.','HEq.','Iff.','Init.','Int.','Lean.','List.','Magma.','Mathlib.','MemoFinOp.','Nat.','Nonempty.','Not.','NthRewrites.','OfNat.','Option.','Or.','Prod.','PUnit.','RewriteCombinations.','RewriteGoal.','RewriteHypothesis.','RewriteHypothesisAndGoal.','SimpleRewrites.','Std.','Subgraph.','Subtype.','Sum.','Trans.','True.','Unit.','JudgeDecide.','JudgeFinOp.','JudgeMagma.','inst','of_decide_','submission.','congrArg','congr_arg','eq_self','of_eq_true','id','eq_comm','eq_mp','eq_mpr','rfl','absurd']}
ids_tables = [('hard1_0005', [[2, 5, 7, 0, 4, 3, 1, 6], [0, 7, 5, 2, 6, 1, 3, 4], [4, 3, 1, 6, 2, 5, 7, 0], [6, 1, 3, 4, 0, 7, 5, 2], [3, 4, 6, 1, 5, 2, 0, 7], [1, 6, 4, 3, 7, 0, 2, 5], [5, 2, 0, 7, 3, 4, 6, 1], [7, 0, 2, 5, 1, 6, 4, 3]]), ('hard1_0062', [[0, 6, 1, 7, 5, 3, 4, 2], [5, 3, 4, 2, 0, 6, 1, 7], [4, 2, 5, 3, 1, 7, 0, 6], [1, 7, 0, 6, 4, 2, 5, 3], [7, 1, 6, 0, 2, 4, 3, 5], [2, 4, 3, 5, 7, 1, 6, 0], [3, 5, 2, 4, 6, 0, 7, 1], [6, 0, 7, 1, 3, 5, 2, 4]]), ('hard2_0009', [[2, 4, 5, 3, 0, 6, 7, 1], [6, 0, 1, 7, 4, 2, 3, 5], [3, 5, 4, 2, 1, 7, 6, 0], [7, 1, 0, 6, 5, 3, 2, 4], [1, 7, 6, 0, 3, 5, 4, 2], [5, 3, 2, 4, 7, 1, 0, 6], [0, 6, 7, 1, 2, 4, 5, 3], [4, 2, 3, 5, 6, 0, 1, 7]]), ('hard2_0012', [[0, 4, 1, 5, 6, 2, 7, 3], [5, 1, 4, 0, 3, 7, 2, 6], [3, 7, 2, 6, 5, 1, 4, 0], [6, 2, 7, 3, 0, 4, 1, 5], [2, 6, 3, 7, 4, 0, 5, 1], [7, 3, 6, 2, 1, 5, 0, 4], [1, 5, 0, 4, 7, 3, 6, 2], [4, 0, 5, 1, 2, 6, 3, 7]]), ('hard2_0064', [[6, 5, 0, 3, 7, 4, 1, 2], [1, 2, 7, 4, 0, 3, 6, 5], [5, 6, 3, 0, 4, 7, 2, 1], [2, 1, 4, 7, 3, 0, 5, 6], [0, 3, 6, 5, 1, 2, 7, 4], [7, 4, 1, 2, 6, 5, 0, 3], [3, 0, 5, 6, 2, 1, 4, 7], [4, 7, 2, 1, 5, 6, 3, 0]]), ('hard2_0067', [[1, 4, 5, 0, 2, 7, 6, 3], [6, 3, 2, 7, 5, 0, 1, 4], [0, 5, 4, 1, 3, 6, 7, 2], [7, 2, 3, 6, 4, 1, 0, 5], [4, 1, 0, 5, 7, 2, 3, 6], [3, 6, 7, 2, 0, 5, 4, 1], [5, 0, 1, 4, 6, 3, 2, 7], [2, 7, 6, 3, 1, 4, 5, 0]]), ('hard2_0123', [[6, 0, 5, 3, 1, 7, 2, 4], [5, 3, 6, 0, 2, 4, 1, 7], [2, 4, 1, 7, 5, 3, 6, 0], [1, 7, 2, 4, 6, 0, 5, 3], [7, 1, 4, 2, 0, 6, 3, 5], [4, 2, 7, 1, 3, 5, 0, 6], [3, 5, 0, 6, 4, 2, 7, 1], [0, 6, 3, 5, 7, 1, 4, 2]]), ('hard2_0133', [[2, 0, 4, 6, 3, 1, 5, 7], [5, 7, 3, 1, 4, 6, 2, 0], [7, 5, 1, 3, 6, 4, 0, 2], [0, 2, 6, 4, 1, 3, 7, 5], [4, 6, 2, 0, 5, 7, 3, 1], [3, 1, 5, 7, 2, 0, 4, 6], [1, 3, 7, 5, 0, 2, 6, 4], [6, 4, 0, 2, 7, 5, 1, 3]]), ('hard2_0165', [[5, 2, 6, 1, 3, 4, 0, 7], [6, 1, 5, 2, 0, 7, 3, 4], [3, 4, 0, 7, 5, 2, 6, 1], [0, 7, 3, 4, 6, 1, 5, 2], [4, 3, 7, 0, 2, 5, 1, 6], [7, 0, 4, 3, 1, 6, 2, 5], [2, 5, 1, 6, 4, 3, 7, 0], [1, 6, 2, 5, 7, 0, 4, 3]]), ('hard2_0169', [[7, 1, 4, 5, 2, 3, 6, 0], [1, 7, 5, 4, 3, 2, 0, 6], [3, 2, 0, 6, 1, 7, 5, 4], [2, 3, 6, 0, 7, 1, 4, 5], [5, 4, 1, 7, 0, 6, 3, 2], [4, 5, 7, 1, 6, 0, 2, 3], [6, 0, 2, 3, 4, 5, 7, 1], [0, 6, 3, 2, 5, 4, 1, 7]]), ('hard2_0175', [[5, 0, 6, 3, 7, 2, 4, 1], [6, 3, 5, 0, 4, 1, 7, 2], [2, 7, 1, 4, 0, 5, 3, 6], [1, 4, 2, 7, 3, 6, 0, 5], [0, 5, 3, 6, 2, 7, 1, 4], [3, 6, 0, 5, 1, 4, 2, 7], [7, 2, 4, 1, 5, 0, 6, 3], [4, 1, 7, 2, 6, 3, 5, 0]]), ('normal_0758', [[6, 1, 7, 0, 5, 2, 4, 3], [2, 5, 3, 4, 1, 6, 0, 7], [3, 4, 2, 5, 0, 7, 1, 6], [7, 0, 6, 1, 4, 3, 5, 2], [4, 3, 5, 2, 7, 0, 6, 1], [0, 7, 1, 6, 3, 4, 2, 5], [1, 6, 0, 7, 2, 5, 3, 4], [5, 2, 4, 3, 6, 1, 7, 0]])]
problems={}
for name in ('normal','hard1','hard2'):
    p=ROOT/'examples'/'problems'/(name+'.jsonl')
    for line in p.read_text().splitlines():
        if line.strip():
            r=json.loads(line); problems[r['id']]=r
results=[]
for pid,table in ids_tables:
    if pid not in problems: raise KeyError(pid)
    tbl=json.dumps(table,separators=(',',':'))
    code=(
        'import JudgeProblem\n'
        'import JudgeDecide.DecideBang\n'
        'import JudgeFinOp.MemoFinOp\n'
        'open MemoFinOp\n\n'
        'set_option maxRecDepth 100000 in\n'
        'def submission : Goal := by\n'
        '  let m : Magma (Fin 8) := {\n'
        f'    op := finOpTable {json.dumps(tbl)}\n'
        '  }\n'
        '  refine ⟨Fin 8, m, ?_⟩\n'
        '  decideFin!\n'
    )
    judge_problem={k:problems[pid][k] for k in ('id','eq1_id','eq2_id','equation1','equation2')}
    judge_problem['proof_policy']=DEFAULT_PROOF_POLICY
    raw=json.dumps({'verdict':'false','code':code})
    res=verify_answer(judge_problem,raw)
    item={'id':pid,'status':res['status'],'error_code':res['error_code'],'message':res['message'],'axioms':res.get('axioms',[]),'direct_declarations':res.get('direct_declarations',[]),'code':code}
    results.append(item)
    print(pid,res['status'],res['error_code'], flush=True)
    if res['status']!='accepted':
        print(res.get('stderr',''), flush=True); print(res.get('stdout',''), flush=True)
out=pathlib.Path('paper_final_lean_results.json'); out.write_text(json.dumps(results,indent=2))
print('SUMMARY',sum(r['status']=='accepted' for r in results),'/',len(results), flush=True)
if not all(r['status']=='accepted' for r in results): raise SystemExit(1)
