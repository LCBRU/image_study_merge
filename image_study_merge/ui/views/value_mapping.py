from flask_api import status
from flask import render_template, request
from image_study_merge.model import DataDictionary, StudyDataColumn, StudyDataColumnValueMapping
from lbrc_flask.database import db
from sqlalchemy import func, or_
from image_study_merge.ui.views.forms import MappingSearchForm
from .. import blueprint


@blueprint.route("/value_mapping/<int:id>")
def value_mapping(id):
    study_data_column = StudyDataColumn.query.get_or_404(id)
    search_form = MappingSearchForm(formdata=request.args)

    choices = {
        '': DataDictionary.NOT_YET_MAPPED,
        DataDictionary.DO_NOT_IMPORT: DataDictionary.DO_NOT_IMPORT,
        DataDictionary.NO_SUITABLE_MAPPING: DataDictionary.NO_SUITABLE_MAPPING,
    }
    choices.update({value: f'{name} ({value})' for value, name in
        study_data_column.mapped_data_dictionary.choice_values.items()
    })

    q = StudyDataColumnValueMapping.query.filter(StudyDataColumnValueMapping.study_data_column_id == study_data_column.id)

    if search_form.search.data:
        q = q.filter(StudyDataColumnValueMapping.value.like(f'%{search_form.search.data}%'))

    if search_form.show_do_not_import.data != '1':
        q = q.filter(func.coalesce(StudyDataColumnValueMapping.mapping, '') != DataDictionary.DO_NOT_IMPORT)

    if search_form.show_not_yet_mapped.data != '1':
        q = q.filter(func.coalesce(StudyDataColumnValueMapping.mapping, '') != '')

    if search_form.show_no_suitable_mapping.data != '1':
        q = q.filter(func.coalesce(StudyDataColumnValueMapping.mapping, '') != DataDictionary.NO_SUITABLE_MAPPING)

    if search_form.show_mapped.data != '1':
        q = q.filter(or_(
            func.coalesce(StudyDataColumnValueMapping.mapping, '') == '',
            func.coalesce(StudyDataColumnValueMapping.mapping, '') == DataDictionary.DO_NOT_IMPORT,
        ))

    mappings = q.paginate(
            page=search_form.page.data,
            per_page=50,
            error_out=False,
        )

    return render_template(
        "ui/value_mapping/index.html",
        mappings=mappings,
        study_data_column=study_data_column,
        search_form=search_form,
        choices=choices,
        show_suggestions=search_form.show_suggestions.data,
    )


@blueprint.route("/value_mapping/update", methods=['POST'])
def value_mapping_update():
    try:
        vm = StudyDataColumnValueMapping.query.get_or_404(request.json['id'])

        vm.mapping = request.json['mapping']

        db.session.add(vm)
        db.session.commit()

        return '', status.HTTP_205_RESET_CONTENT

    except:
        return 'A problem has occured.  Please try reloading the page.', status.HTTP_500_INTERNAL_SERVER_ERROR
