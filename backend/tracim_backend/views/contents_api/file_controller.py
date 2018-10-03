# coding=utf-8
import typing

import transaction
from depot.manager import DepotManager
from preview_generator.exception import UnavailablePreviewType
from pyramid.config import Configurator

from hapic.data import HapicFile
from tracim_backend.app_models.contents import CONTENT_TYPES
from tracim_backend.app_models.contents import FILE_TYPE
from tracim_backend.exceptions import ContentLabelAlreadyUsedHere
from tracim_backend.exceptions import ContentNotFound
from tracim_backend.exceptions import EmptyLabelNotAllowed
from tracim_backend.exceptions import PageOfPreviewNotFound
from tracim_backend.exceptions import ParentNotFound
from tracim_backend.exceptions import PreviewDimNotAllowed
from tracim_backend.exceptions import UnavailablePreview
from tracim_backend.extensions import hapic
from tracim_backend.lib.core.content import ContentApi
from tracim_backend.lib.utils.authorization import require_content_types
from tracim_backend.lib.utils.authorization import require_workspace_role
from tracim_backend.lib.utils.request import TracimRequest
from tracim_backend.models.context_models import ContentInContext
from tracim_backend.models.context_models import RevisionInContext
from tracim_backend.models.data import ActionDescription
from tracim_backend.models.data import UserRoleInWorkspace
from tracim_backend.models.revision_protection import new_revision
from tracim_backend.views.controllers import Controller
from tracim_backend.views.core_api.schemas import AllowedJpgPreviewDimSchema
from tracim_backend.views.core_api.schemas import ContentDigestSchema
from tracim_backend.views.core_api.schemas import ContentPreviewSizedPathSchema
from tracim_backend.views.core_api.schemas import FileContentModifySchema
from tracim_backend.views.core_api.schemas import FileContentSchema
from tracim_backend.views.core_api.schemas import FileQuerySchema
from tracim_backend.views.core_api.schemas import FileRevisionSchema
from tracim_backend.views.core_api.schemas import FileSchema
from tracim_backend.views.core_api.schemas import NoContentSchema
from tracim_backend.views.core_api.schemas import PageQuerySchema
from tracim_backend.views.core_api.schemas import ParentIdSchema
from tracim_backend.views.core_api.schemas import \
    RevisionPreviewSizedPathSchema
from tracim_backend.views.core_api.schemas import SetContentStatusSchema
from tracim_backend.views.core_api.schemas import \
    WorkspaceAndContentIdPathSchema
from tracim_backend.views.core_api.schemas import \
    WorkspaceAndContentRevisionIdPathSchema
from tracim_backend.views.core_api.schemas import WorkspaceIdPathSchema

try:  # Python 3.5+
    from http import HTTPStatus
except ImportError:
    from http import client as HTTPStatus


SWAGGER_TAG__FILE_ENDPOINTS = 'Files'


class FileController(Controller):
    """
    Endpoints for File Content
    """

    # File data
    @hapic.with_api_doc(tags=[SWAGGER_TAG__FILE_ENDPOINTS])
    @require_workspace_role(UserRoleInWorkspace.CONTRIBUTOR)
    @hapic.input_path(WorkspaceIdPathSchema())
    @hapic.input_files(FileSchema())
    @hapic.input_forms(ParentIdSchema())
    @hapic.output_body(ContentDigestSchema())
    # TODO - G.M - 2018-07-24 - Use hapic for input file
    def create_file(self, context, request: TracimRequest, hapic_data=None):
        """
        Create a file .This will create 2 new
        revision.
        """
        app_config = request.registry.settings['CFG']
        api = ContentApi(
            show_archived=True,
            show_deleted=True,
            current_user=request.current_user,
            session=request.dbsession,
            config=app_config,
        )
        file = hapic_data.files['files']
        parent_id = hapic_data.forms.get('parent_id') or 0  # FDV
        api = ContentApi(
            current_user=request.current_user,
            session=request.dbsession,
            config=app_config
        )

        parent = None
        if parent_id:
            try:
                parent = api.get_one(content_id=parent_id, content_type=CONTENT_TYPES.Any_SLUG)  # nopep8
            except ContentNotFound as exc:
                raise ParentNotFound(
                    'Parent with content_id {} not found'.format(parent_id)
                ) from exc
        content = api.create(
            filename=file.filename,
            content_type_slug=FILE_TYPE,
            workspace=request.current_workspace,
            parent=parent,
        )
        api.save(content, ActionDescription.CREATION)
        with new_revision(
                session=request.dbsession,
                tm=transaction.manager,
                content=content
        ):
            api.update_file_data(
                content,
                new_filename=file.filename,
                new_mimetype=file.type,
                new_content=file.file,
            )

        return api.get_content_in_context(content)

    @hapic.with_api_doc(tags=[SWAGGER_TAG__FILE_ENDPOINTS])
    @require_workspace_role(UserRoleInWorkspace.CONTRIBUTOR)
    @require_content_types([FILE_TYPE])
    @hapic.input_path(WorkspaceAndContentIdPathSchema())
    # TODO - G.M - 2018-07-24 - Use hapic for input file
    @hapic.output_body(NoContentSchema(), default_http_code=HTTPStatus.NO_CONTENT)  # nopep8
    def upload_file(self, context, request: TracimRequest, hapic_data=None):
        """
        Upload a new version of raw file of content. This will create a new
        revision.
        """
        app_config = request.registry.settings['CFG']
        api = ContentApi(
            show_archived=True,
            show_deleted=True,
            current_user=request.current_user,
            session=request.dbsession,
            config=app_config,
        )
        content = api.get_one(
            hapic_data.path.content_id,
            content_type=CONTENT_TYPES.Any_SLUG
        )
        file = request.POST['files']
        with new_revision(
                session=request.dbsession,
                tm=transaction.manager,
                content=content
        ):
            api.update_file_data(
                content,
                new_filename=file.filename,
                new_mimetype=file.type,
                new_content=file.file,
            )

        return

    @hapic.with_api_doc(tags=[SWAGGER_TAG__FILE_ENDPOINTS])
    @require_workspace_role(UserRoleInWorkspace.READER)
    @require_content_types([FILE_TYPE])
    @hapic.input_query(FileQuerySchema())
    @hapic.input_path(WorkspaceAndContentIdPathSchema())
    @hapic.output_file([])
    def download_file(self, context, request: TracimRequest, hapic_data=None):
        """
        Download raw file of last revision of content.
        """
        app_config = request.registry.settings['CFG']
        api = ContentApi(
            show_archived=True,
            show_deleted=True,
            current_user=request.current_user,
            session=request.dbsession,
            config=app_config,
        )
        content = api.get_one(
            hapic_data.path.content_id,
            content_type=CONTENT_TYPES.Any_SLUG
        )
        file = DepotManager.get().get(content.depot_file)
        return HapicFile(
            file_object=file,
            mimetype=file.content_type,
            filename=content.file_name,
            as_attachment=hapic_data.query.force_download
        )

    @hapic.with_api_doc(tags=[SWAGGER_TAG__FILE_ENDPOINTS])
    @require_workspace_role(UserRoleInWorkspace.READER)
    @require_content_types([FILE_TYPE])
    @hapic.input_query(FileQuerySchema())
    @hapic.input_path(WorkspaceAndContentRevisionIdPathSchema())
    @hapic.output_file([])
    def download_revisions_file(self, context, request: TracimRequest, hapic_data=None):  # nopep8
        """
        Download raw file for specific revision of content.
        """
        app_config = request.registry.settings['CFG']
        api = ContentApi(
            show_archived=True,
            show_deleted=True,
            current_user=request.current_user,
            session=request.dbsession,
            config=app_config,
        )
        content = api.get_one(
            hapic_data.path.content_id,
            content_type=CONTENT_TYPES.Any_SLUG
        )
        revision = api.get_one_revision(
            revision_id=hapic_data.path.revision_id,
            content=content
        )
        file = DepotManager.get().get(revision.depot_file)
        return HapicFile(
            file_object=file,
            mimetype=file.content_type,
            filename=revision.file_name,
            as_attachment=hapic_data.query.force_download
        )

    # preview
    # pdf
    @hapic.with_api_doc(tags=[SWAGGER_TAG__FILE_ENDPOINTS])
    @require_workspace_role(UserRoleInWorkspace.READER)
    @require_content_types([FILE_TYPE])
    @hapic.handle_exception(UnavailablePreviewType, HTTPStatus.BAD_REQUEST)
    @hapic.handle_exception(UnavailablePreview, HTTPStatus.BAD_REQUEST)
    @hapic.handle_exception(PageOfPreviewNotFound, HTTPStatus.BAD_REQUEST)
    @hapic.input_query(PageQuerySchema())
    @hapic.input_path(WorkspaceAndContentIdPathSchema())
    @hapic.output_file([])
    def preview_pdf(self, context, request: TracimRequest, hapic_data=None):
        """
        Obtain a specific page pdf preview of last revision of content.
        """
        app_config = request.registry.settings['CFG']
        api = ContentApi(
            show_archived=True,
            show_deleted=True,
            current_user=request.current_user,
            session=request.dbsession,
            config=app_config,
        )
        content = api.get_one(
            hapic_data.path.content_id,
            content_type=CONTENT_TYPES.Any_SLUG
        )
        pdf_preview_path = api.get_pdf_preview_path(
            content.content_id,
            content.revision_id,
            page_number=hapic_data.query.page
        )
        filename = "{}_page_{}.pdf".format(content.label, hapic_data.query.page)
        return HapicFile(
            file_path=pdf_preview_path,
            filename=filename,
            as_attachment=hapic_data.query.force_download
        )

    @hapic.with_api_doc(tags=[SWAGGER_TAG__FILE_ENDPOINTS])
    @require_workspace_role(UserRoleInWorkspace.READER)
    @require_content_types([FILE_TYPE])
    @hapic.handle_exception(UnavailablePreview, HTTPStatus.BAD_REQUEST)
    @hapic.handle_exception(UnavailablePreviewType, HTTPStatus.BAD_REQUEST)
    @hapic.input_query(FileQuerySchema())
    @hapic.input_path(WorkspaceAndContentIdPathSchema())
    @hapic.output_file([])
    def preview_pdf_full(self, context, request: TracimRequest, hapic_data=None):  # nopep8
        """
        Obtain a full pdf preview (all page) of last revision of content.
        """
        app_config = request.registry.settings['CFG']
        api = ContentApi(
            show_archived=True,
            show_deleted=True,
            current_user=request.current_user,
            session=request.dbsession,
            config=app_config,
        )
        content = api.get_one(
            hapic_data.path.content_id,
            content_type=CONTENT_TYPES.Any_SLUG
        )
        pdf_preview_path = api.get_full_pdf_preview_path(content.revision_id)
        filename = "{label}.pdf".format(label=content.label)
        return HapicFile(
            file_path=pdf_preview_path,
            filename=filename,
            as_attachment=hapic_data.query.force_download
        )

    @hapic.with_api_doc(tags=[SWAGGER_TAG__FILE_ENDPOINTS])
    @require_workspace_role(UserRoleInWorkspace.READER)
    @require_content_types([FILE_TYPE])
    @hapic.handle_exception(UnavailablePreview, HTTPStatus.BAD_REQUEST)
    @hapic.handle_exception(UnavailablePreviewType, HTTPStatus.BAD_REQUEST)
    @hapic.input_path(WorkspaceAndContentRevisionIdPathSchema())
    @hapic.input_query(FileQuerySchema())
    @hapic.output_file([])
    def preview_pdf_full_revision(self, context, request: TracimRequest, hapic_data=None):  # nopep8
        """
        Obtain full pdf preview of a specific revision of content.
        """
        app_config = request.registry.settings['CFG']
        api = ContentApi(
            show_archived=True,
            show_deleted=True,
            current_user=request.current_user,
            session=request.dbsession,
            config=app_config,
        )
        content = api.get_one(
            hapic_data.path.content_id,
            content_type=CONTENT_TYPES.Any_SLUG
        )
        revision = api.get_one_revision(
            revision_id=hapic_data.path.revision_id,
            content=content
        )
        pdf_preview_path = api.get_full_pdf_preview_path(
            revision.revision_id,
        )
        filename = "{label}.pdf".format(label=revision.label)
        return HapicFile(
            file_path=pdf_preview_path,
            filename=filename,
            as_attachment=hapic_data.query.force_download
        )

    @hapic.with_api_doc(tags=[SWAGGER_TAG__FILE_ENDPOINTS])
    @require_workspace_role(UserRoleInWorkspace.READER)
    @require_content_types([FILE_TYPE])
    @hapic.handle_exception(UnavailablePreview, HTTPStatus.BAD_REQUEST)
    @hapic.handle_exception(UnavailablePreviewType, HTTPStatus.BAD_REQUEST)
    @hapic.input_path(WorkspaceAndContentRevisionIdPathSchema())
    @hapic.input_query(PageQuerySchema())
    @hapic.output_file([])
    def preview_pdf_revision(self, context, request: TracimRequest, hapic_data=None):  # nopep8
        """
        Obtain a specific page pdf preview of a specific revision of content.
        """
        app_config = request.registry.settings['CFG']
        api = ContentApi(
            show_archived=True,
            show_deleted=True,
            current_user=request.current_user,
            session=request.dbsession,
            config=app_config,
        )
        content = api.get_one(
            hapic_data.path.content_id,
            content_type=CONTENT_TYPES.Any_SLUG
        )
        revision = api.get_one_revision(
            revision_id=hapic_data.path.revision_id,
            content=content
        )
        pdf_preview_path = api.get_pdf_preview_path(
            revision.content_id,
            revision.revision_id,
            page_number=hapic_data.query.page
        )
        filename = "{label}_page_{page_number}.pdf".format(
            label=content.label,
            page_number=hapic_data.query.page
        )
        return HapicFile(
            file_path=pdf_preview_path,
            filename=filename,
            as_attachment=hapic_data.query.force_download
        )

    # jpg
    @hapic.with_api_doc(tags=[SWAGGER_TAG__FILE_ENDPOINTS])
    @require_workspace_role(UserRoleInWorkspace.READER)
    @require_content_types([FILE_TYPE])
    @hapic.handle_exception(UnavailablePreview, HTTPStatus.BAD_REQUEST)
    @hapic.handle_exception(PageOfPreviewNotFound, HTTPStatus.BAD_REQUEST)
    @hapic.input_path(WorkspaceAndContentIdPathSchema())
    @hapic.input_query(PageQuerySchema())
    @hapic.output_file([])
    def preview_jpg(self, context, request: TracimRequest, hapic_data=None):
        """
        Obtain normally sied jpg preview of last revision of content.
        """
        app_config = request.registry.settings['CFG']
        api = ContentApi(
            show_archived=True,
            show_deleted=True,
            current_user=request.current_user,
            session=request.dbsession,
            config=app_config,
        )
        content = api.get_one(
            hapic_data.path.content_id,
            content_type=CONTENT_TYPES.Any_SLUG
        )
        allowed_dim = api.get_jpg_preview_allowed_dim()
        jpg_preview_path = api.get_jpg_preview_path(
            content_id=content.content_id,
            revision_id=content.revision_id,
            page_number=hapic_data.query.page,
            width=allowed_dim.dimensions[0].width,
            height=allowed_dim.dimensions[0].height,
        )
        filename = "{label}_page_{page_number}.jpg".format(
            label=content.label,
            page_number=hapic_data.query.page
        )
        return HapicFile(
            file_path=jpg_preview_path,
            filename=filename,
            as_attachment=hapic_data.query.force_download
        )

    @hapic.with_api_doc(tags=[SWAGGER_TAG__FILE_ENDPOINTS])
    @require_workspace_role(UserRoleInWorkspace.READER)
    @require_content_types([FILE_TYPE])
    @hapic.handle_exception(UnavailablePreview, HTTPStatus.BAD_REQUEST)
    @hapic.handle_exception(PageOfPreviewNotFound, HTTPStatus.BAD_REQUEST)
    @hapic.handle_exception(PreviewDimNotAllowed, HTTPStatus.BAD_REQUEST)
    @hapic.input_query(PageQuerySchema())
    @hapic.input_path(ContentPreviewSizedPathSchema())
    @hapic.output_file([])
    def sized_preview_jpg(self, context, request: TracimRequest, hapic_data=None):  # nopep8
        """
        Obtain resized jpg preview of last revision of content.
        """
        app_config = request.registry.settings['CFG']
        api = ContentApi(
            show_archived=True,
            show_deleted=True,
            current_user=request.current_user,
            session=request.dbsession,
            config=app_config,
        )
        content = api.get_one(
            hapic_data.path.content_id,
            content_type=CONTENT_TYPES.Any_SLUG
        )
        jpg_preview_path = api.get_jpg_preview_path(
            content_id=content.content_id,
            revision_id=content.revision_id,
            page_number=hapic_data.query.page,
            height=hapic_data.path.height,
            width=hapic_data.path.width,
        )
        filename = "{label}_page_{page_number}_{width}x{height}.jpg".format(
            label=content.label,
            page_number=hapic_data.query.page,
            width=hapic_data.path.width,
            height=hapic_data.path.height
        )
        return HapicFile(
            file_path=jpg_preview_path,
            filename=filename,
            as_attachment=hapic_data.query.force_download
        )

    @hapic.with_api_doc(tags=[SWAGGER_TAG__FILE_ENDPOINTS])
    @require_workspace_role(UserRoleInWorkspace.READER)
    @require_content_types([FILE_TYPE])
    @hapic.handle_exception(UnavailablePreview, HTTPStatus.BAD_REQUEST)
    @hapic.handle_exception(PageOfPreviewNotFound, HTTPStatus.BAD_REQUEST)
    @hapic.handle_exception(PreviewDimNotAllowed, HTTPStatus.BAD_REQUEST)
    @hapic.input_path(RevisionPreviewSizedPathSchema())
    @hapic.input_query(PageQuerySchema())
    @hapic.output_file([])
    def sized_preview_jpg_revision(self, context, request: TracimRequest, hapic_data=None):  # nopep8
        """
        Obtain resized jpg preview of a specific revision of content.
        """
        app_config = request.registry.settings['CFG']
        api = ContentApi(
            show_archived=True,
            show_deleted=True,
            current_user=request.current_user,
            session=request.dbsession,
            config=app_config,
        )
        content = api.get_one(
            hapic_data.path.content_id,
            content_type=CONTENT_TYPES.Any_SLUG
        )
        revision = api.get_one_revision(
            revision_id=hapic_data.path.revision_id,
            content=content
        )
        jpg_preview_path = api.get_jpg_preview_path(
            content_id=content.content_id,
            revision_id=revision.revision_id,
            page_number=hapic_data.query.page,
            height=hapic_data.path.height,
            width=hapic_data.path.width,
        )
        filename = "{label}_page_{page_number}_{width}x{height}.jpg".format(
            label=revision.label,
            page_number=hapic_data.query.page,
            width=hapic_data.path.width,
            height=hapic_data.path.height
        )
        return HapicFile(
            file_path=jpg_preview_path,
            filename=filename,
            as_attachment=hapic_data.query.force_download
        )

    @hapic.with_api_doc(tags=[SWAGGER_TAG__FILE_ENDPOINTS])
    @require_workspace_role(UserRoleInWorkspace.READER)
    @require_content_types([FILE_TYPE])
    @hapic.input_path(WorkspaceAndContentIdPathSchema())
    @hapic.output_body(AllowedJpgPreviewDimSchema())
    def allowed_dim_preview_jpg(self, context, request: TracimRequest, hapic_data=None):  # nopep8
        """
        Get allowed dimensions of jpg preview. If restricted is true,
        only those dimensions are strictly accepted.
        """
        app_config = request.registry.settings['CFG']
        api = ContentApi(
            show_archived=True,
            show_deleted=True,
            current_user=request.current_user,
            session=request.dbsession,
            config=app_config,
        )
        return api.get_jpg_preview_allowed_dim()

    # File infos
    @hapic.with_api_doc(tags=[SWAGGER_TAG__FILE_ENDPOINTS])
    @require_workspace_role(UserRoleInWorkspace.READER)
    @require_content_types([FILE_TYPE])
    @hapic.input_path(WorkspaceAndContentIdPathSchema())
    @hapic.output_body(FileContentSchema())
    def get_file_infos(self, context, request: TracimRequest, hapic_data=None) -> ContentInContext:  # nopep8
        """
        Get thread content
        """
        app_config = request.registry.settings['CFG']
        api = ContentApi(
            show_archived=True,
            show_deleted=True,
            current_user=request.current_user,
            session=request.dbsession,
            config=app_config,
        )
        content = api.get_one(
            hapic_data.path.content_id,
            content_type=CONTENT_TYPES.Any_SLUG
        )
        return api.get_content_in_context(content)

    @hapic.with_api_doc(tags=[SWAGGER_TAG__FILE_ENDPOINTS])
    @hapic.handle_exception(EmptyLabelNotAllowed, HTTPStatus.BAD_REQUEST)
    @hapic.handle_exception(ContentLabelAlreadyUsedHere, HTTPStatus.BAD_REQUEST)
    @require_workspace_role(UserRoleInWorkspace.CONTRIBUTOR)
    @require_content_types([FILE_TYPE])
    @hapic.input_path(WorkspaceAndContentIdPathSchema())
    @hapic.input_body(FileContentModifySchema())
    @hapic.output_body(FileContentSchema())
    def update_file_info(self, context, request: TracimRequest, hapic_data=None) -> ContentInContext:  # nopep8
        """
        update thread
        """
        app_config = request.registry.settings['CFG']
        api = ContentApi(
            show_archived=True,
            show_deleted=True,
            current_user=request.current_user,
            session=request.dbsession,
            config=app_config,
        )
        content = api.get_one(
            hapic_data.path.content_id,
            content_type=CONTENT_TYPES.Any_SLUG
        )
        with new_revision(
                session=request.dbsession,
                tm=transaction.manager,
                content=content
        ):
            api.update_content(
                item=content,
                new_label=hapic_data.body.label,
                new_content=hapic_data.body.raw_content,

            )
            api.save(content)
        return api.get_content_in_context(content)

    @hapic.with_api_doc(tags=[SWAGGER_TAG__FILE_ENDPOINTS])
    @require_workspace_role(UserRoleInWorkspace.READER)
    @require_content_types([FILE_TYPE])
    @hapic.input_path(WorkspaceAndContentIdPathSchema())
    @hapic.output_body(FileRevisionSchema(many=True))
    def get_file_revisions(
            self,
            context,
            request: TracimRequest,
            hapic_data=None
    ) -> typing.List[RevisionInContext]:
        """
        get file revisions
        """
        app_config = request.registry.settings['CFG']
        api = ContentApi(
            show_archived=True,
            show_deleted=True,
            current_user=request.current_user,
            session=request.dbsession,
            config=app_config,
        )
        content = api.get_one(
            hapic_data.path.content_id,
            content_type=CONTENT_TYPES.Any_SLUG
        )
        revisions = content.revisions
        return [
            api.get_revision_in_context(revision)
            for revision in revisions
        ]

    @hapic.with_api_doc(tags=[SWAGGER_TAG__FILE_ENDPOINTS])
    @hapic.handle_exception(EmptyLabelNotAllowed, HTTPStatus.BAD_REQUEST)
    @require_workspace_role(UserRoleInWorkspace.CONTRIBUTOR)
    @require_content_types([FILE_TYPE])
    @hapic.input_path(WorkspaceAndContentIdPathSchema())
    @hapic.input_body(SetContentStatusSchema())
    @hapic.output_body(NoContentSchema(), default_http_code=HTTPStatus.NO_CONTENT)  # nopep8
    def set_file_status(self, context, request: TracimRequest, hapic_data=None) -> None:  # nopep8
        """
        set file status
        """
        app_config = request.registry.settings['CFG']
        api = ContentApi(
            show_archived=True,
            show_deleted=True,
            current_user=request.current_user,
            session=request.dbsession,
            config=app_config,
        )
        content = api.get_one(
            hapic_data.path.content_id,
            content_type=CONTENT_TYPES.Any_SLUG
        )
        with new_revision(
                session=request.dbsession,
                tm=transaction.manager,
                content=content
        ):
            api.set_status(
                content,
                hapic_data.body.status,
            )
            api.save(content)
        return

    def bind(self, configurator: Configurator) -> None:
        """
        Add route to configurator.
        """

        # file info #
        # Get file info
        configurator.add_route(
            'file_info',
            '/workspaces/{workspace_id}/files/{content_id}',
            request_method='GET'
        )
        configurator.add_view(self.get_file_infos, route_name='file_info')  # nopep8
        # update file
        configurator.add_route(
            'update_file_info',
            '/workspaces/{workspace_id}/files/{content_id}',
            request_method='PUT'
        )  # nopep8
        configurator.add_view(self.update_file_info, route_name='update_file_info')  # nopep8

        # raw file #
        # create file
        configurator.add_route(
            'create_file',
            '/workspaces/{workspace_id}/files',  # nopep8
            request_method='POST'
        )
        configurator.add_view(self.create_file, route_name='create_file')  # nopep8
        # upload raw file
        configurator.add_route(
            'upload_file',
            '/workspaces/{workspace_id}/files/{content_id}/raw',  # nopep8
            request_method='PUT'
        )
        configurator.add_view(self.upload_file, route_name='upload_file')  # nopep8
        # download raw file
        configurator.add_route(
            'download_file',
            '/workspaces/{workspace_id}/files/{content_id}/raw',  # nopep8
            request_method='GET'
        )
        configurator.add_view(self.download_file, route_name='download_file')  # nopep8
        # download raw file of revision
        configurator.add_route(
            'download_revision',
            '/workspaces/{workspace_id}/files/{content_id}/revisions/{revision_id}/raw',  # nopep8
            request_method='GET'
        )
        configurator.add_view(self.download_revisions_file, route_name='download_revision')  # nopep8

        # previews #
        # get preview pdf full
        configurator.add_route(
            'preview_pdf_full',
            '/workspaces/{workspace_id}/files/{content_id}/preview/pdf/full',  # nopep8
            request_method='GET'
        )
        configurator.add_view(self.preview_pdf_full, route_name='preview_pdf_full')  # nopep8
        # get preview pdf
        configurator.add_route(
            'preview_pdf',
            '/workspaces/{workspace_id}/files/{content_id}/preview/pdf',  # nopep8
            request_method='GET'
        )
        configurator.add_view(self.preview_pdf, route_name='preview_pdf')  # nopep8
        # get preview jpg allowed dims
        configurator.add_route(
            'allowed_dim_preview_jpg',
            '/workspaces/{workspace_id}/files/{content_id}/preview/jpg/allowed_dims',  # nopep8
            request_method='GET'
        )
        configurator.add_view(self.allowed_dim_preview_jpg, route_name='allowed_dim_preview_jpg')  # nopep8
        # get preview jpg
        configurator.add_route(
            'preview_jpg',
            '/workspaces/{workspace_id}/files/{content_id}/preview/jpg',  # nopep8
            request_method='GET'
        )
        configurator.add_view(self.preview_jpg, route_name='preview_jpg')  # nopep8
        # get preview jpg with size
        configurator.add_route(
            'sized_preview_jpg',
            '/workspaces/{workspace_id}/files/{content_id}/preview/jpg/{width}x{height}',  # nopep8
            request_method='GET'
        )
        configurator.add_view(self.sized_preview_jpg, route_name='sized_preview_jpg')  # nopep8
        # get jpg preview for revision
        configurator.add_route(
            'sized_preview_jpg_revision',
            '/workspaces/{workspace_id}/files/{content_id}/revisions/{revision_id}/preview/jpg/{width}x{height}',  # nopep8
            request_method='GET'
        )
        configurator.add_view(self.sized_preview_jpg_revision, route_name='sized_preview_jpg_revision')  # nopep8
        # get full pdf preview for revision
        configurator.add_route(
            'preview_pdf_full_revision',
            '/workspaces/{workspace_id}/files/{content_id}/revisions/{revision_id}/preview/pdf/full',  # nopep8
            request_method='GET'
        )
        configurator.add_view(self.preview_pdf_full_revision, route_name='preview_pdf_full_revision')  # nopep8
        # get pdf preview for revision
        configurator.add_route(
            'preview_pdf_revision',
            '/workspaces/{workspace_id}/files/{content_id}/revisions/{revision_id}/preview/pdf',  # nopep8
            request_method='GET'
        )
        configurator.add_view(self.preview_pdf_revision, route_name='preview_pdf_revision')  # nopep8
        # others #
        # get file revisions
        configurator.add_route(
            'file_revisions',
            '/workspaces/{workspace_id}/files/{content_id}/revisions',  # nopep8
            request_method='GET'
        )
        configurator.add_view(self.get_file_revisions, route_name='file_revisions')  # nopep8

        # get file status
        configurator.add_route(
            'set_file_status',
            '/workspaces/{workspace_id}/files/{content_id}/status',  # nopep8
            request_method='PUT'
        )
        configurator.add_view(self.set_file_status, route_name='set_file_status')  # nopep8
