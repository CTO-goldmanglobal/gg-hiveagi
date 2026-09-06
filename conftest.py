"""Root conftest — makes the repo root importable for tests.

With this file present, pytest adds the repo root to sys.path, so tests can do
`from tools.local_bridge import ...` without the brittle `sys.path.insert` hacks
that caused mypy "module found twice" errors. Keep this file minimal.
"""
