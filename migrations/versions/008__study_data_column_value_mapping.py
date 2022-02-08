from sqlalchemy import (
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

    sdc = Table("study_data_column", meta, autoload=True)

    t = Table(
        "study_data_column_value_mapping",
        meta,
        Column("id", Integer, primary_key=True),
        Column("study_data_column_id", Integer, ForeignKey(sdc.c.id), index=True, nullable=False),
        Column("value", NVARCHAR(100)),
        Column("mapping", NVARCHAR(100)),
        *get_audit_mixin_columns(),
    )

    t.create()

    cons = UniqueConstraint(t.c.study_data_column_id, t.c.value, name='ix__study_data_column_value_mapping__study_data_column_id__value')
    cons.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    t = Table("study_data_column_value_mapping", meta, autoload=True)
    t.drop()
