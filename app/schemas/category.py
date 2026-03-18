"""Category schemas."""

from pydantic import BaseModel, Field

from app.schemas.common import TimestampSchema


class CategoryBase(TimestampSchema):
    """Category read schema."""

    id: int
    parent_id: int | None
    name: str
    slug: str
    is_active: bool
    sort_order: int


class CategoryCreate(BaseModel):
    """Category create/update payload."""

    parent_id: int | None = None
    name: str
    slug: str
    is_active: bool = True
    sort_order: int = 0


class CategoryTree(CategoryBase):
    """Category tree schema."""

    children: list["CategoryTree"] = Field(default_factory=list)


CategoryTree.model_rebuild()
