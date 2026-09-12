from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.errors import DomainError
from .schema import DepositIn, GoalIn
from .service import GoalService

router = APIRouter(prefix="/goals", tags=["goals"])


def call(operation):
    try: return operation()
    except DomainError as error: raise HTTPException(error.status_code, error.detail) from error


@router.get("")
def list_goals(db: Session = Depends(get_db)): return GoalService(db).list()

@router.post("", status_code=201)
def create_goal(body: GoalIn, db: Session = Depends(get_db)): return GoalService(db).create(body)

@router.get("/{goal_id}")
def get_goal(goal_id: int, db: Session = Depends(get_db)): return call(lambda: GoalService(db).get(goal_id))

@router.put("/{goal_id}")
def update_goal(goal_id: int, body: GoalIn, db: Session = Depends(get_db)): return call(lambda: GoalService(db).update(goal_id, body))

@router.delete("/{goal_id}", status_code=204)
def delete_goal(goal_id: int, db: Session = Depends(get_db)):
    call(lambda: GoalService(db).delete(goal_id))
    return Response(status_code=204)

@router.post("/{goal_id}/deposits", status_code=201)
def create_deposit(goal_id: int, body: DepositIn, db: Session = Depends(get_db)): return call(lambda: GoalService(db).add_deposit(goal_id, body))
