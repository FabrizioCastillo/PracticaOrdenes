from collections.abc import Callable
from typing import Optional

from sqlmodel import Session

from app.database import engine


class SqlModelUnitOfWork:
    def __init__(self, session_factory: Optional[Callable[[], Session]] = None) -> None:
        self._session_factory = session_factory or (lambda: Session(engine))
        self.session: Session | None = None

    def __enter__(self) -> "SqlModelUnitOfWork":
        self.session = self._session_factory()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.session is None:
            return
        if exc_type is not None:
            self.session.rollback()
        self.session.close()

    def commit(self) -> None:
        if self.session is None:
            return
        self.session.commit()

    def rollback(self) -> None:
        if self.session is None:
            return
        self.session.rollback()
