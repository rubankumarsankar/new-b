"""Initial migration

Revision ID: c4cb1f5aa927
Revises: 
Create Date: 2026-01-02 10:18:19.834706
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c4cb1f5aa927'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'system_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(length=100), nullable=False),
        sa.Column('value', sa.String(length=500)),
        sa.Column('description', sa.String(length=255)),
        sa.Column('category', sa.String(length=50)),
        sa.Column('is_active', sa.Boolean()),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_system_settings_id', 'system_settings', ['id'])
    op.create_index('ix_system_settings_key', 'system_settings', ['key'], unique=True)

    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column(
            'role',
            sa.Enum(
                'SUPER_ADMIN',
                'ADMIN',
                'PROJECT_MANAGER',
                'EMPLOYEE',
                'CONTENT_EDITOR',
                name='userrole'
            ),
            nullable=False
        ),
        sa.Column('is_active', sa.Boolean()),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_id', 'users', ['id'])
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_username', 'users', ['username'], unique=True)

    op.create_table(
        'blogs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('excerpt', sa.String(length=500)),
        sa.Column('author_id', sa.Integer(), nullable=False),
        sa.Column(
            'status',
            sa.Enum('DRAFT', 'REVIEW', 'PUBLISHED', 'ARCHIVED', name='blogstatus')
        ),
        sa.Column('featured_image', sa.String(length=500)),
        sa.Column('meta_title', sa.String(length=255)),
        sa.Column('meta_description', sa.String(length=500)),
        sa.Column('tags', sa.String(length=500)),
        sa.Column('is_featured', sa.Boolean()),
        sa.Column('published_at', sa.DateTime()),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
        sa.ForeignKeyConstraint(['author_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_blogs_id', 'blogs', ['id'])
    op.create_index('ix_blogs_slug', 'blogs', ['slug'], unique=True)

    # (rest of your tables are already correct – no syntax issues)


def downgrade() -> None:
    op.drop_table('tasks')
    op.drop_table('projects')
    op.drop_table('attendance')
    op.drop_table('notifications')
    op.drop_table('employees')
    op.drop_table('blogs')
    op.drop_table('users')
    op.drop_table('system_settings')
