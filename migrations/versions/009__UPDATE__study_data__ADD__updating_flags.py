from sqlalchemy import (
    Boolean,
    NVARCHAR,
    MetaData,
    Table,
    Column,
    Integer,
    ForeignKey,
)
from lbrc_flask.security.migrations import get_audit_mixin_columns
from migrate.changeset.constraint import UniqueConstraint

meta = MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    t = Table("study_data", meta, autoload=True)

    updating = Column("updating", Boolean, default=False)
    updating.create(t)

    deleted = Column("deleted", Boolean, default=False)
    deleted.create(t)

    locked = Column("locked", Boolean, default=False)
    locked.create(t)


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    t = Table("study_data", meta, autoload=True)

    t.c.updating.drop()
    t.c.deleted.drop()
    t.c.locked.drop()
