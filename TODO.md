# TODO List - Refactoring Agent

## Current State
- Refactoring agent: 328 lines (exceeds 300 HARD LIMIT)
- System prompts: analyze + apply phases implemented
- Tests: unit tests + system tests available
- Documentation: README.md, AGENTS.md present
- Model: gemma4:e2b as default

## High Priority

### Code Reduction (HARD LIMIT: 300 lines executable code)
- [ ] Reduce `src/refactoring_agent.py` from 328 to <=300 lines
- [ ] Move helper functions to separate module if needed
- [ ] Remove redundant code
- [ ] Simplify complex logic

### Test File Cleanup
- [ ] Remove smell hints from `code_smells/service.py` (variable names, comments)
- [ ] Clean `code_smells/processor.py`
- [ ] Clean `code_smells/utils.py`
- [ ] Clean `code_smells/format_utils.py`
- [ ] Ensure test files contain only neutral code descriptions

### Prompt Verification
- [ ] Verify analyze prompt produces valid, actionable smells
- [ ] Verify apply prompt correctly removes old methods
- [ ] Verify apply prompt updates all call sites
- [ ] Verify apply prompt preserves behavior exactly

## Medium Priority

### Backup System
- [ ] Verify backup creation works with permission fallback
- [ ] Test backup restore process

### Output Validation
- [ ] Verify model removes old code when refactored
- [ ] Verify model calls new helper methods instead of old ones
- [ ] Verify no wrapper methods are created

### Testing
- [ ] Run system tests with cleaned test files
- [ ] Test with files at different positions (start, middle, end)
- [ ] Test with different smell types
- [ ] Test temperature variations in prompts

### Documentation
- [ ] Update README.md with current CLI arguments
- [ ] Document file size limitations (<60 lines for reliability)
- [ ] Document backup mechanism in README

## Low Priority

### Enhancements
- [ ] Test different temperature values for model output
- [ ] Experiment with alternative prompt structures
- [ ] Consider adding more smell types
- [ ] Improve diff display formatting

## Known Issues

1. **Output Truncation**: Model with 131k context may truncate outputs above ~4000 tokens
   - Workaround: Split large files, use `fix_truncated_json()`
   
2. **Context Window**: Effective output reliability drops with large files
   - Solution: Keep files <60 lines

3. **Line Limit Violation**: refactoring_agent.py at 328 lines (limit: 300)
   - Must reduce executable code count

4. **Test File Contamination**: code_smells files contain smell hints
   - Prevents model from finding smells organically
