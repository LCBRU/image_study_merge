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
        "data_dictionary",
        meta,
        Column("id", Integer, primary_key=True),
        Column("field_number", Integer),
        Column("field_name", NVARCHAR(100)),
        Column("form_name", NVARCHAR(100)),
        Column("section_name", NVARCHAR(100)),
        Column("field_type", NVARCHAR(100)),
        Column("field_label", NVARCHAR(100)),
        Column("choices", NVARCHAR(500)),
        Column("field_note", NVARCHAR(100)),
        Column("text_validation_type", NVARCHAR(100)),
        Column("text_validation_min", NVARCHAR(100)),
        Column("text_validation_max", NVARCHAR(100)),
        *get_audit_mixin_columns(),
    )

    t.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    t = Table("data_dictionary", meta, autoload=True)
    t.drop()
