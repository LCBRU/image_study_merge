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

    sdc = Table("study_data_column", meta, autoload=True)
    dd = Table("data_dictionary", meta, autoload=True)

    t = Table(
        "study_data_column_suggestion",
        meta,
        Column("id", Integer, primary_key=True),
        Column("study_data_column_id", Integer, ForeignKey(sdc.c.id), index=True, nullable=False),
        Column("data_dictionary_id", Integer, ForeignKey(dd.c.id), index=True, nullable=False),
        *get_audit_mixin_columns(),
    )

    t.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    t = Table("study_data_column_suggestion", meta, autoload=True)
    t.drop()
