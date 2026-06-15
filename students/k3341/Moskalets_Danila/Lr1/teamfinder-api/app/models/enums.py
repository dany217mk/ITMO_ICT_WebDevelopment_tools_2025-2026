import enum


class UserRole(str, enum.Enum):
    """Роли пользователей"""
    ADMIN = "ADMIN"
    USER = "USER"


class ProficiencyLevel(str, enum.Enum):
    """Уровни владения навыком"""
    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"
    EXPERT = "EXPERT"


class ProjectStatus(str, enum.Enum):
    """Статусы проекта"""
    DRAFT = "DRAFT"
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"


class TeamRole(str, enum.Enum):
    """Роли в команде"""
    LEAD = "LEAD"
    MEMBER = "MEMBER"
    OBSERVER = "OBSERVER"


class MemberStatus(str, enum.Enum):
    """Статусы участников команды"""
    INVITED = "INVITED"
    ACTIVE = "ACTIVE"
    LEFT = "LEFT"
    REMOVED = "REMOVED"


class SkillImportance(str, enum.Enum):
    """Важность навыка для проекта"""
    NICE_TO_HAVE = "NICE_TO_HAVE"
    IMPORTANT = "IMPORTANT"
    REQUIRED = "REQUIRED"


class TaskStatus(str, enum.Enum):
    """Статусы задач"""
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    REVIEW = "REVIEW"
    DONE = "DONE"


class TaskPriority(str, enum.Enum):
    """Приоритеты задач"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"