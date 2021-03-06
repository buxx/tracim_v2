# -*- coding: utf-8 -*-
import io
import os

import pytest
from sqlalchemy.exc import InvalidRequestError
from wsgidav.wsgidav_app import DEFAULT_CONFIG
from tracim_backend import WebdavAppFactory
from tracim_backend.lib.core.user import UserApi
from tracim_backend.lib.webdav import TracimDomainController
from tracim_backend.tests import eq_
from tracim_backend.lib.core.notifications import DummyNotifier
from tracim_backend.lib.webdav.dav_provider import Provider
from tracim_backend.lib.webdav.resources import RootResource
from tracim_backend.models import Content
from tracim_backend.models import ContentRevisionRO
from tracim_backend.tests import StandardTest
from tracim_backend.fixtures.content import Content as ContentFixtures
from tracim_backend.fixtures.users_and_groups import Base as BaseFixture
from wsgidav import util
from unittest.mock import MagicMock


class TestWebdavFactory(StandardTest):

    config_section = 'webdav_test'

    def test_unit__initConfig__ok__nominal_case(self):
        """
        Check if config is correctly modify for wsgidav using mocked
        wsgidav and tracim conf (as dict)
        :return:
        """
        tracim_settings = self.settings
        wsgidav_setting = DEFAULT_CONFIG.copy()
        wsgidav_setting.update(
            {
               'root_path':  '',
               'acceptbasic': True,
               'acceptdigest': False,
               'defaultdigest': False,
            }
        )
        mock = MagicMock()
        mock._initConfig = WebdavAppFactory._initConfig
        mock._readConfigFile.return_value = wsgidav_setting
        mock._get_tracim_settings.return_value = tracim_settings
        config = mock._initConfig(mock)
        assert config
        assert config['acceptbasic'] is True
        assert config['acceptdigest'] is False
        assert config['defaultdigest'] is False
        # TODO - G.M - 25-05-2018 - Better check for middleware stack config
        assert 'middleware_stack' in config
        assert len(config['middleware_stack']) == 7
        assert 'root_path' in config
        assert 'provider_mapping' in config
        assert config['root_path'] in config['provider_mapping']
        assert isinstance(config['provider_mapping'][config['root_path']], Provider)  # nopep8
        assert 'domaincontroller' in config
        assert isinstance(config['domaincontroller'], TracimDomainController)

    def test_unit__readConfigFile__ok__nominal_case(self):
        tracim_settings = self.settings
        default_config_file = os.path.abspath(tracim_settings['wsgidav.config_path'])  # nopep8
        mock = MagicMock()
        mock._readConfigFile = WebdavAppFactory._readConfigFile
        webdav_config_file = mock._readConfigFile(
            mock,
            default_config_file,
            verbose=1,
        )
        assert webdav_config_file['host'] == "0.0.0.0"
        assert webdav_config_file['port'] == 3030
        assert webdav_config_file['show_history'] is True
        assert webdav_config_file['show_deleted'] is True
        assert webdav_config_file['show_archived'] is True
        assert webdav_config_file['manager_locks'] is True
        assert webdav_config_file['root_path'] == ''
        assert webdav_config_file['acceptbasic'] is True
        assert webdav_config_file['acceptdigest'] is False
        assert webdav_config_file['defaultdigest'] is False


class TestWebDav(StandardTest):
    fixtures = [BaseFixture, ContentFixtures]

    def _get_provider(self, config):
        return Provider(
            show_archived=False,
            show_deleted=False,
            show_history=False,
            app_config=config,
        )

    def _get_environ(
            self,
            provider: Provider,
            username: str,
    ) -> dict:
        return {
            'http_authenticator.username': username,
            'http_authenticator.realm': '/',
            'wsgidav.provider': provider,
            'tracim_user': self._get_user(username),
            'tracim_dbsession': self.session,
        }

    def _get_user(self, email):
        return UserApi(None,
                       self.session,
                       self.app_config
                       ).get_one_by_email(email)

    def _put_new_text_file(
            self,
            provider,
            environ,
            file_path,
            file_content,
    ):
        # This part id a reproduction of
        # wsgidav.request_server.RequestServer#doPUT

        # Grab parent folder where create file
        parentRes = provider.getResourceInst(
            util.getUriParent(file_path),
            environ,
        )
        assert parentRes, 'we should found folder for {0}'.format(file_path)

        new_resource = parentRes.createEmptyResource(
            util.getUriName(file_path),
        )
        write_object = new_resource.beginWrite(
            contentType='application/octet-stream',
        )
        write_object.write(file_content)
        write_object.close()
        new_resource.endWrite(withErrors=False)

        # Now file should exist
        return provider.getResourceInst(
            file_path,
            environ,
        )

    def test_unit__get_root__ok(self):
        provider = self._get_provider(self.app_config)
        root = provider.getResourceInst(
            '/',
            self._get_environ(
                provider,
                'bob@fsf.local',
            )
        )
        assert root, 'Path / should return a RootResource instance'
        assert isinstance(root, RootResource)

    def test_unit__list_workspaces_with_user__ok(self):
        provider = self._get_provider(self.app_config)
        root = provider.getResourceInst(
            '/',
            self._get_environ(
                provider,
                'bob@fsf.local',
            )
        )
        assert root, 'Path / should return a RootResource instance'
        assert isinstance(root, RootResource), 'Path / should return a RootResource instance'

        children = root.getMemberList()
        eq_(
            2,
            len(children),
            msg='RootResource should return 2 workspaces instead {0}'.format(
                len(children),
            )
        )

        workspaces_names = [w.name for w in children]
        assert 'Recipes' in workspaces_names, \
            'Recipes should be in names ({0})'.format(
                workspaces_names,
        )
        assert 'Others' in workspaces_names, 'Others should be in names ({0})'.format(
            workspaces_names,
        )

    def test_unit__list_workspaces_with_admin__ok(self):
        provider = self._get_provider(self.app_config)
        root = provider.getResourceInst(
            '/',
            self._get_environ(
                provider,
                'admin@admin.admin',
            )
        )
        assert root, 'Path / should return a RootResource instance'
        assert isinstance(root, RootResource), 'Path / should return a RootResource instance'

        children = root.getMemberList()
        eq_(
            2,
            len(children),
            msg='RootResource should return 3 workspaces instead {0}'.format(
                len(children),
            )
        )

        workspaces_names = [w.name for w in children]
        assert 'Recipes' in workspaces_names, 'Recipes should be in names ({0})'.format(
            workspaces_names,
        )
        assert 'Business' in workspaces_names, 'Business should be in names ({0})'.format(
            workspaces_names,
        )

    def test_unit__list_workspace_folders__ok(self):
        provider = self._get_provider(self.app_config)
        Recipes = provider.getResourceInst(
            '/Recipes/',
            self._get_environ(
                provider,
                'bob@fsf.local',
            )
        )
        assert Recipes, 'Path /Recipes should return a Wrkspace instance'

        children = Recipes.getMemberList()
        eq_(
            2,
            len(children),
            msg='Recipes should list 2 folders instead {0}'.format(
                len(children),
            ),
        )

        folders_names = [f.name for f in children]
        assert 'Salads' in folders_names, 'Salads should be in names ({0})'.format(
                folders_names,
        )
        assert 'Desserts' in folders_names, 'Desserts should be in names ({0})'.format(
                folders_names,
        )

    def test_unit__list_content__ok(self):
        provider = self._get_provider(self.app_config)
        Salads = provider.getResourceInst(
            '/Recipes/Desserts',
            self._get_environ(
                provider,
                'bob@fsf.local',
            )
        )
        assert Salads, 'Path /Salads should return a Wrkspace instance'

        children = Salads.getMemberList()
        eq_(
            5,
            len(children),
            msg='Salads should list 5 Files instead {0}'.format(
                len(children),
            ),
        )

        content_names = [c.name for c in children]
        assert 'Brownie Recipe.html' in content_names, \
            'Brownie Recipe.html should be in names ({0})'.format(
                content_names,
        )

        assert 'Best Cakesʔ.html' in content_names,\
            'Best Cakesʔ.html should be in names ({0})'.format(
                content_names,
        )
        assert 'Apple_Pie.txt' in content_names,\
            'Apple_Pie.txt should be in names ({0})'.format(content_names,)

        assert 'Fruits Desserts' in content_names, \
            'Fruits Desserts should be in names ({0})'.format(
                content_names,
        )

        assert 'Tiramisu Recipe.html' in content_names,\
            'Tiramisu Recipe.html should be in names ({0})'.format(
                content_names,
        )

    def test_unit__get_content__ok(self):
        provider = self._get_provider(self.app_config)
        pie = provider.getResourceInst(
            '/Recipes/Desserts/Apple_Pie.txt',
            self._get_environ(
                provider,
                'bob@fsf.local',
            )
        )

        assert pie, 'Apple_Pie should be found'
        eq_('Apple_Pie.txt', pie.name)

    def test_unit__delete_content__ok(self):
        provider = self._get_provider(self.app_config)
        pie = provider.getResourceInst(
            '/Recipes/Desserts/Apple_Pie.txt',
            self._get_environ(
                provider,
                'bob@fsf.local',
            )
        )
        
        content_pie = self.session.query(ContentRevisionRO) \
            .filter(Content.label == 'Apple_Pie') \
            .one()  # It must exist only one revision, cf fixtures
        eq_(
            False,
            content_pie.is_deleted,
            msg='Content should not be deleted !'
        )
        content_pie_id = content_pie.content_id

        pie.delete()

        self.session.flush()
        content_pie = self.session.query(ContentRevisionRO) \
            .filter(Content.content_id == content_pie_id) \
            .order_by(Content.revision_id.desc()) \
            .first()
        eq_(
            True,
            content_pie.is_deleted,
            msg='Content should be deleted!'
        )

        result = provider.getResourceInst(
            '/Recipes/Desserts/Apple_Pie.txt',
            self._get_environ(
                provider,
                'bob@fsf.local',
            )
        )
        eq_(None, result, msg='Result should be None instead {0}'.format(
            result
        ))

    def test_unit__create_content__ok(self):
        provider = self._get_provider(self.app_config)
        environ = self._get_environ(
            provider,
            'bob@fsf.local',
        )
        result = provider.getResourceInst(
            '/Recipes/Salads/greek_salad.txt',
            environ,
        )

        eq_(None, result, msg='Result should be None instead {0}'.format(
            result
        ))

        result = self._put_new_text_file(
            provider,
            environ,
            '/Recipes/Salads/greek_salad.txt',
            b'Greek Salad\n',
        )

        assert result, 'Result should not be None instead {0}'.format(
            result
        )
        eq_(
            b'Greek Salad\n',
            result.content.depot_file.file.read(),
            msg='fiel content should be "Greek Salad\n" but it is {0}'.format(
                result.content.depot_file.file.read()
            )
        )

    def test_unit__create_delete_and_create_file__ok(self):
        provider = self._get_provider(self.app_config)
        environ = self._get_environ(
            provider,
            'bob@fsf.local',
        )
        new_file = provider.getResourceInst(
            '/Recipes/Salads/greek_salad.txt',
            environ,
        )

        eq_(None, new_file, msg='Result should be None instead {0}'.format(
            new_file
        ))

        # create it
        new_file = self._put_new_text_file(
            provider,
            environ,
            '/Recipes/Salads/greek_salad.txt',
            b'Greek Salad\n',
        )
        assert new_file, 'Result should not be None instead {0}'.format(
            new_file
        )

        content_new_file = self.session.query(ContentRevisionRO) \
            .filter(Content.label == 'greek_salad') \
            .one()  # It must exist only one revision
        eq_(
            False,
            content_new_file.is_deleted,
            msg='Content should not be deleted!'
        )
        content_new_file_id = content_new_file.content_id

        # Delete if
        new_file.delete()

        self.session.flush()
        content_pie = self.session.query(ContentRevisionRO) \
            .filter(Content.content_id == content_new_file_id) \
            .order_by(Content.revision_id.desc()) \
            .first()
        eq_(
            True,
            content_pie.is_deleted,
            msg='Content should be deleted!'
        )

        result = provider.getResourceInst(
            '/Recipes/Salads/greek_salad.txt',
            self._get_environ(
                provider,
                'bob@fsf.local',
            )
        )
        eq_(None, result, msg='Result should be None instead {0}'.format(
            result
        ))

        # Then create it again
        new_file = self._put_new_text_file(
            provider,
            environ,
            '/Recipes/Salads/greek_salad.txt',
            b'greek_salad\n',
        )
        assert new_file, 'Result should not be None instead {0}'.format(
            new_file
        )

        # Previous file is still dleeted
        self.session.flush()
        content_pie = self.session.query(ContentRevisionRO) \
            .filter(Content.content_id == content_new_file_id) \
            .order_by(Content.revision_id.desc()) \
            .first()
        eq_(
            True,
            content_pie.is_deleted,
            msg='Content should be deleted!'
        )

        # And an other file exist for this name
        content_new_new_file = self.session.query(ContentRevisionRO) \
            .filter(Content.label == 'greek_salad') \
            .order_by(Content.revision_id.desc()) \
            .first()
        assert content_new_new_file.content_id != content_new_file_id,\
            'Contents ids should not be same!'

        eq_(
            False,
            content_new_new_file.is_deleted,
            msg='Content should not be deleted!'
        )

    def test_unit__rename_content__ok(self):
        provider = self._get_provider(self.app_config)
        environ = self._get_environ(
            provider,
            'bob@fsf.local',
        )
        pie = provider.getResourceInst(
            '/Recipes/Desserts/Apple_Pie.txt',
            environ,
        )

        content_pie = self.session.query(ContentRevisionRO) \
            .filter(Content.label == 'Apple_Pie') \
            .one()  # It must exist only one revision, cf fixtures
        assert content_pie, 'Apple_Pie should be exist'
        content_pie_id = content_pie.content_id

        pie.moveRecursive('/Recipes/Desserts/Apple_Pie_RENAMED.txt')

        # Database content is renamed
        content_pie = self.session.query(ContentRevisionRO) \
            .filter(ContentRevisionRO.content_id == content_pie_id) \
            .order_by(ContentRevisionRO.revision_id.desc()) \
            .first()
        eq_(
            'Apple_Pie_RENAMED',
            content_pie.label,
            msg='File should be labeled Apple_Pie_RENAMED, not {0}'.format(
                content_pie.label
            )
        )

    def test_unit__move_content__ok(self):
        provider = self._get_provider(self.app_config)
        environ = self._get_environ(
            provider,
            'bob@fsf.local',
        )
        pie = provider.getResourceInst(
            '/Recipes/Desserts/Apple_Pie.txt',
            environ,
        )

        content_pie = self.session.query(ContentRevisionRO) \
            .filter(Content.label == 'Apple_Pie') \
            .one()  # It must exist only one revision, cf fixtures
        assert content_pie, 'Apple_Pie should be exist'
        content_pie_id = content_pie.content_id
        content_pie_parent = content_pie.parent
        eq_(
            content_pie_parent.label,
            'Desserts',
            msg='field parent should be Desserts',
        )

        pie.moveRecursive('/Recipes/Salads/Apple_Pie.txt')  # move in f2

        # Database content is moved
        content_pie = self.session.query(ContentRevisionRO) \
            .filter(ContentRevisionRO.content_id == content_pie_id) \
            .order_by(ContentRevisionRO.revision_id.desc()) \
            .first()

        assert content_pie.parent.label != content_pie_parent.label,\
            'file should be moved in Salads but is in {0}'.format(
                content_pie.parent.label
        )

    def test_unit__move_and_rename_content__ok(self):
        provider = self._get_provider(self.app_config)
        environ = self._get_environ(
            provider,
            'bob@fsf.local',
        )
        pie = provider.getResourceInst(
            '/Recipes/Desserts/Apple_Pie.txt',
            environ,
        )

        content_pie = self.session.query(ContentRevisionRO) \
            .filter(Content.label == 'Apple_Pie') \
            .one()  # It must exist only one revision, cf fixtures
        assert content_pie, 'Apple_Pie should be exist'
        content_pie_id = content_pie.content_id
        content_pie_parent = content_pie.parent
        eq_(
            content_pie_parent.label,
            'Desserts',
            msg='field parent should be Desserts',
        )

        pie.moveRecursive('/Others/Infos/Apple_Pie_RENAMED.txt')

        # Database content is moved
        content_pie = self.session.query(ContentRevisionRO) \
            .filter(ContentRevisionRO.content_id == content_pie_id) \
            .order_by(ContentRevisionRO.revision_id.desc()) \
            .first()
        assert content_pie.parent.label != content_pie_parent.label,\
            'file should be moved in Recipesf2 but is in {0}'.format(
                content_pie.parent.label
        )
        eq_(
            'Apple_Pie_RENAMED',
            content_pie.label,
            msg='File should be labeled Apple_Pie_RENAMED, not {0}'.format(
                content_pie.label
            )
        )

    def test_unit__move_content__ok__another_workspace(self):
        provider = self._get_provider(self.app_config)
        environ = self._get_environ(
            provider,
            'bob@fsf.local',
        )
        content_to_move_res = provider.getResourceInst(
            '/Recipes/Desserts/Apple_Pie.txt',
            environ,
        )

        content_to_move = self.session.query(ContentRevisionRO) \
            .filter(Content.label == 'Apple_Pie') \
            .one()  # It must exist only one revision, cf fixtures
        assert content_to_move, 'Apple_Pie should be exist'
        content_to_move_id = content_to_move.content_id
        content_to_move_parent = content_to_move.parent
        eq_(
            content_to_move_parent.label,
            'Desserts',
            msg='field parent should be Desserts',
        )

        content_to_move_res.moveRecursive('/Others/Infos/Apple_Pie.txt')  # move in Business, f1

        # Database content is moved
        content_to_move = self.session.query(ContentRevisionRO) \
            .filter(ContentRevisionRO.content_id == content_to_move_id) \
            .order_by(ContentRevisionRO.revision_id.desc()) \
            .first()

        assert content_to_move.parent, 'Content should have a parent'

        assert content_to_move.parent.label == 'Infos',\
            'file should be moved in Infos but is in {0}'.format(
                content_to_move.parent.label
        )

    def test_unit__update_content__ok(self):
        provider = self._get_provider(self.app_config)
        environ = self._get_environ(
            provider,
            'bob@fsf.local',
        )
        result = provider.getResourceInst(
            '/Recipes/Salads/greek_salad.txt',
            environ,
        )

        eq_(None, result, msg='Result should be None instead {0}'.format(
            result
        ))

        result = self._put_new_text_file(
            provider,
            environ,
            '/Recipes/Salads/greek_salad.txt',
            b'hello\n',
        )

        assert result, 'Result should not be None instead {0}'.format(
            result
        )
        eq_(
            b'hello\n',
            result.content.depot_file.file.read(),
            msg='fiel content should be "hello\n" but it is {0}'.format(
                result.content.depot_file.file.read()
            )
        )

        # ReInit DummyNotifier counter
        DummyNotifier.send_count = 0

        # Update file content
        write_object = result.beginWrite(
            contentType='application/octet-stream',
        )
        write_object.write(b'An other line')
        write_object.close()
        result.endWrite(withErrors=False)

        eq_(
            1,
            DummyNotifier.send_count,
            msg='DummyNotifier should send 1 mail, not {}'.format(
                DummyNotifier.send_count
            ),
        )
