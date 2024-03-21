from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from crud.async_crud import BaseAsyncCRUD
from models import JobComment
from schemas.comment import JobCommentCreateDB, JobCommentUpdate


class CRUDJobComment(
    BaseAsyncCRUD[JobComment, JobCommentCreateDB, JobCommentUpdate]
):
    ...

    async def get_parents(
        self, db: AsyncSession, *, id: int
    ) -> List[JobComment]:
        child_cte = (
            select(self.model)
            .where(self.model.id == id, self.model.is_deleted.is_(False))
            .cte("cte", recursive=True)
        )
        statement = select(
            child_cte.union(
                select(self.model).join(
                    child_cte, child_cte.c.parent_id == self.model.id
                )
            )
        )
        result = await db.execute(statement)
        return result.scalars().all()
        
    ...
    