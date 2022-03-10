from sqlalchemy import (
    MetaData,
    Table,
    Column,
    Integer,
    ForeignKey,
    NVARCHAR,
)
from lbrc_flask.security.migrations import get_audit_mixin_columns

meta = MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    sdc = Table("study_data_column", meta, autoload=True)
    dd = Table("data_dictionary", meta, autoload=True)

    t = Table(
        "study_data_column_suggestion",
        meta,
        Column("id", Integer, primary_key=True),
        Column("match_score", Integer),
        Column("study_data_column_id", Integer, ForeignKey(sdc.c.id), index=True, nullable=False),
        Column("mapping", NVARCHAR(100)),
        *get_audit_mixin_columns(),
    )

    t.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    t = Table("study_data_column_suggestion", meta, autoload=True)
    t.drop()
