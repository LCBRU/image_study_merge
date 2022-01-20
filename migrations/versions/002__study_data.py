from sqlalchemy import (
    MetaData,
    Table,
    Column,
    Integer,
    NVARCHAR,
    ForeignKey,
    DateTime,
)
from lbrc_flask.security.migrations import get_audit_mixin_columns

meta = MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    t = Table(
        "study_data",
        meta,
        Column("id", Integer, primary_key=True),
        Column("study_name", NVARCHAR(100)),
        Column("filename", NVARCHAR(500)),
        Column("extension", NVARCHAR(100)),
        *get_audit_mixin_columns(),
    )

    t.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    t = Table("study_data", meta, autoload=True)
    t.drop()
