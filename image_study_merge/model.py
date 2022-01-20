import os
from flask import current_app
from pathlib import Path
from werkzeug.utils import secure_filename
from lbrc_flask.security import AuditMixin
from lbrc_flask.model import CommonMixin
from lbrc_flask.database import db


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


class StudyDataExcel97(StudyData):
    __mapper_args__ = {
        "polymorphic_identity": '.xsl',
    }


class StudyDataCsv(StudyData):
    __mapper_args__ = {
        "polymorphic_identity": '.csv',
    }
