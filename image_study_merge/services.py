import re
from turtle import st
from image_study_merge.model import DataDictionary, StudyData, StudyDataColumn, StudyDataColumnSuggestion, StudyDataRow, StudyDataRowData
from lbrc_flask.database import db
from itertools import chain
from nltk.corpus import stopwords


def extract_study_data(study_data_id):
    study_data = StudyData.query.get(study_data_id)

    extract_study_data_columns(study_data)
    extract_study_data_rows(study_data)


def extract_study_data_columns(study_data):
    columns = [
        StudyDataColumn(
            column_number=i,
            study_data_id=study_data.id,
            name=c,
        ) for i, c in enumerate(study_data.get_data().get_column_names(), 1)
    ]

    db.session.add_all(columns)
    db.session.commit()


def extract_study_data_rows(study_data):
    columns = {c.name:c for c in study_data.columns}

    column_data = []
    rows = []

    for r in study_data.get_data().iter_rows():
        row = StudyDataRow(study_data_id=study_data.id)
        rows.append(row)

        for column_name, value in r.items():
            column_data.append(
                StudyDataRowData(
                    study_data_row=row,
                    study_data_column=columns[column_name],
                    value=value,
                )
            )

    db.session.add_all(rows)
    db.session.add_all(column_data)
    db.session.commit()


def automap(study_data):
    data_dictionary = DataDictionary.query.all()

    automap__do_not_map(study_data, data_dictionary)
    automap__map_exact_field_name(study_data, data_dictionary)
    automap__map_exact_field_label(study_data, data_dictionary)
    automap__match_by_name(study_data, data_dictionary)


def automap__match_by_name(study_data, data_dictionary):
    re_split_name = re.compile('[^a-zA-Z\d]')

    delete_suggested_mappings(study_data)

    dictionary_words = {}

    for d in data_dictionary:
        name_word_bits = chain.from_iterable([
            re_split_name.split(d.field_name),
            re_split_name.split(d.field_label),
        ])

        for u in {n.lower() for n in name_word_bits if len(n) > 0}:
            if u in dictionary_words:
                dictionary_words[u].append(d)
            else:
                dictionary_words[u] = [d]

    column_mappings = {}

    for c in study_data.unmapped_columns:
        for u in {n.lower() for n in re_split_name.split(c.name) if len(n) > 0}:
            if u in dictionary_words:
                for dd in dictionary_words[u]:
                    if c in column_mappings:
                        column_mappings[c].add(dd)
                    else:
                        column_mappings[c] = {dd}

    suggestions = []

    for c, dds in column_mappings.items():
        for dd in dds:
            suggestions.append(StudyDataColumnSuggestion(
                study_data_column=c,
                data_dictionary=dd,
            ))

    db.session.add_all(suggestions)
    db.session.commit()


def delete_suggested_mappings(study_data):
    sdi = StudyDataColumn.query.with_entities(StudyDataColumn.id).filter(StudyDataColumn.study_data_id == study_data.id).subquery()
    StudyDataColumnSuggestion.query.filter(StudyDataColumnSuggestion.study_data_column_id.in_(sdi)).delete(synchronize_session='fetch')


def automap__do_not_map(study_data, data_dictionary):
    automap__dictionary(study_data, {'complete?': DataDictionary.DO_NOT_MAP})


def automap__map_exact_field_name(study_data, data_dictionary):
    automap__dictionary(study_data, {d.field_name.lower(): d.field_name for d in data_dictionary})


def automap__map_exact_field_label(study_data, data_dictionary):
    automap__dictionary(study_data, {d.field_label.lower(): d.field_name for d in data_dictionary})


def automap__dictionary(study_data, dictionary):
    complete_mappings = []

    for c in study_data.unmapped_columns:
        if c.name.lower() in dictionary:
            c.mapping = dictionary[c.name.lower()]
            complete_mappings.append(c)

    db.session.add_all(complete_mappings)
    db.session.commit()
