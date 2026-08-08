#!/usr/bin/env python3
import json, sys, pathlib
ROOT=pathlib.Path(sys.argv[1]).resolve(); sys.path.insert(0,str(ROOT))
from judge.verify import verify_answer
DEFAULT_PROOF_POLICY={
 'allowed_axioms':['propext','Quot.sound','Classical.choice'],
 'allowed_declarations':['letFun'],
 'allowed_declaration_prefixes':['And.','Bool.','Classical.','Decidable.','Eq.','EquationLHS','EquationRHS','Goal','Exists.','False.','Fin.','Fintype.','Function.','HEq.','Iff.','Init.','Int.','Lean.','List.','Magma.','Mathlib.','MemoFinOp.','Nat.','Nonempty.','Not.','NthRewrites.','OfNat.','Option.','Or.','Prod.','PUnit.','RewriteCombinations.','RewriteGoal.','RewriteHypothesis.','RewriteHypothesisAndGoal.','SimpleRewrites.','Std.','Subgraph.','Subtype.','Sum.','Trans.','True.','Unit.','JudgeDecide.','JudgeFinOp.','JudgeMagma.','inst','of_decide_','submission.','congrArg','congr_arg','eq_self','of_eq_true','id','eq_comm','eq_mp','eq_mpr','rfl','absurd']}

def make_table(beta,gamma):
    gi=[0]*8
    for i,v in enumerate(gamma): gi[v]=i
    return [[gi[x ^ beta[y]] for y in range(8)] for x in range(8)]
A=make_table([0,2,4,6,3,1,7,5],[0,3,6,5,7,4,1,2])
B=make_table([0,2,4,6,3,1,7,5],[0,7,5,2,1,6,4,3])
C=make_table([0,1,2,3,5,4,7,6],[0,1,2,3,6,7,5,4])
groups={
 'A':['hard1_0005','hard2_0012','hard2_0064','hard2_0123','hard2_0175'],
 'B':['hard1_0062','hard2_0009','hard2_0067','hard2_0133','hard2_0165','normal_0758'],
 'C':['hard2_0169']}
tables={'A':A,'B':B,'C':C}
ids_tables=[]
for label,ids in groups.items():
    for pid in ids: ids_tables.append((pid,label,tables[label]))
problems={}
for name in ('normal','hard1','hard2'):
    for line in (ROOT/'examples'/'problems'/(name+'.jsonl')).read_text().splitlines():
        if line.strip():
            r=json.loads(line); problems[r['id']]=r
results=[]
for pid,label,table in ids_tables:
    tbl=json.dumps(table,separators=(',',':'))
    code=('import JudgeProblem\nimport JudgeDecide.DecideBang\nimport JudgeFinOp.MemoFinOp\nopen MemoFinOp\n\n'
          'set_option maxRecDepth 100000 in\ndef submission : Goal := by\n  let m : Magma (Fin 8) := {\n'
          f'    op := finOpTable {json.dumps(tbl)}\n  }}\n  refine ⟨Fin 8, m, ?_⟩\n  decideFin!\n')
    judge_problem={k:problems[pid][k] for k in ('id','eq1_id','eq2_id','equation1','equation2')}; judge_problem['proof_policy']=DEFAULT_PROOF_POLICY
    res=verify_answer(judge_problem,json.dumps({'verdict':'false','code':code}))
    results.append({'id':pid,'archetype':label,'status':res['status'],'error_code':res['error_code'],'message':res['message'],'code':code})
    print(pid,'archetype='+label,res['status'],res['error_code'],flush=True)
pathlib.Path('paper_final_lean_results.json').write_text(json.dumps(results,indent=2))
print('ARCHETYPES',len(tables),'PROBLEMS',len(results),'ACCEPTED',sum(r['status']=='accepted' for r in results),flush=True)
if not all(r['status']=='accepted' for r in results): raise SystemExit(1)
