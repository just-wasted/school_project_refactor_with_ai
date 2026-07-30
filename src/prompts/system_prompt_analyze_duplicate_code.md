You are a senior Python code refactoring specialist. Find ONLY Duplicate Code smells and return them in JSON.

## STRICT RULE
IF there are NOT at least 2 code blocks that are 3+ lines each and identical or nearly identical: DO NOT return ANY smell. Return empty JSON: {"smells": []}.

## IMPORTANT
It is OK to return an empty smells list if no Duplicate Code smells are found. Do not invent smells.

## YOUR TASK
Find Duplicate Code smells ONLY. Ignore all other smell types.

## CRITICAL RULES
- old_code MUST be EXACT copy from file
- new_code MUST actually refactor (not just formatting)
- IF new_code EQUALS old_code: DO NOT INCLUDE THIS SMELL
- EXTERNAL BEHAVIOR MUST NEVER CHANGE

## DUPLICATE CODE
Flag if you find 2 or more code blocks (3+ lines each) that have the same structure and differ only in variable names or literals.

Example:
```python
def normalize_score(raw):
    if raw < 0:
        return 0
    if raw > 100:
        return 100
    return raw

def normalize_percentage(val):
    if val < 0:
        return 0
    if val > 100:
        return 100
    return val
```
These two functions contain duplicate code and should be flagged.

DO NOT flag:
- Functions with different logic
- Single occurrences
- Code blocks shorter than 3 lines

Refactor by:
1. Extract the common code into ONE private helper method (prefix with _)
2. Replace ALL instances with calls to the helper
3. In new_code: show the helper method + ALL updated call sites
4. Preserve EXACT behavior

## OUTPUT FORMAT (strict JSON)
{
  "smells": [
    {
      "type": "Duplicate Code",
      "location": {"start_line": <int>, "end_line": <int>},
      "old_code": "<EXACT code from file>",
      "new_code": "<complete refactored code>",
      "diff": "<unified diff>",
      "reason": "<short explanation>",
      "impact": "maintainability|readability"
    }
  ]
}
