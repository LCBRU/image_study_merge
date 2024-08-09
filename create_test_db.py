#!/usr/bin/env python3

from random import choice, randint
from dotenv import load_dotenv
from lbrc_flask.database import db
from lbrc_flask.security import init_roles, init_users
from sqlalchemy import select
from image_study_merge.model import DataDictionary, StudyData, StudyDataColumn, StudyDataCsv, StudyDataRow, StudyDataRowData
from faker import Faker

from image_study_merge.services import automap_column__match_by_name, extract_study_data_values
fake = Faker()

load_dotenv()

from image_study_merge import create_app

application = create_app()
application.app_context().push()
db.create_all()
init_roles([])
init_users()


def unique_words(n):
    return {fake.word().title() for _ in range(n)}

data_dict_types = [
    dict(
        field_type='string',
        choices='',
        field_note='',
        text_validation_type='',
        text_validation_min='',
        text_validation_max='',
    ),
    dict(
        field_type='dropdown',
        choices='a,a|b,b|c,c|d,d',
        field_note='',
        text_validation_type='',
        text_validation_min='',
        text_validation_max='',
    ),
]

# Data Dictionary
form_sections = []
for f in unique_words(randint(2,5)):
    for s in unique_words(randint(2,4)):
        form_sections.append((f, s))

data_dictionaries = []
for i,n in enumerate(unique_words(randint(len(form_sections) * 20, len(form_sections) * 40))):
    f, s = choice(form_sections)
    random_type = choice(data_dict_types)
    data_dictionaries.append(DataDictionary(
        field_number=i,
        field_name=n,
        form_name=f,
        section_name=s,
        field_label=n,
        **random_type,
    ))

db.session.add_all(data_dictionaries)
db.session.commit()


# Studies
study_names = unique_words(5)

studies = []

for s in study_names:
    studies.append(
        StudyDataCsv(
            study_name=s
        )
    )

db.session.add_all(studies)
db.session.commit()

studies = list(db.session.execute(select(StudyData)).scalars())

# Study Data Columns
study_data_columns = []

for s in studies:
    for i, n in enumerate(unique_words(randint(100,200))):
        study_data_columns.append(
            StudyDataColumn(
                column_number=i,
                study_data=s,
                name=n,
            )
        )

db.session.add_all(study_data_columns)
db.session.commit()

study_data_columns = db.session.execute(select(StudyDataColumn)).scalars()

# Study Data Rows
study_data_rows = []

for s in studies:
    for _ in range(randint(10, 100)):
        study_data_rows.append(StudyDataRow(
            study_data=s,
        ))

db.session.add_all(study_data_rows)
db.session.commit()

study_data_rows = db.session.execute(select(StudyDataRow)).scalars()

# Study Data Row Data
study_data_row_datas = []

for r in study_data_rows:
    for c in r.study_data.columns:
        study_data_row_datas.append(StudyDataRowData(
            study_data_row=r,
            study_data_column=c,
            value=fake.word(),
        ))

db.session.add_all(study_data_row_datas)
db.session.commit()

for s in studies:
    extract_study_data_values(s)
    automap_column__match_by_name(s, DataDictionary.query.all())

db.session.close()
