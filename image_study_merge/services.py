from image_study_merge.model import StudyData, StudyDataColumn, StudyDataRow, StudyDataRowData
from lbrc_flask.database import db


def extract_study_data(study_data_id):
    study_data = StudyData.query.get(study_data_id)

    extract_study_data_columns(study_data)
    extract_study_data_rows(study_data)


def extract_study_data_columns(study_data):
    columns = [
        StudyDataColumn(
            study_data_id=study_data.id,
            name=c,
        ) for c in study_data.get_data().get_column_names()
    ]

    db.session.add_all(columns)
    db.session.commit()


def extract_study_data_rows(study_data):
    columns = {c.name:c for c in study_data.columns}

    for r in study_data.get_data().iter_rows():
        row = StudyDataRow(study_data_id=study_data.id)
        db.session.add(row)

        for column_name, value in r.items():
            v = StudyDataRowData(
                study_data_row=row,
                study_data_column=columns[column_name],
                value=value,
            )
            db.session.add(v)

    db.session.commit()
