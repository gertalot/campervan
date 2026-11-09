# Implementation notes

Task 1 introduces the revisioned workflow foundation; see the Task 1 SDD report for wire contracts and limitations.
No app/job runtime or manual acceptance has been performed. All new workflow actions currently report unavailable.
Producer tasks must use `capture_inputs` for dispatch and read-time freshness, and record settings and context usage
in artifact assumptions. Physical observations remain owned by the existing measurement store.
