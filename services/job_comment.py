from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from constants.comment import COMMENTS_NESTING_MAX_DEPTH
from crud.comments import comments as crud_comments
from models import Job, JobComment, User
from schemas import comment as schema_comment_job
from schemas.comment import JobCommentCreate


class JobCommentService:
    ...
    
    async def _create_comment(
        self,
        db: AsyncSession,
        new_comment_data: JobCommentCreate,
        job: Job,
        author: User,
    ) -> JobComment:
        data = new_comment_data.model_dump(exclude_unset=True)
        if parent_uid := data.get("parent_uid"):
            if found_comment := await crud_comments.get_by_uid(
                db, uid=parent_uid
            ):
                data["parent_id"] = found_comment.id
                del data["parent_uid"]
                comment_depth = await self.get_comment_nesting_depth(
                    db, found_comment
                )
                if comment_depth >= COMMENTS_NESTING_MAX_DEPTH:
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            f"Total number of nested comments mustn't exceed "
                            f"{COMMENTS_NESTING_MAX_DEPTH}"
                        ),
                    )
            else:
                raise HTTPException(
                    status_code=404,
                    detail=f"Comment {parent_uid} not found",
                )
        if data.get("first_parent_uid"):
            if not await crud_comments.get_by_uid(db, uid=parent_uid):
                raise HTTPException(
                    status_code=404,
                    detail=f"Comment {parent_uid} not found",
                )
        return await crud_comments.create(
            db=db,
            obj_in=schema_comment_job.JobCommentCreateDB(
                **data,
                author_id=author.id,
                job_id=job.id,
            ),
        )

    @staticmethod
    async def get_comment_nesting_depth(
        db: AsyncSession,
        comment: JobComment,
    ) -> int:
        return (
            len(await crud_comments.get_parents(db, id=comment.parent_id)) + 1
        )
    
    ...
