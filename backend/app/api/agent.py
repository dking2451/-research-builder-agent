from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas.agent import AgentRunRequest, AgentRunResponse
from app.services.orchestrator import run_agent

router = APIRouter(tags=["agent"])


@router.post("/agent/run", response_model=AgentRunResponse)
def agent_run(payload: AgentRunRequest, db: Session = Depends(get_db)) -> AgentRunResponse:
    try:
        return run_agent(
            db,
            project_id=payload.project_id,
            conversation_id=payload.conversation_id,
            mode=payload.mode,
            prompt=payload.prompt,
        )
    except ValueError as e:
        msg = str(e).lower()
        code = 404 if "not found" in msg else 400
        raise HTTPException(status_code=code, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Agent failed: {e}") from e
