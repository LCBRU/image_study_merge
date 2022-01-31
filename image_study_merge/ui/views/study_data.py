from .. import blueprint
from flask import render_template, request, flash, redirect, url_for, send_file
from lbrc_flask.forms import SearchForm, FlashingForm, FileField, ConfirmForm
from image_study_merge.services import automap, extract_study_data
from image_study_merge.model import StudyData, study_data_factory
from flask_wtf.file import FileRequired
from lbrc_flask.database import db
from wtforms import StringField
from wtforms.validators import Length, DataRequired


class UploadStudyDataForm(FlashingForm):
    study_name = StringField("Study Name", validators=[Length(max=100), DataRequired()])
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

    q = StudyData.query

    if search_form.search.data:
        q = q.filter(StudyData.filename.like(f'%{search_form.search.data}%'))

    study_datas = q.paginate(
        page=search_form.page.data,
        per_page=5,
        error_out=False,
    )

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

        return redirect(url_for('ui.index'))

    return render_template(
        "ui/study_data_upload.html",
        form=form,
    )


@blueprint.route("/study_data/download/<int:id>")
def study_data_download(id):
    sd = StudyData.query.get_or_404(id)

    return send_file(
        sd.filepath,
        as_attachment=True,
        download_name=sd.filename,
    )


@blueprint.route("/study_data/delete", methods=['POST'])
def study_data_delete():
    form = ConfirmForm()

    if form.validate_on_submit():
        sd = StudyData.query.get_or_404(form.id.data)
        db.session.delete(sd)
        db.session.commit()

    return redirect(url_for('ui.index'))


@blueprint.route("/study_data/automap/<int:id>")
def study_data_automap(id):
    study_data = StudyData.query.get_or_404(id)

    automap(study_data)

    return redirect(url_for('ui.index'))
