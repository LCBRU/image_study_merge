from collections import Counter
from itertools import chain
import re
import nltk
from flask import current_app
from image_study_merge.model import DataDictionary, StudyData, StudyDataColumn, StudyDataColumnSuggestion, StudyDataColumnValueMapping, StudyDataRow, StudyDataRowData
from lbrc_flask.database import db
from nltk.corpus import stopwords
from lbrc_flask.celery import celery
from lbrc_flask.export import csv_download
from sqlalchemy.orm import joinedload

thesaurus = [
    {'gender', 'sex'},
    {'smoker', 'smoking'},
    {'avg', 'average', 'mean'},
    {'peak', 'max', 'maximum'},
    {'min', 'minimum'},
    {'base', 'baseline'},
    {'%', 'perc', 'percentage'},
]

expansions = {
    'bp': {'blood', 'pressure'},
    'sbp': {'systolic', 'blood', 'pressure'},
    'dbp': {'diastolic', 'blood', 'pressure'},
    'hr': {'heart', 'rate', 'pulse'},
    'dob': {'date', 'birth'},
    'hypercholesterolaemia': {'high', 'cholesterol'}
}

less_important_words = {
    'date',
    'study',
    'value',
    'min',
    'minimum',
    'max',
    'maximum',
    'peak',
    'base',
    'baseline',
    'avg',
    'average',
    'mean',
    'time',
    'volume',
    'velocity',
    'total',
    'score',
    'performed',
    'duration',
    '0',
    '1',
    '2',
    '3',
    '4',
    '5',
    '6',
    '7',
    '8',
    '9',
}

units = {
    'mmhg',

    'years',
    'mins',
    'min',
    'minute',
    'minutes',
    's',
    'sec',
    'secs',
    'second',
    'seconds',
    'msecs',
    'ms',
    'us',
    'µs',
    'ns',

    'µm',
    'um',
    'mm',
    'cm',
    'm',

    'iu',

    'ng',
    'µg',
    'ug',
    'mg',
    'g',
    'kg',

    'bpm',
    'beat',

    'µmol',
    'umol',
    'mmol',
    'mol',

    'µl',
    'ul',
    'ml',
    'l',

    'w',

    'hu',

    'hz',
    'khz',
    'mhz',

    '%',
    'percentage',
    'perc',
}

def extract_study_data(study_data_id):
    study_data = StudyData.query.get(study_data_id)
    study_data.updating = True
    db.session.add(study_data)
    db.session.commit()

    _extract_study_data.delay(study_data_id)


@celery.task()
def _extract_study_data(study_data_id):
    study_data = StudyData.query.get(study_data_id)

    extract_study_data_columns(study_data)
    extract_study_data_rows(study_data)
    extract_study_data_values(study_data)

    study_data = StudyData.query.get(study_data_id)
    study_data.updating = False
    db.session.add(study_data)
    db.session.commit()


def extract_study_data_columns(study_data):
    current_app.logger.info('extract_study_data_columns: Started')
    columns = [
        StudyDataColumn(
            column_number=i,
            study_data_id=study_data.id,
            name=c,
        ) for i, c in enumerate(study_data.get_data().get_column_names(), 1)
    ]

    db.session.add_all(columns)
    db.session.commit()

    current_app.logger.info('extract_study_data_columns: Completed')


def extract_study_data_rows(study_data):
    current_app.logger.info('extract_study_data_rows: Started')

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

    current_app.logger.info('extract_study_data_rows: Completed')


def extract_study_data_values(study_data):
    current_app.logger.info('extract_study_data_values: Started')

    for c in study_data.columns:
        values = []

        for v in c.unique_data_value():
            values.append(StudyDataColumnValueMapping(
                study_data_column=c,
                value=v,
            ))

        db.session.add_all(values)
        db.session.commit()

    current_app.logger.info('extract_study_data_values: Completed')


def delete_mappings(study_data_id):
    study_data = StudyData.query.get(study_data_id)
    study_data.updating = True
    db.session.add(study_data)
    db.session.commit()

    _delete_mappings.delay(study_data_id)


@celery.task()
def _delete_mappings(study_data_id):
    study_data = StudyData.query.get(study_data_id)

    columns = []
    value_mappings = []
    suggested_mappings = []

    for c in study_data.columns:
        if c.mapping:
            c.mapping = ''
            columns.append(c)

        value_mappings.extend(c.value_mappings)
        suggested_mappings.extend(c.suggested_mappings)

    db.session.add_all(columns)

    for vm in value_mappings:
        db.session.delete(vm)
    for sm in suggested_mappings:
        db.session.delete(sm)

    db.session.commit()

    study_data = StudyData.query.get(study_data_id)
    study_data.updating = False
    db.session.add(study_data)
    db.session.commit()


def delete_study_data(study_data_id):
    study_data = StudyData.query.get(study_data_id)
    study_data.deleted = True
    db.session.add(study_data)
    db.session.commit()

    _delete_study_data.delay(study_data_id)


@celery.task()
def _delete_study_data(study_data_id):
    study_data = StudyData.query.get(study_data_id)

    db.session.delete(study_data)
    db.session.commit()

def automap(study_data_id):
    study_data = StudyData.query.get(study_data_id)
    study_data.updating = True
    db.session.add(study_data)
    db.session.commit()

    _automap.delay(study_data_id)


@celery.task()
def _automap(study_data_id):
    study_data = StudyData.query.get(study_data_id)

    data_dictionary = DataDictionary.query.all()

    automap_column__do_not_map(study_data, data_dictionary)
    automap_column__map_exact_field_name(study_data, data_dictionary)
    automap_column__map_exact_field_label(study_data, data_dictionary)
    automap_column__match_by_name(study_data, data_dictionary)

    automap_values__map_exact_name(study_data)

    study_data = StudyData.query.get(study_data_id)
    study_data.updating = False
    db.session.add(study_data)
    db.session.commit()


def automap_column__match_by_name(study_data, data_dictionary):
    nltk.download('stopwords')

    delete_column_suggested_mappings(study_data)

    dictionary_words = {}

    for d in data_dictionary:
        for column_name_bit in get_word_bits(f'{d.field_name} {d.field_label}'):
            dictionary_words.setdefault(column_name_bit, []).append(d)

    column_mappings = {}

    for c in study_data.columns:
        column_mappings[c] = {
            'important': [],
            'less important': [],
            'units': [],
            'stop words': [],
        }

        for column_name_bit in get_word_bits(c.name):
            if column_name_bit in dictionary_words:
                for dd in dictionary_words[column_name_bit]:
                    if column_name_bit in units:
                        column_mappings[c]['units'].append(dd)
                    elif column_name_bit in less_important_words:
                        column_mappings[c]['less important'].append(dd)
                    elif column_name_bit in stopwords.words():
                        column_mappings[c]['stop words'].append(dd)
                    else:
                        column_mappings[c]['important'].append(dd)

    suggestions = []

    for c, matches in column_mappings.items():
        important_count = Counter(matches['important'])
        less_important_count = Counter(matches['less important'])
        units_count = Counter(matches['units'])
        stop_words_count = Counter(matches['stop words'])

        for dd, cnt in important_count.most_common():
            score = (cnt * 2) + less_important_count[dd] + units_count[dd] + stop_words_count[dd]

            suggestions.append(StudyDataColumnSuggestion(
                match_score=score,
                study_data_column=c,
                mapping=dd.field_name,
            ))

    db.session.add_all(suggestions)
    db.session.commit()


def get_word_bits(value, debug=False):
    re_not_alpha = re.compile('[^a-zA-Z]')
    re_not_numeric = re.compile('[^1-9]')
    re_not_percentage = re.compile('[^%]')

    if debug:
        print({n.lower() for n in re_not_alpha.split(value) if len(n) > 0})

    bits = {n.lower() for n in re_not_alpha.split(value) if len(n) > 0} 
    bits |= {n for n in re_not_numeric.split(value) if len(n) > 0} 
    bits |= {n for n in re_not_percentage.split(value) if len(n) > 0} 

    expansion_bits = set()

    for b in bits:
        if b in expansions:
            expansion_bits |= expansions[b]

    bits |= expansion_bits

    for contraction, expansion in expansions.items():
        if expansion.issubset(bits):
            bits.add(contraction)

    for synonyms in thesaurus:
        if bits.intersection(synonyms):
            bits |= synonyms

    print(bits)

    return bits


def standardize_name(value):
    re_not_alphanumeric = re.compile('[^a-zA-Z]')
    re_in_brackets = re.compile('\(.*\)')

    return re_not_alphanumeric.sub('', re_in_brackets.sub(' ', value))


def delete_column_suggested_mappings(study_data):
    sdi = StudyDataColumn.query.with_entities(StudyDataColumn.id).filter(StudyDataColumn.study_data_id == study_data.id).subquery()
    StudyDataColumnSuggestion.query.filter(StudyDataColumnSuggestion.study_data_column_id.in_(sdi)).delete(synchronize_session='fetch')


def automap_column__do_not_map(study_data, data_dictionary):
    automap_columns__dictionary(study_data, {standardize_name('complete?'): DataDictionary.DO_NOT_IMPORT})


def automap_column__map_exact_field_name(study_data, data_dictionary):
    automap_columns__dictionary(study_data, {standardize_name(d.field_name.lower()): d.field_name for d in data_dictionary})


def automap_column__map_exact_field_label(study_data, data_dictionary):
    automap_columns__dictionary(study_data, {standardize_name(d.field_label.lower()): d.field_name for d in data_dictionary})


def automap_columns__dictionary(study_data, dictionary):
    complete_mappings = []

    for c in study_data.unmapped_columns:
        standard_name = standardize_name(c.name.lower())
        if standard_name in dictionary:
            c.mapping = dictionary[standard_name]
            complete_mappings.append(c)

    db.session.add_all(complete_mappings)
    db.session.commit()


def automap_values__map_exact_name(study_data):
    for c in study_data.mapped_columns:
        if c.mapped_data_dictionary.has_choices:
            automap_value__map_exact_name(c)


def automap_value__map_exact_name(study_data_column):
    automap_values__dictionary(study_data_column, {standardize_name(name.lower()): value for value, name in study_data_column.mapped_data_dictionary.choice_values.items()})


def automap_values__dictionary(study_data_column, dictionary):
    complete_mappings = []

    for c in study_data_column.unmapped_values:
        standard_name = standardize_name(c.value.lower())
        if standard_name in dictionary:
            c.mapping = dictionary[standard_name]
            complete_mappings.append(c)

    db.session.add_all(complete_mappings)
    db.session.commit()


def create_export(study_id):
    sd = StudyData.query.options(joinedload(StudyData.columns)).get(study_id)

    field_names = chain(*[dd.get_export_column_names() for dd in DataDictionary.query.all()])
    rows = [c.get_export_mapping() for c in sd.rows]

    return csv_download(f'export_{study_id}', field_names, rows)
