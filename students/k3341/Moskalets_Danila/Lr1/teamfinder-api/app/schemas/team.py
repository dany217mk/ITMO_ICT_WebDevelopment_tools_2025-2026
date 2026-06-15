from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from app.schemas.user import UserResponse

from app.schemas.user import UserResponse


class TeamRole(str, Enum):
    """Роль в команде"""
    LEAD = "LEAD"
    MEMBER = "MEMBER"
    OBSERVER = "OBSERVER"


class MemberStatus(str, Enum):
    """Статус участника команды"""
    INVITED = "INVITED"
    ACTIVE = "ACTIVE"
    LEFT = "LEFT"
    REMOVED = "REMOVED"


class TeamResponse(BaseModel):
    """Базовый ответ команды"""
    id: int
    project_id: int
    created_by: Optional[int]
    name: str
    description: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class TeamMemberResponse(BaseModel):
    """Участник команды"""
    user: UserResponse
    role_in_team: TeamRole
    status: MemberStatus
    joined_at: datetime
    
    class Config:
        from_attributes = True


class TeamDetailResponse(TeamResponse):
    """Детальный ответ команды (с участниками)"""
    members: List[TeamMemberResponse] = []


class CreateTeamRequest(BaseModel):
    """Запрос на создание команды"""
    name: str = Field(..., max_length=256, example="Frontend Team")
    description: Optional[str] = Field(None, example="UI/UX and frontend development")


class UpdateTeamRequest(BaseModel):
    """Запрос на обновление команды"""
    name: Optional[str] = Field(None, max_length=256)
    description: Optional[str] = None


class InviteMemberRequest(BaseModel):
    """Запрос на приглашение в команду"""
    user_id: int
    role_in_team: TeamRole


class UpdateMemberRequest(BaseModel):
    """Запрос на обновление участника"""
    role_in_team: Optional[TeamRole] = None
    status: Optional[MemberStatus] = None


# Forward reference fix (если нужно)
TeamDetailResponse.model_rebuild()