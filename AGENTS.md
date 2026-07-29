# Coding Agent Guidelines

## General Rules

- Code must be valid and syntactically correct
- Preserve existing behavior - no functional changes unless explicitly requested
- One logical change per commit
- Follow existing code style (indentation, naming conventions)
- Remove all emojis from code, comments, and commit messages

## Project Structure

- Source code: `src/`
- Test files: `tests/`
- Prompts: `src/prompts/`
- Example code: `code_smells/` (keep files <60 lines for reliability)
- Backups: `backup/` (auto-generated, read-only)

## Code Quality

- Verify syntax before applying changes (use `python -m py_compile`)
- Backup original files before refactoring
- Handle indentation correctly (4 spaces per level)
- Maintain class/method structure when modifying code
- All code must be executable Python

## Emoji Policy

Emojis are explicitly unwanted in the entire project. This includes:
- Code and comments
- Commit messages
- Documentation
- Output messages
- Any text files

## Backup Mechanism

- Backups are created automatically in `backup/` directory
- Backup files are read-only (0o444 permissions)
- Format: `YYYYMMDD_HHMMSS_<originalname>.py`

## LLM Integration Lessons

### Output Reliability
- **Context vs Output Limit**: A model with 131k context tokens (gemma4) may still truncate outputs
- **Effective limit**: Practical output reliability drops above ~4000 tokens
- **Solution**: Use `num_predict` parameter + split large files into smaller ones (<60 lines)

### JSON Handling
- **Model behavior**: Even with `format: json`, models may return incomplete JSON
- **Workaround**: Implement `fix_truncated_json()` to recover from partial outputs
- **Recommendation**: Split files to avoid hitting model output limits

### Prompt Engineering
- Short, clear prompts with specific examples work better than long, generic ones
- Separate analysis and application phases with dedicated prompts
- Test prompts with multiple runs - models are not 100% deterministic
