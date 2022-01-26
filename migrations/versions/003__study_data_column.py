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

    sd = Table("study_data", meta, autoload=True)

    t = Table(
        "study_data_column",
        meta,
        Column("id", Integer, primary_key=True),
        Column("column_number", Integer),
        Column("study_data_id", Integer, ForeignKey(sd.c.id), index=True, nullable=False),
        Column("name", NVARCHAR(500)),
        Column("mapping", NVARCHAR(100)),
        *get_audit_mixin_columns(),
    )

    t.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    t = Table("study_data_column", meta, autoload=True)
    t.drop()
