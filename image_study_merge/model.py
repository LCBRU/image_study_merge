import os
import re
from itertools import groupby
from unittest import result
from flask import current_app
from pathlib import Path
from werkzeug.utils import secure_filename
from lbrc_flask.security import AuditMixin
from lbrc_flask.model import CommonMixin
from lbrc_flask.database import db
from lbrc_flask.column_data import ExcelData, Excel97Data, CsvData


def study_data_factory(filename, **kwargs):
    _, file_extension = os.path.splitext(filename)

    if file_extension == '.csv':
        return StudyDataCsv(filename=filename, **kwargs)
    elif file_extension == '.xlsx':
        return StudyDataXlsx(filename=filename, **kwargs)
    elif file_extension == '.xls':
        return StudyDataExcel97(filename=filename, **kwargs)


class FileUploadDirectory:

    @staticmethod
    def path():
        result = Path(current_app.config["FILE_UPLOAD_DIRECTORY"])
        result.mkdir(parents=True, exist_ok=True)

        return result


class StudyData(AuditMixin, CommonMixin, db.Model):

    id = db.Column(db.Integer, primary_key=True)
    study_name = db.Column(db.String(100))
    filename = db.Column(db.String(500))
    extension = db.Column(db.String(100), nullable=False)

    __mapper_args__ = {
        "polymorphic_on": extension,
    }

    @property
    def filepath(self):
        return FileUploadDirectory.path() / secure_filename(f"{self.id}_{self.filename}")

    @property
    def unmapped_columns(self):
        return [c for c in self.columns if not c.mapped_data_dictionary]

    @property
    def mapped_columns(self):
        return [c for c in self.columns if c.mapped_data_dictionary]


class StudyDataXlsx(StudyData):
    __mapper_args__ = {
        "polymorphic_identity": '.xslx',
    }

    def get_data(self):
        return ExcelData(self.filepath)


class StudyDataExcel97(StudyData):
    __mapper_args__ = {
        "polymorphic_identity": '.xsl',
    }

    def get_data(self):
        return Excel97Data(self.filepath)


class StudyDataCsv(StudyData):
    __mapper_args__ = {
        "polymorphic_identity": '.csv',
    }

    def get_data(self):
        return CsvData(self.filepath)


class DataDictionary(AuditMixin, CommonMixin, db.Model):
    DO_NOT_MAP = '[Do Not Map]'
    NO_MAPPING = '[No Mapping]'

    id = db.Column(db.Integer, primary_key=True)
    field_number = db.Column(db.Integer)
    field_name = db.Column(db.String(100))
    form_name = db.Column(db.String(100))
    section_name = db.Column(db.String(100))
    field_type = db.Column(db.String(100))
    field_label = db.Column(db.String(100))
    choices = db.Column(db.String(100))
    field_note = db.Column(db.String(100))
    text_validation_type = db.Column(db.String(100))
    text_validation_min = db.Column(db.String(100))
    text_validation_max = db.Column(db.String(100))

    @staticmethod
    def grouped_data_dictionary():
        dd_items = []
        dd_items.append(DataDictionary(
            form_name='',
            section_name='',
            field_name='',
            field_label=DataDictionary.NO_MAPPING,
        ))
        dd_items.append(DataDictionary(
            form_name='',
            section_name='',
            field_name=DataDictionary.DO_NOT_MAP,
            field_label=DataDictionary.DO_NOT_MAP,
        ))

        dd_items.extend(DataDictionary.query.all())

        return DataDictionary.group_data_dictionary_items(dd_items)

    @staticmethod
    def group_data_dictionary_items(data_dictionary):
        result = []
        for k, g in groupby(data_dictionary, lambda dd: dd.group_name):
            result.append({
                'group': k,
                'fields': [dd for dd in g],
            })

        return result

    @property
    def field_description(self):
        return f'{self.field_label} ({self.field_name})'

    @property
    def form_name_title(self):
        return re.sub(r"[-_]", " ", self.form_name).title()

    @property
    def group_name(self):
        return ': '.join(filter(len, [self.form_name_title, self.section_name]))

    @property
    def full_name(self):
        return ': '.join(filter(len, [self.group_name, self.field_label]))

    @property
    def has_choices(self):
        return self.field_type in {'yesno', 'radio', 'dropdown', 'checkbox'}

    @property
    def choice_values(self):
        if self.field_type in {'radio', 'dropdown', 'checkbox'}:
            result = {}

            for c in self.choices.split('|'):
                value, name = c.split(',')
                result[value.strip()] = (name or '').strip()
            
            return result

        elif self.field_type == 'yesno':
            return {
                '0': 'no',
                '1': 'yes',
            }
        else:
            return {}


class StudyDataColumn(AuditMixin, CommonMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    column_number = db.Column(db.Integer)
    study_data_id = db.Column(db.Integer, db.ForeignKey(StudyData.id))
    study_data = db.relationship(StudyData, backref=db.backref("columns", cascade="all,delete"))

    name = db.Column(db.String(500))
    mapping = db.Column(db.String(100), db.ForeignKey(DataDictionary.field_name))

    mapped_data_dictionary = db.relationship(DataDictionary)

    def unique_data_value(self):
        return {d.value for d in self.data if d.value}

    @property
    def mapped_values(self):
        return [v for v in self.value_mappings if v.mapping]

    @property
    def unmapped_values(self):
        return [v for v in self.value_mappings if not v.mapping]


class StudyDataColumnValueMapping(AuditMixin, CommonMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    study_data_column_id = db.Column(db.Integer, db.ForeignKey(StudyDataColumn.id))
    study_data_column = db.relationship(StudyDataColumn, backref=db.backref("value_mappings", cascade="all,delete"))

    value = db.Column(db.String(100))
    mapping = db.Column(db.String(100))


class StudyDataColumnSuggestion(AuditMixin, CommonMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    match_score = db.Column(db.Integer)
    study_data_column_id = db.Column(db.Integer, db.ForeignKey(StudyDataColumn.id))
    study_data_column = db.relationship(StudyDataColumn, backref=db.backref("suggested_mappings", cascade="all,delete"))
    data_dictionary_id = db.Column(db.Integer, db.ForeignKey(DataDictionary.id))
    data_dictionary = db.relationship(DataDictionary)


class StudyDataRow(AuditMixin, CommonMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    study_data_id = db.Column(db.Integer, db.ForeignKey(StudyData.id))
    study_data = db.relationship(StudyData, backref=db.backref("rows", cascade="all,delete"))


class StudyDataRowData(AuditMixin, CommonMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    study_data_row_id = db.Column(db.Integer, db.ForeignKey(StudyDataRow.id))
    study_data_row = db.relationship(StudyDataRow, backref=db.backref("rows", cascade="all,delete"))
    study_data_column_id = db.Column(db.Integer, db.ForeignKey(StudyDataColumn.id))
    study_data_column = db.relationship(StudyDataColumn, backref=db.backref("data", cascade="all,delete"))

    value = db.Column(db.String(1000))
