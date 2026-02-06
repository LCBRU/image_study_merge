from functools import cache
from pathlib import Path
from random import choice
from typing import Optional
from faker.providers import BaseProvider
from lbrc_flask.pytest.faker import FakeCreator, FakeCreatorArgs, UserCreator
from image_study_merge.model import DataDictionary, StudyData, StudyDataColumn, StudyDataColumnValueMapping, StudyDataColumnSuggestion, StudyDataRow, StudyDataRowData


class StudyDataCreator(FakeCreator):
    cls = StudyData
    
    def _create_item(self, save, args: FakeCreatorArgs):
        params = dict(
            study_name = args.get('study_name', self.faker.unique.word()),
            filename = args.get('filename', self.faker.file_name(extension=choice(['csv']))),
            updating = args.get('updating', False),
            deleted = args.get('deleted', False),
            locked = args.get('locked', False),
        )

        if params.get('filename') is not None:
            params['extension'] = Path(params['filename']).suffix

        return self.cls(**params)

    def assert_equal(self, expected: StudyData, actual: StudyData):
        assert expected.study_name == actual.study_name
        assert expected.filename == actual.filename
        assert expected.extension == actual.extension
        assert expected.updating == actual.updating
        assert expected.deleted == actual.deleted
        assert expected.locked == actual.locked


class StudyDataColumnCreator(FakeCreator):
    cls = StudyDataColumn
    
    def _create_item(self, save, args: FakeCreatorArgs):
        params = dict(
            column_number = args.get('column_number', self.faker.unique.pyint()),
            name = args.get('name', self.faker.unique.word()),
        )

        args.set_params_with_object(params, 'study_data', creator=self.faker.study_data())

        if 'mapped_data_dictionary' in args:
            value: DataDictionary = args.get('mapped_data_dictionary')

            if value.field_name is not None:
                params['mapping'] = value.field_name
            else:
                params['mapped_data_dictionary'] = value
        elif 'mapping' in args:
            params['mapping'] = args.get('mapping')
        else:
            params['mapped_data_dictionary'] = self.faker.data_dictionary().get(save=save)

        return self.cls(**params)

    def assert_equal(self, expected: StudyDataColumn, actual: StudyDataColumn):
        assert expected.column_number == actual.column_number
        assert expected.name == actual.name
        assert self._get_mapping(expected) == self._get_mapping(actual)

    def _get_mapping(self, col: StudyDataColumn) -> Optional[str]:
        if col.mapping:
            return col.mapping
        
        if col.mapped_data_dictionary:
            return col.mapped_data_dictionary.field_name


class StudyDataColumnValueMappingCreator(FakeCreator):
    cls = StudyDataColumnValueMapping
    
    def _create_item(self, save, args: FakeCreatorArgs):
        params = dict(
            value = args.get('value', self.faker.unique.word()),
            mapping = args.get('mapping', self.faker.unique.word()),
        )

        args.set_params_with_object(params, 'study_data_column', creator=self.faker.study_data_column())

        return self.cls(**params)

    def assert_equal(self, expected: StudyDataColumnValueMapping, actual: StudyDataColumnValueMapping):
        assert expected.column_number == actual.column_number
        assert expected.name == actual.name
        assert self._get_column_id(expected) == self._get_column_id(actual)

    def _get_column_id(self, mapping: StudyDataColumnValueMapping) -> Optional[int]:
        if mapping.study_data_column_id:
            return mapping.study_data_column_id
        
        if mapping.study_data_column:
            return mapping.study_data_column.id


class StudyDataColumnSuggestion(FakeCreator):
    cls = StudyDataColumnSuggestion
    
    def _create_item(self, save, args: FakeCreatorArgs):
        params = dict(
            match_score = args.get('match_score', self.faker.unique.pyint()),
        )

        args.set_params_with_object(params, 'study_data_column', creator=self.faker.study_data_column())

        if 'data_dictionary' in args:
            value: DataDictionary = args.get('data_dictionary')

            if value.field_name is not None:
                params['mapping'] = value.field_name
            else:
                params['data_dictionary'] = value
        elif 'mapping' in args:
            params['mapping'] = args.get('mapping')
        else:
            params['data_dictionary'] = self.faker.data_dictionary().get(save=save)

        return self.cls(**params)

    def assert_equal(self, expected: StudyDataColumnSuggestion, actual: StudyDataColumnSuggestion):
        assert expected.match_score == actual.match_score
        assert self._get_column_id(expected) == self._get_column_id(actual)

    def _get_column_id(self, suggestion: StudyDataColumnSuggestion) -> Optional[int]:
        if suggestion.study_data_column_id:
            return suggestion.study_data_column_id
        
        if suggestion.study_data_column:
            return suggestion.study_data_column.id

    def _get_mapping(self, col: StudyDataColumnSuggestion) -> Optional[str]:
        if col.mapping:
            return col.mapping
        
        if col.data_dictionary:
            return col.data_dictionary.field_name


class StudyDataRowCreator(FakeCreator):
    cls = StudyDataRow
    
    def _create_item(self, save, args: FakeCreatorArgs):
        params = dict()

        args.set_params_with_object(params, 'study_data_column', creator=self.faker.study_data_column())

        return self.cls(**params)

    def assert_equal(self, expected: StudyDataRow, actual: StudyDataRow):
        assert self._get_column_id(expected) == self._get_column_id(actual)

    def _get_column_id(self, mapping: StudyDataRow) -> Optional[int]:
        if mapping.study_data_column_id:
            return mapping.study_data_column_id
        
        if mapping.study_data_column:
            return mapping.study_data_column.id


class StudyDataRowDataCreator(FakeCreator):
    cls = StudyDataRowData
    
    def _create_item(self, save, args: FakeCreatorArgs):
        params = dict(
            value = args.get('value', self.faker.unique.pystr())
        )

        args.set_params_with_object(params, 'study_data_row', creator=self.faker.study_data_row())
        args.set_params_with_object(params, 'study_data_column', creator=self.faker.study_data_column())

        return self.cls(**params)

    def assert_equal(self, expected: StudyDataRow, actual: StudyDataRow):
        assert expected.value == actual.value
        assert self._get_column_id(expected) == self._get_column_id(actual)
        assert self._get_row_id(expected) == self._get_row_id(actual)

    def _get_column_id(self, mapping: StudyDataRowData) -> Optional[int]:
        if mapping.study_data_column_id:
            return mapping.study_data_column_id
        
        if mapping.study_data_column:
            return mapping.study_data_column.id

    def _get_row_id(self, mapping: StudyDataRowData) -> Optional[int]:
        if mapping.study_data_row_id:
            return mapping.study_data_row_id
        
        if mapping.study_data_row:
            return mapping.study_data_row.id


class DataDictionaryCreator(FakeCreator):
    cls = DataDictionary
    
    def _create_item(self, save, args: FakeCreatorArgs):
        params = dict(
            field_number = args.get('field_number', self.faker.unique.pyint()),
            field_name = args.get('field_name', self.faker.unique.word()),
            form_name = args.get('form_name', self.faker.unique.word()),
            section_name = args.get('section_name', self.faker.unique.word()),
            field_type = args.get('field_type', self.faker.unique.word()),
            field_label = args.get('field_label', self.faker.unique.word()),
            field_note = args.get('field_note', self.faker.sentence()),
            text_validation_type = args.get('text_validation_type', ''),
            text_validation_min = args.get('text_validation_min', ''),
            text_validation_max = args.get('text_validation_max', ''),
        )

        if 'choice_list' in args:
            params['choices'] = '|'.join(args.get('choice_list'))
        else:
            params['choices'] = args.get('choices', '')

        return self.cls(**params)

    def assert_equal(self, expected: DataDictionary, actual: DataDictionary):
        assert expected.field_number == actual.field_number
        assert expected.field_name == actual.field_name
        assert expected.form_name == actual.form_name
        assert expected.section_name == actual.section_name
        assert expected.field_type == actual.field_type
        assert expected.field_label == actual.field_label
        assert expected.field_note == actual.field_note
        assert expected.text_validation_type == actual.text_validation_type
        assert expected.text_validation_max == actual.text_validation_max
        assert expected.text_validation_min == actual.text_validation_min


class ImageStudyMergeProvider(BaseProvider):
    @cache
    def study_data(self):
        return StudyDataCreator(self)

    @cache
    def study_data_column(self):
        return StudyDataColumnCreator(self)
    
    @cache
    def study_data_column_value_mapping(self):
        return StudyDataColumnValueMappingCreator(self)
    
    @cache
    def study_data_column_suggestion(self):
        return StudyDataColumnSuggestion(self)
    
    @cache
    def study_data_row(self):
        return StudyDataRowCreator(self)
    
    @cache
    def study_data_row_data(self):
        return StudyDataRowDataCreator(self)
    
    @cache
    def data_dictionary(self):
        return DataDictionaryCreator(self)
    
    @cache
    def user(self):
        return UserCreator(self)

