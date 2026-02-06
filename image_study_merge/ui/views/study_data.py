from .. import blueprint
from flask import render_template, request, flash, redirect, url_for, send_file
from lbrc_flask.forms import SearchForm, FlashingForm, FileField, ConfirmForm, Unique
from image_study_merge.services import automap, create_export, delete_mappings, delete_study_data, extract_study_data
from image_study_merge.model import StudyData, study_data_factory
from flask_wtf.file import FileRequired
from lbrc_flask.database import db
from wtforms import StringField
from wtforms.validators import Length, DataRequired
from lbrc_flask.security import must_be_admin
from lbrc_flask.response import refresh_response
from sqlalchemy import select


class UploadStudyDataForm(FlashingForm):
    study_name = StringField(
        "Study Name",
        validators=[
            Length(max=100),
            DataRequired(),
            Unique(StudyData, StudyData.study_name),
        ])
    upload = FileField(
        'Study Data File',
        accept=[
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.ms-excel',
            '.csv',
        ],
        validators=[FileRequired()]
    )


@blueprint.route("/")
def index():
    search_form = SearchForm(formdata=request.args)

    q = select(StudyData).where(StudyData.deleted == False)

    if search_form.search.data:
        q = q.filter(StudyData.filename.like(f'%{search_form.search.data}%'))

    study_datas = db.paginate(select=q)

    return render_template(
        "ui/index.html",
        study_datas=study_datas,
        search_form=search_form,
        confirm_form=ConfirmForm(),
    )


@blueprint.route("/upload_study_data", methods=['GET', 'POST'])
def study_data_upload():
    form = UploadStudyDataForm()

    if form.validate_on_submit():
        sd = StudyData()

        sd = study_data_factory(
            form.upload.data.filename,
            study_name=form.study_name.data,
        )

        db.session.add(sd)
        db.session.commit()

        form.upload.data.save(sd.filepath)

        extract_study_data(sd.id)

        flash('Study Data Uploaded')

        return refresh_response()

    return render_template(
        "lbrc/form_modal.html",
        title='Study Data Upload',
        form=form,
        url=url_for('ui.study_data_upload', id=id),
    )


@blueprint.route("/study_data/<int:id>/download")
def study_data_download(id):
    sd = db.get_or_404(StudyData, id)

    return send_file(
        sd.filepath,
        as_attachment=True,
        download_name=sd.filename,
    )


@blueprint.route("/study_data/<int:id>/delete", methods=['POST'])
def study_data_delete(id):
    sd = db.get_or_404(StudyData, id)
    delete_study_data(sd.id)

    return refresh_response()


@blueprint.route("/study_data/<int:id>/delete_mappings", methods=['POST'])
def study_data_delete_mappings(id):
    sd = db.get_or_404(StudyData, id)
    delete_mappings(sd.id)

    return refresh_response()


@blueprint.route("/study_data/<int:id>/automap", methods=['POST'])
def study_data_automap(id):
    study_data = db.get_or_404(StudyData, id)

    automap(study_data.id)

    return refresh_response()


@blueprint.route("/study_data/<int:id>/lock", methods=['POST'])
def study_data_lock(id):
    sd = db.get_or_404(StudyData, id)
    sd.locked = True

    db.session.add(sd)
    db.session.commit()

    flash(f'Study data {sd.study_name} locked')

    return refresh_response()


@blueprint.route("/study_data/<int:id>/unlock", methods=['POST'])
@must_be_admin()
def study_data_unlock(id):
    sd = db.get_or_404(StudyData, id)
    sd.locked = False

    db.session.add(sd)
    db.session.commit()

    flash(f'Study data {sd.study_name} unlocked')

    return refresh_response()


@blueprint.route("/study_data/<int:id>/export")
@must_be_admin()
def study_data_export(id):
    return create_export(id)
