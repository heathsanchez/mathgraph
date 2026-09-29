import TaskNet.Semantics

open Std
open TaskNet

def auditRange : RealRange := { low := 0.0, high := 10.0 }

def auditTimeline : Timeline :=
  .cumulativeTimeline "x" auditRange auditRange 0.0

def auditTask : TaskDef := {
  id := "T"
  ident := 1
  priority := 1
  startrng := { low := 1, high := 1 }
  endrng := { low := 2, high := 2 }
  durrng := { low := 1, high := 1 }
  dur := 1
  start := 1
  after := []
  containedin := []
  after_definitions := []
  containedin_definitions := []
  kind := .required
  pre := []
  inv := []
  post := []
  impacts := [
    { id := "x", when := .pre, how := .assign (.realVal 50.0) }
  ]
}

def auditTaskNet : TaskNet := {
  id := "ClampAssignmentAudit"
  timelines := [auditTimeline]
  tasks := [auditTask]
  taskdefs := []
  endTime := 3
}

def auditSchedule : Schedule :=
  ({} : Schedule).insert "T" (1, 2)

def auditIncluded : HashSet TaskName :=
  HashSet.emptyWithCapacity

def auditValid : Bool :=
  AdmissibleSparse auditTaskNet auditSchedule auditIncluded

def main : IO Unit := do
  IO.println s!"LEAN_ADMISSIBLE={auditValid}"
  if auditValid then
    IO.println "LEAN_ASSIGNMENT_RESULT=within_[0,10]_after_clamp"
  else
    throw <| IO.userError "Expected upstream Lean validator to accept the pinned schedule"
