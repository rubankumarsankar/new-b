from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from ...database import get_db
from ...models.blog import Blog, BlogStatus
from ...models.user import User, UserRole
from ..deps import get_current_user
from pydantic import BaseModel

router = APIRouter()

class BlogCreate(BaseModel):
    title: str
    slug: str
    content: str
    excerpt: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    tags: Optional[str] = None

class BlogUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    excerpt: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    tags: Optional[str] = None

class BlogResponse(BaseModel):
    id: int
    title: str
    slug: str
    content: str
    excerpt: Optional[str]
    author_id: int
    status: BlogStatus
    author_name: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

@router.get("/", response_model=List[BlogResponse])
def get_blogs(
    status: Optional[BlogStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all blogs"""
    query = db.query(Blog)
    
    if current_user.role == UserRole.CONTENT_EDITOR:
        query = query.filter(Blog.author_id == current_user.id)
    
    if status:
        query = query.filter(Blog.status == status)
    
    blogs = query.order_by(Blog.created_at.desc()).all()
    
    return [
        {
            "id": blog.id,
            "title": blog.title,
            "slug": blog.slug,
            "content": blog.content,
            "excerpt": blog.excerpt,
            "author_id": blog.author_id,
            "status": blog.status,
            "author_name": blog.author.username if blog.author else None,
            "created_at": blog.created_at
        }
        for blog in blogs
    ]

@router.get("/{blog_id}", response_model=BlogResponse)
def get_blog(
    blog_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get blog by ID"""
    blog = db.query(Blog).filter(Blog.id == blog_id).first()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    
    return {
        "id": blog.id,
        "title": blog.title,
        "slug": blog.slug,
        "content": blog.content,
        "excerpt": blog.excerpt,
        "author_id": blog.author_id,
        "status": blog.status,
        "author_name": blog.author.username if blog.author else None,
        "created_at": blog.created_at
    }

@router.post("/", response_model=BlogResponse)
def create_blog(
    blog_data: BlogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create new blog"""
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.CONTENT_EDITOR]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Check if slug exists
    if db.query(Blog).filter(Blog.slug == blog_data.slug).first():
        raise HTTPException(status_code=400, detail="Slug already exists")
    
    blog = Blog(
        title=blog_data.title,
        slug=blog_data.slug,
        content=blog_data.content,
        excerpt=blog_data.excerpt,
        author_id=current_user.id,
        meta_title=blog_data.meta_title,
        meta_description=blog_data.meta_description,
        tags=blog_data.tags,
        status=BlogStatus.DRAFT
    )
    
    db.add(blog)
    db.commit()
    db.refresh(blog)
    
    return {
        "id": blog.id,
        "title": blog.title,
        "slug": blog.slug,
        "content": blog.content,
        "excerpt": blog.excerpt,
        "author_id": blog.author_id,
        "status": blog.status,
        "author_name": current_user.username,
        "created_at": blog.created_at
    }

@router.put("/{blog_id}", response_model=BlogResponse)
def update_blog(
    blog_id: int,
    blog_data: BlogUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update blog"""
    blog = db.query(Blog).filter(Blog.id == blog_id).first()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    
    # Check permissions
    if current_user.role == UserRole.CONTENT_EDITOR and blog.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if blog_data.title is not None:
        blog.title = blog_data.title
    if blog_data.content is not None:
        blog.content = blog_data.content
    if blog_data.excerpt is not None:
        blog.excerpt = blog_data.excerpt
    if blog_data.meta_title is not None:
        blog.meta_title = blog_data.meta_title
    if blog_data.meta_description is not None:
        blog.meta_description = blog_data.meta_description
    if blog_data.tags is not None:
        blog.tags = blog_data.tags
    
    db.commit()
    db.refresh(blog)
    
    return {
        "id": blog.id,
        "title": blog.title,
        "slug": blog.slug,
        "content": blog.content,
        "excerpt": blog.excerpt,
        "author_id": blog.author_id,
        "status": blog.status,
        "author_name": blog.author.username if blog.author else None,
        "created_at": blog.created_at
    }

@router.patch("/{blog_id}/status")
def update_blog_status(
    blog_id: int,
    status: BlogStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update blog status"""
    blog = db.query(Blog).filter(Blog.id == blog_id).first()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    
    # Only admin can publish
    if status == BlogStatus.PUBLISHED and current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Only admins can publish blogs")
    
    blog.status = status
    if status == BlogStatus.PUBLISHED:
        blog.published_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Blog status updated successfully"}

@router.delete("/{blog_id}")
def delete_blog(
    blog_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete blog"""
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    blog = db.query(Blog).filter(Blog.id == blog_id).first()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    
    db.delete(blog)
    db.commit()
    
    return {"message": "Blog deleted successfully"}