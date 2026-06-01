import ast
import io
import signal
import contextlib

SAFE_BUILTIN_NAMES = {
    "abs", "all", "any", "bool", "dict", "divmod", "enumerate", "float", "int",
    "len", "list", "map", "max", "min", "pow", "print", "range", "repr", "reversed",
    "round", "set", "sorted", "str", "sum", "tuple", "zip",
}


class _TimeoutError(Exception):
    pass


def _handler(signum, frame):
    raise _TimeoutError("execution exceeded timeout")


def _build_safe_builtins() -> dict:
    import builtins as _b
    return {name: getattr(_b, name) for name in SAFE_BUILTIN_NAMES if hasattr(_b, name)}


def _exec_with_repl_semantics(code: str, safe_globals: dict, stdout: io.StringIO) -> None:

    tree = ast.parse(code, mode="exec")
    last_expr = None
    if tree.body and isinstance(tree.body[-1], ast.Expr):
        last_expr = tree.body[-1].value
        tree.body = tree.body[:-1]

    with contextlib.redirect_stdout(stdout):
        if tree.body:
            exec(compile(tree, "<agent_python_exec>", "exec"), safe_globals, safe_globals)
        if last_expr is not None:
            value = eval(
                compile(ast.Expression(last_expr), "<agent_python_exec>", "eval"),
                safe_globals,
                safe_globals,
            )
            if value is not None:
                print(repr(value))


def run(args: dict, timeout_seconds: int = 5) -> dict:
    code = args.get("code", "")
    if not isinstance(code, str) or not code.strip():
        return {"ok": False, "error": "missing or empty 'code'", "error_type": "bad_input"}

    safe_globals = {"__builtins__": _build_safe_builtins()}
    stdout = io.StringIO()
    old_handler = signal.signal(signal.SIGALRM, _handler)
    signal.alarm(timeout_seconds)

    try:
        _exec_with_repl_semantics(code, safe_globals, stdout)
        signal.alarm(0)
        return {"ok": True, "result": stdout.getvalue()}
    except _TimeoutError:
        return {"ok": False, "error": f"timeout after {timeout_seconds}s", "error_type": "timeout"}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}", "error_type": "exec_error"}
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


SPEC = {
    "name": "python_exec",
    "description": "Run a short Python snippet for arithmetic / list / string operations. The value of the last bare expression is auto-printed (REPL-style); you can also call print() explicitly. No imports, no file I/O, no network. 5s timeout.",
}
