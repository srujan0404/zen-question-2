# Error injection validation

Each row exercises a failure path. Every case must return an error envelope (no uncaught exceptions).

| Case | Result | error_type | Error message (first 80 chars) |
|---|---|---|---|
| python_exec ZeroDivisionError | PASS | `exec_error` | ZeroDivisionError: division by zero |
| python_exec timeout | PASS | `timeout` | timeout after 5s |
| python_exec blocked import | PASS | `exec_error` | ImportError: __import__ not found |
| python_exec syntax error | PASS | `exec_error` | SyntaxError: '(' was never closed (<string>, line 1) |
| wikipedia page not found | PASS | `network_error` | JSONDecodeError: Expecting value: line 1 column 1 (char 0) |
| wikipedia disambiguation | PASS | `network_error` | JSONDecodeError: Expecting value: line 1 column 1 (char 0) |
| datetime bad input | PASS | `bad_input` | time data 'not-a-date' does not match format '%Y-%m-%d' |
| unknown tool | PASS | `bad_input` | unknown action 'ghost_tool'. Available: ['python_exec', 'wikipedia', 'datetime'] |
| non-dict action_input | PASS | `bad_input` | action_input must be a JSON object, got str |
