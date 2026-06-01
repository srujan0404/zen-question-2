from agent.tools.python_exec import run as exec_run


def test_simple_arithmetic():
    result = exec_run({"code": "print(2 + 2)"})
    assert result["ok"] is True
    assert result["result"].strip() == "4"


def test_multiline_with_division():
    code = "a = 1000\nb = 7\nprint(a / b)"
    result = exec_run({"code": code})
    assert result["ok"] is True
    assert "142.857" in result["result"]


def test_syntax_error_returns_error_envelope():
    result = exec_run({"code": "print(1 +"})
    assert result["ok"] is False
    assert result["error_type"] == "exec_error"


def test_runtime_error_returns_error_envelope():
    result = exec_run({"code": "print(1/0)"})
    assert result["ok"] is False
    assert result["error_type"] == "exec_error"
    assert "ZeroDivisionError" in result["error"]


def test_import_os_is_blocked():
    result = exec_run({"code": "import os\nprint(os.listdir('/'))"})
    assert result["ok"] is False
    assert result["error_type"] == "exec_error"


def test_file_open_is_blocked():
    result = exec_run({"code": "open('/etc/passwd').read()"})
    assert result["ok"] is False
    assert result["error_type"] == "exec_error"


def test_timeout_kills_infinite_loop():
    result = exec_run({"code": "while True: pass"}, timeout_seconds=2)
    assert result["ok"] is False
    assert result["error_type"] == "timeout"
