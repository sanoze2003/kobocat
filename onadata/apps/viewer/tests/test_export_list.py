# coding: utf-8
import os
import unittest

from django.urls import reverse

from onadata.apps.main.tests.test_base import TestBase
from onadata.apps.viewer.models.export import Export
from onadata.apps.main.models.meta_data import MetaData
from onadata.apps.viewer.views import export_list


class TestExportList(TestBase):

    def setUp(self):
        super().setUp()
        self._publish_transportation_form()
        survey = self.surveys[0]
        self._make_submission(
            os.path.join(
                self.this_directory, 'fixtures', 'transportation',
                'instances', survey, survey + '.xml'))

    def test_unauthorised_users_cannot_export_form_data(self):
        kwargs = {'username': self.user.username,
                  'id_string': self.xform.id_string,
                  'export_type': Export.CSV_EXPORT}

        url = reverse(export_list, kwargs=kwargs)
        response = self.client.get(url)

        # check that the 'New Export' button is not being rendered
        self.assertNotIn(
            '<input title="" data-original-title="" \
            class="btn large btn-primary" \
            value="New Export" type="submit">', response.content.decode())
        self.assertEqual(response.status_code, 200)

    @unittest.skip('Fails under Django 1.6')
    def test_csv_export_list(self):
        kwargs = {'username': self.user.username.upper(),
                  'id_string': self.xform.id_string.upper(),
                  'export_type': Export.CSV_EXPORT}

        # test csv
        url = reverse(export_list, kwargs=kwargs)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_xls_export_list(self):
        kwargs = {'username': self.user.username,
                  'id_string': self.xform.id_string,
                  'export_type': Export.XLS_EXPORT}
        url = reverse(export_list, kwargs=kwargs)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_kml_export_list(self):
        kwargs = {'username': self.user.username,
                  'id_string': self.xform.id_string,
                  'export_type': Export.KML_EXPORT}
        url = reverse(export_list, kwargs=kwargs)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_zip_export_list(self):
        kwargs = {'username': self.user.username,
                  'id_string': self.xform.id_string,
                  'export_type': Export.ZIP_EXPORT}
        url = reverse(export_list, kwargs=kwargs)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class TestDataExportURL(TestBase):

    def setUp(self):
        super().setUp()
        self._publish_transportation_form()

    def _filename_from_disposition(self, content_disposition):
        filename_pos = content_disposition.index('filename=')
        self.assertTrue(filename_pos != -1)
        return content_disposition[filename_pos + len('filename='):]

    def test_csv_export_url(self):
        self._submit_transport_instance()
        url = reverse('csv_export', kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string,
        })
        response = self.client.get(url)
        headers = dict(response.items())
        self.assertEqual(headers['Content-Type'], 'application/csv')
        content_disposition = headers['Content-Disposition']
        filename = self._filename_from_disposition(content_disposition)
        basename, ext = os.path.splitext(filename)
        self.assertEqual(ext, '.csv')

    def test_csv_export_url_without_records(self):
        # csv using the pandas path can throw a NoRecordsFound Exception -
        # handle it gracefully
        url = reverse('csv_export', kwargs={
            'username': self.user.username,
            'id_string': self.xform.id_string,
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    @unittest.skip('Fails under Django 1.6')
    def test_xls_export_url(self):
        self._submit_transport_instance()
        url = reverse('xls_export', kwargs={
            'username': self.user.username.upper(),
            'id_string': self.xform.id_string.upper(),
        })
        response = self.client.get(url)
        headers = dict(response.items())
        self.assertEqual(headers['Content-Type'],
                         'application/vnd.openxmlformats')
        content_disposition = headers['Content-Disposition']
        filename = self._filename_from_disposition(content_disposition)
        basename, ext = os.path.splitext(filename)
        self.assertEqual(ext, '.xlsx')
