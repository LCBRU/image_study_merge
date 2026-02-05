import pytest
from lbrc_flask.pytest.testers import IndexTester, RequiresLoginTester, PanelListContentAsserter, PagedSize20ResultSet
from image_study_merge.model import StudyDataColumn


class ColumnMappingIndexTester:
    @property
    def endpoint(self):
        return 'ui.column_mapping'

    @pytest.fixture(autouse=True)
    def set_existing(self, client, faker):
        self.study_data = faker.study_data().get(save=True)
        self.parameters['id'] = self.study_data.id


class ColumnMappingRowContentAsserter(PanelListContentAsserter):
    def assert_row_details(self, row, expected_result: StudyDataColumn):
        assert row is not None
        assert expected_result is not None


class TestColumnMappingRequiresLogin(ColumnMappingIndexTester, RequiresLoginTester):
    ...


class TestColumnMapping(ColumnMappingIndexTester, IndexTester):
    @property
    def content_asserter(self):
        return ColumnMappingRowContentAsserter
    
    @pytest.mark.parametrize("item_count", PagedSize20ResultSet.test_page_edges())
    @pytest.mark.parametrize("current_page", PagedSize20ResultSet.test_current_pages())
    def test__get__no_filters(self, item_count, current_page):
        study_data_column = self.faker.study_data_column().get_list(
            save=True,
            item_count=item_count,
            study_data_id=self.study_data.id,
        )

        self.parameters['page'] = current_page

        resp = self.get()

        self.assert_all(
            page_count_helper=PagedSize20ResultSet(page=current_page, expected_results=study_data_column),
            resp=resp,
        )

    # Todo: Add more tests for filtering, sorting, etc.
