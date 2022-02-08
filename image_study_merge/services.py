from collections import Counter
import re
import nltk
from image_study_merge.model import DataDictionary, StudyData, StudyDataColumn, StudyDataColumnSuggestion, StudyDataColumnValueMapping, StudyDataRow, StudyDataRowData
from lbrc_flask.database import db
from itertools import chain
from nltk.corpus import stopwords


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

    extract_study_data_columns(study_data)
    extract_study_data_rows(study_data)
    extract_study_data_values(study_data)


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

        for column_name, value in r:
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


def extract_study_data_values(study_data):
    values = []

    for c in study_data.columns:
        for v in c.unique_data_value():
            values.append(StudyDataColumnValueMapping(
                study_data_column=c,
                value=v,
            ))

    db.session.add_all(values)
    db.session.commit()


def delete_mappings(study_data):
    columns = []
    value_mappings = []

    for c in study_data.columns:
        if c.mapping:
            c.mapping = ''
            columns.append(c)

        for vm in c.value_mappings:
            if vm.mapping:
                vm.mapping = ""
                value_mappings.append(vm)

    db.session.add_all(columns)
    db.session.add_all(value_mappings)
    db.session.commit()


def automap(study_data):
    data_dictionary = DataDictionary.query.all()

    automap_column__do_not_map(study_data, data_dictionary)
    automap_column__map_exact_field_name(study_data, data_dictionary)
    automap_column__map_exact_field_label(study_data, data_dictionary)
    automap_column__match_by_name(study_data, data_dictionary)

    automap_values__map_exact_name(study_data)


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
                data_dictionary=dd,
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

    return bits


def standardize_name(value):
    re_not_alphanumeric = re.compile('[^a-zA-Z]')
    re_in_brackets = re.compile('\(.*\)')

    return re_not_alphanumeric.sub('', re_in_brackets.sub(' ', value))


def delete_column_suggested_mappings(study_data):
    sdi = StudyDataColumn.query.with_entities(StudyDataColumn.id).filter(StudyDataColumn.study_data_id == study_data.id).subquery()
    StudyDataColumnSuggestion.query.filter(StudyDataColumnSuggestion.study_data_column_id.in_(sdi)).delete(synchronize_session='fetch')


def automap_column__do_not_map(study_data, data_dictionary):
    automap_columns__dictionary(study_data, {standardize_name('complete?'): DataDictionary.DO_NOT_MAP})


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
