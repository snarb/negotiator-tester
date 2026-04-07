### 1. Plan Node Default
- Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions)
- If something goes sideways, STOP and re-plan immediately - don't keep pushing
- Use plan mode for verification steps, not just building
- Write detailed specs upfront to reduce ambiguity 

### 2. Subagent Strategy
- Use subagents liberally to keep main context window clean
- Offload research, exploration, and parallel analysis to subagents
- For complex problems, throw more compute at it via subagents
- One task per subagent for focused execution 

### 3. Self-Improvement Loop
- After ANY correction from the user: update tasks/lessons.md with the pattern
- Write rules for yourself that prevent the same mistake
- Ruthlessly iterate on these lessons until mistake rate drops
- Review lessons at session start for relevant project 

### 4. Verification Before Done
- Never mark a task complete without proving it works
- Diff behavior between main and your changes when relevant
- Ask yourself: "Would a staff engineer approve this?"
- Run UI tests, check logs, demonstrate correctness before ending the task

### 5. Demand Elegance (Balanced)
- For non-trivial changes: pause and ask "is there a more elegant way?"
- If a fix feels hacky: "Knowing everything I know now, implement the elegant solution"
- Skip this for simple, obvious fixes - don't over-engineer
- Challenge your own work before presenting it 

### 6. Autonomous Bug Fixing
- When given a bug report: just fix it. Don't ask for hand-holding
- Point at logs, errors, failing tests - then resolve them
- Zero context switching required from the user
- Go fix failing CI tests without being told how 

## Task Management 

1. Plan First
2. Verify Plan: Check in before starting implementation
3. Track Progress
6. Capture Lessons: Update tasks/lessons.md after corrections 

## Documentation
- Comprehensive documentation is available in `docs/architecture.md`
- The external integration contract for UI testing and simulation is defined via the Inbound and Outbound Action APIs as documented in `docs/ICD.md`
- General setup and installation instructions can be found in the `README.md` file.
- Backend Database Schema documentation is available in  `docs/Database Schema.md`
- Alsways update documentation as the last step, fully preserve details in the existing docs; remove or rewrite only the sections that are actually obsolete.


## Core Principles 

- Simplicity First: Make every change as simple as possible. Impact minimal code.
- No Laziness: Find root causes. No temporary fixes. Senior developer standards. 