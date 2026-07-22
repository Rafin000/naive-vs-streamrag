class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, list[dict]] = {}

    def get(self, session_id: str) -> list[dict]:
        return self._sessions.setdefault(session_id, [])

    def append(self, session_id: str, message: dict) -> None:
        self._sessions.setdefault(session_id, []).append(message)

    def replace(self, session_id: str, messages: list[dict]) -> None:
        self._sessions[session_id] = messages


memory = SessionStore()
