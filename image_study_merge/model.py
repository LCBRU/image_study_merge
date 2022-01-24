import os
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


class StudyDataColumn(AuditMixin, CommonMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    study_data_id = db.Column(db.Integer, db.ForeignKey(StudyData.id))
    study_data = db.relationship(StudyData, backref=db.backref("columns", cascade="all,delete"))

    name = db.Column(db.String(500))
    mapping = db.Column(db.String(100))


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


class DataDictionary(AuditMixin, CommonMixin, db.Model):
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

