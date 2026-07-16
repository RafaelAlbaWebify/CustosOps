# TestClient dependency

CustosOps uses `httpx2` for FastAPI/Starlette `TestClient` support.

The previous direct `httpx` constraint produced a `StarletteDeprecationWarning` directing users to install `httpx2` instead. The backend requirements therefore constrain `httpx2>=2.7,<3.0` and do not install both packages together.

Validation is provided by the existing Linux and Windows backend test jobs.
