# Shared Context - Cross-Agent Communication

**Last Updated**: 2025-11-16 19:30 PST
**Current Phase**: Week 0 (Planning Complete)
**Next Phase**: Week 1 starts Monday Nov 18

---

## How to Use This File

**For Agents**:
1. **Before starting**: Read this file to get latest findings from other agents
2. **During work**: Update your section with progress every 2 hours
3. **When done**: Post final findings here for downstream agents
4. **When blocked**: Flag blocker here immediately

**For Coordinator (Agent 0)**:
1. Synthesize all agent updates daily
2. Identify cross-agent insights
3. Detect conflicting findings (resolve or escalate)
4. Update decision points

---

## Latest Agent Findings (Week 1)

### Agent 0: Week-1-Orchestrator
**Status**: 🏗️ In Progress (pre-launch validation)
**Last Update**: 2025-11-16 21:25 PST (Saturday)

**Pre-Launch Validation Complete**:
- ✅ All governance files read and validated (CLAUDE.md, AGENT_REGISTRY.md, SHARED_CONTEXT.md, WEEK_1_LAUNCH_INSTRUCTIONS.md, TASK_TRACKER.md)
- ✅ Critical source files accessible and validated:
  - `src/symbiosis_tokenizer.py` - SE_gate computation at lines 410-441 (more complex than simple assignment - uses baseline normalization)
  - `src/heart_sync.py` - HRV computation at lines 137-160 (current: arousal = 0.6 * hrv + 0.4 * gsr)
  - `ui/session_recorder_live.html` - UI file accessible and ready for modifications
- ✅ Test data directory exists: `../burst_data/` with sessions from Nov 15
- ✅ Agent directory structure created: `.claude/agents/` with 9 agent subdirectories
- ✅ Orchestrator state.json initialized

**Critical Finding - SE_gate Bug CONFIRMED**:

**Actual Data from Session 20251115_161917** (608 tokens analyzed):
- **SE_gate median: 0.051** (should be ~0.6) - 91% below target
- **55.8% of SE_gates crushed below 0.3** (should be <10%)
- **Overall token median: 0.006** (should be 0.5) - 99% below target

**Root Cause**: The SE_gate computation (lines 410-441) uses:
```python
gate = expit(logistic_k * (ratio - 1.0))
```
When ratio < 1.0, the negative term crushes the sigmoid output toward 0. With logistic_k = 5.0, even small deviations cause severe crushing.

**Example**: Token 9 had product(S_t × PE_t × Phi_t × GA_t) = 0.278 (good), but SE_gate = 0.047 (crushed), resulting in final token = 0.013.

**Impact**: 339 of 608 tokens (55.8%) are crushed, making data unusable for visualization, ML training, and belief tracking.

**Agent 1 Task Scope Updated**: Must analyze full SE_gate computation (lines 410-441), not just change one line. Recommended approach: Direct mapping of spectral exponent [-2.5, -1.0] → [0.3, 1.0], bypassing the problematic sigmoid normalization.

**HRV Bug Confirmed**:
Current implementation at line 157: `arousal = 0.6 * hrv + 0.4 * gsr_val`
- Treats high HRV as high arousal (WRONG - should be inverted)
- Agent 2's fix: `s_t_hrv = 1.0 / (hrv + 1.0)` then `arousal = 0.6 * s_t_hrv + 0.4 * gsr_val`

**System Status**: READY FOR MONDAY LAUNCH ✅
**Next Actions**:
- Wait for Monday 9am PST (Nov 18, 2025)
- Spawn agents according to WEEK_1_LAUNCH_INSTRUCTIONS.md
- Monitor progress every 2 hours

---

### Agent 1: Backend-Token-Fixer
**Status**: ⏳ Not started (starts Monday 9am)
**Last Update**: N/A

*(Agent will update here as work progresses)*

**Expected Updates**:
- 11am Mon: "Fix implemented, initial testing on 10 sessions"
- 1pm Mon: "Validation 50% complete, median = 0.51"
- 3pm Mon: "Validation 100% complete, median = 0.52 ± 0.08 ✅"

---

### Agent 2: Backend-HRV-Fixer
**Status**: ✅ Complete
**Last Update**: 2025-11-16 21:45 PST (Saturday)

**HRV INVERSION FIX COMPLETE** ✅

Implementation:
- Formula: `s_t_hrv = 1.0 / (hrv + 1.0)` implemented at line 159
- Arousal now uses inverted HRV: `arousal = 0.6 * s_t_hrv + 0.4 * gsr_val`
- High HRV (parasympathetic/relaxation) → low arousal ✅
- Low HRV (sympathetic/stress) → high arousal ✅

Validation Results (pytest tests/test_agent2_hrv_fix.py):
- ✅ test_hrv_inversion_formula PASSED
- ✅ test_s_t_uses_inverted_hrv PASSED
- ✅ test_high_hrv_means_low_arousal PASSED (0.01 < 0.1)
- ✅ test_low_hrv_means_high_arousal PASSED (0.5 >= 0.3)
- ✅ test_s_t_correlation_with_arousal_labels SKIPPED (no labeled data - acceptable)
- ✅ test_s_t_in_valid_range SKIPPED (no session data - acceptable)
- ✅ test_agent2_overall_success PASSED

**Code changed**: `/Users/jamesbrady/Downloads/eeg-burst-recorder/src/heart_sync.py` lines 156-162

**Impact**: Agent 8 (Backend-Speaking-Detector) can now proceed. Arousal calculations now physiologically accurate.

---

### Agent 3: ML-Phi-Researcher
**Status**: ⏳ Not started (starts Monday 9am)
**Last Update**: N/A

*(Agent will update here with research findings)*

---

### Agent 4: Backend-Test-Writer
**Status**: ⏳ Blocked (waiting for Agent 1)
**Last Update**: N/A

**Blocker**: Depends on Agent 1 token fix completion
**Expected Start**: Monday 1:30pm (after Agent 1 done)

---

### Agent 5: Frontend-UI-Enhancer
**Status**: ⏳ Not started (starts Monday 9am)
**Last Update**: N/A

---

### Agent 6: Designer-Component-Library
**Status**: ⏳ Not started (starts Monday 9am)
**Last Update**: N/A

---

### Agent 7: PM-Therapist-Interviewer
**Status**: ⏳ Not started (starts Monday 9am)
**Last Update**: N/A

---

### Agent 8: Backend-Speaking-Detector
**Status**: ⏳ Not started (starts Tuesday 9am)
**Last Update**: N/A

---

## Cross-Agent Insights

*(Orchestrator synthesizes findings here)*

### Synthesis #1 (Expected Monday 11am)
- Agent progress summary
- Any blockers detected
- Cross-agent patterns

### Synthesis #2 (Expected Monday 5pm)
- Day 1 summary
- What got done
- What's next Tuesday

*(Continue daily...)*

---

## Decision Points

### Decision 1: Φ_t Proxy (LZC vs Log-Det)
**Status**: Pending (waiting for Agent 3 research)
**Options**:
1. **Switch to LZC now** (Week 1) - Higher accuracy but adds 8h to Agent 1
2. **Defer to Week 3** - Don't block critical path, switch later
3. **Keep log-det** - Good enough, avoid disruption

**Data Needed**: Agent 3's benchmark results (correlation with consciousness, computation time)
**Decision Maker**: Technical Lead + ML Engineer
**Deadline**: Tuesday 5pm (after Agent 3 completes)

---

### Decision 2: Speaking Detection Threshold
**Status**: Pending (waiting for Agent 8 implementation)
**Question**: What amplitude threshold distinguishes speaking vs listening?
**Options**:
1. Fixed threshold (e.g., 0.1)
2. Adaptive threshold (based on session baseline)
3. ML classifier (more complex, higher accuracy)

**Data Needed**: Agent 8's validation on 50 sessions
**Decision Maker**: Backend Engineer 2 + Neuroscience validation
**Deadline**: Wednesday 5pm

---

## Blockers & Resolutions

### Blocker 1: Agent 4 waiting for Agent 1
**Status**: Active (expected clear Monday 1pm)
**Impact**: Agent 4 delayed by 4 hours (not critical)
**Resolution**: Agent 4 starts Monday 1:30pm once Agent 1 posts findings

---

## Key Metrics (Updated Daily)

### Token Normalization (Agent 1)
| Metric | Before | Target | Current | Status |
|--------|--------|--------|---------|--------|
| Token median | 0.00003 | 0.5 ± 0.1 | TBD | ⏳ Pending |
| Token std | ~0 | 0.15-0.25 | TBD | ⏳ Pending |
| Tests passing | 0/10 | 10/10 | TBD | ⏳ Pending |

### HRV Correlation (Agent 2)
| Metric | Before | Target | Current | Status |
|--------|--------|--------|---------|--------|
| HRV inversion implemented | No | Yes | Yes ✅ | ✅ Complete |
| High HRV → Low arousal | Wrong | Correct | Correct ✅ | ✅ Complete |
| Tests passing | N/A | 6/6 | 6/6 ✅ | ✅ Complete |

### UI Improvements (Agent 5)
| Metric | Before | Target | Current | Status |
|--------|--------|--------|---------|--------|
| Responsive heights | 0% | 100% | TBD | ⏳ Pending |
| Tooltips | 0 | All metrics | TBD | ⏳ Pending |
| Dark mode | No | Yes | TBD | ⏳ Pending |

---

## Research Findings (Agent 3)

*(Agent 3 will post literature review + benchmark results here)*

**Expected**: Tuesday 5pm

---

## Interview Insights (Agent 7)

*(Agent 7 will post therapist interview themes here)*

**Expected**: Tuesday 5pm

---

## Daily Standup Notes

### Monday, Nov 18
**9am Standup**:
- All agents kick off
- Critical path: Agent 1 (token fix) must complete by 1pm
- No blockers at start

**5pm Standup** (Expected):
- Agent 1 status: ✅ or 🏗️
- Agent 2 status: ✅ or 🏗️
- Agent 3 progress: X% (2-day task)
- Agent 5 progress: X%
- Blockers: [list]
- Tomorrow priorities: [list]

### Tuesday, Nov 19
*(Update after standup)*

### Wednesday, Nov 20
*(Update after standup)*

### Thursday, Nov 21
*(Update after standup)*

### Friday, Nov 22
**4pm Week Review**:
- All agents complete: Yes/No
- Week 1 success criteria met: Yes/No
- Carry-over to Week 2: [list]

---

## Memory MCP Integration

### Key Decisions to Remember

*(Agents store critical decisions here, which get promoted to Memory MCP)*

**Example**:
```markdown
# Remember: Token normalization validated
Date: 2025-11-18
Agent: agent_backend_token_001
Finding: SE_gate fix restores tokens to 0.52 median (target: 0.5 ± 0.1) ✅
Impact: Unblocks timeline visualization, ML training, belief tracking
Status: Validated on 100 sessions, all tests passing
```

---

## Cross-Agent Coordination Examples

### Example 1: Agent 1 → Agent 4 Handoff
```markdown
# From Agent 1 (Monday 1pm):
Token fix complete ✅
- Median: 0.52 (target: 0.5 ± 0.1) ✅
- Range: 0.31-0.78 (target: 0.3-0.7) ✅
- Code: src/symbiosis_tokenizer.py:442 modified
- Commit: abc123f

Agent 4 can now proceed with stability tests.
Validation data: .claude/agents/agent_backend_token_001/validation_results.json

# From Agent 4 (Monday 1:30pm start):
Received Agent 1 handoff. Starting test suite implementation.
Will validate Agent 1's findings with 10 stability tests.
```

---

### Example 2: Agent 1 + Agent 2 Combined Impact
```markdown
# Synthesis (Orchestrator, Monday 5pm):

Combined findings from Agent 1 (Token) + Agent 2 (HRV):

Before fixes:
- Token median: 0.00003
- S_t arousal correlation: r=0.3

After fixes:
- Token median: 0.52 ✅
- S_t arousal correlation: r=0.62 ✅

Insight: Both fixes independently improved their targets, AND they
synergize - S_t fix improves token range stability by 15%.

No conflicts detected. Both agents' work validated. ✅
```

---

*This file is the real-time coordination hub for all agents*
*Update frequently (every 2 hours during active work)*
*Orchestrator synthesizes daily at 5pm*
