# coding=utf-8
import marshmallow
from marshmallow import post_load
from marshmallow.validate import Length
from marshmallow.validate import OneOf
from marshmallow.validate import Range

from tracim_backend.app_models.contents import CONTENT_STATUS
from tracim_backend.app_models.contents import CONTENT_TYPES
from tracim_backend.app_models.contents import GlobalStatus
from tracim_backend.app_models.contents import open_status
from tracim_backend.app_models.validator import all_content_types_validator
from tracim_backend.lib.utils.utils import DATETIME_FORMAT
from tracim_backend.models.auth import Group
from tracim_backend.models.auth import Profile
from tracim_backend.models.context_models import ActiveContentFilter
from tracim_backend.models.context_models import ResetPasswordRequest
from tracim_backend.models.context_models import ResetPasswordCheckToken
from tracim_backend.models.context_models import ResetPasswordModify
from tracim_backend.models.context_models import FolderContentUpdate
from tracim_backend.models.context_models import AutocompleteQuery
from tracim_backend.models.context_models import CommentCreation
from tracim_backend.models.context_models import CommentPath
from tracim_backend.models.context_models import ContentCreation
from tracim_backend.models.context_models import ContentFilter
from tracim_backend.models.context_models import ContentIdsQuery
from tracim_backend.models.context_models import ContentPreviewSizedPath
from tracim_backend.models.context_models import FileQuery
from tracim_backend.models.context_models import FolderContentUpdate
from tracim_backend.models.context_models import LoginCredentials
from tracim_backend.models.context_models import MoveParams
from tracim_backend.models.context_models import PageQuery
from tracim_backend.models.context_models import RevisionPreviewSizedPath
from tracim_backend.models.context_models import RoleUpdate
from tracim_backend.models.context_models import SetContentStatus
from tracim_backend.models.context_models import SetEmail
from tracim_backend.models.context_models import SetPassword
from tracim_backend.models.context_models import TextBasedContentUpdate
from tracim_backend.models.context_models import UserCreation
from tracim_backend.models.context_models import UserInfos
from tracim_backend.models.context_models import UserProfile
from tracim_backend.models.context_models import UserWorkspaceAndContentPath
from tracim_backend.models.context_models import WorkspaceAndContentPath
from tracim_backend.models.context_models import \
    WorkspaceAndContentRevisionPath
from tracim_backend.models.context_models import WorkspaceAndUserPath
from tracim_backend.models.context_models import WorkspaceMemberInvitation
from tracim_backend.models.context_models import WorkspaceUpdate
from tracim_backend.models.data import ActionDescription
from tracim_backend.models.data import UserRoleInWorkspace


class UserDigestSchema(marshmallow.Schema):
    """
    Simple user schema
    """
    user_id = marshmallow.fields.Int(dump_only=True, example=3)
    avatar_url = marshmallow.fields.Url(
        allow_none=True,
        example="/api/v2/asset/avatars/suri-cate.jpg",
        description="avatar_url is the url to the image file. "
                    "If no avatar, then set it to null "
                    "(and frontend will interpret this with a default avatar)",
    )
    public_name = marshmallow.fields.String(
        example='Suri Cate',
    )


class UserSchema(UserDigestSchema):
    """
    Complete user schema
    """
    email = marshmallow.fields.Email(
        required=True,
        example='suri.cate@algoo.fr'
    )
    created = marshmallow.fields.DateTime(
        format=DATETIME_FORMAT,
        description='User account creation date',
    )
    is_active = marshmallow.fields.Bool(
        example=True,
        description='Is user account activated ?'
    )
    is_deleted = marshmallow.fields.Bool(
        example=False,
        description='Is user account deleted ?'
    )
    # TODO - G.M - 17-04-2018 - Restrict timezone values
    timezone = marshmallow.fields.String(
        description="Timezone as tz database format",
        example="Europe/Paris",
    )
    # TODO - G.M - 17-04-2018 - check this, relative url allowed ?
    caldav_url = marshmallow.fields.Url(
        allow_none=True,
        relative=True,
        attribute='calendar_url',
        example="/api/v2/calendar/user/3.ics/",
        description="The url for calendar CalDAV direct access",
    )
    profile = marshmallow.fields.String(
        attribute='profile',
        validate=OneOf(Profile._NAME),
        example='trusted-users',
    )
    lang = marshmallow.fields.String(
        description="User langage in iso639 format",
        example='en',
        required=False,
        validate=Length(min=2, max=3),
        allow_none=True,
        default=None,
    )

    class Meta:
        description = 'User account of Tracim'


class LoggedInUserPasswordSchema(marshmallow.Schema):
    loggedin_user_password = marshmallow.fields.String(
        required=True,
    )


class SetEmailSchema(LoggedInUserPasswordSchema):
    email = marshmallow.fields.Email(
        required=True,
        example='suri.cate@algoo.fr'
    )

    @post_load
    def create_set_email_object(self, data):
        return SetEmail(**data)


class SetPasswordSchema(LoggedInUserPasswordSchema):
    new_password = marshmallow.fields.String(
        example='8QLa$<w',
        required=True
    )
    new_password2 = marshmallow.fields.String(
        example='8QLa$<w',
        required=True
    )

    @post_load
    def create_set_password_object(self, data):
        return SetPassword(**data)


class UserInfosSchema(marshmallow.Schema):
    timezone = marshmallow.fields.String(
        description="Timezone as tz database format",
        example="Europe/Paris",
        required=True,
    )
    public_name = marshmallow.fields.String(
        example='Suri Cate',
        required=True,
    )
    lang = marshmallow.fields.String(
        description="User langage in iso639 format",
        example='en',
        required=True,
        validate=Length(min=2, max=3),
        allow_none=True,
        default=None,
    )

    @post_load
    def create_user_info_object(self, data):
        return UserInfos(**data)


class UserProfileSchema(marshmallow.Schema):
    profile = marshmallow.fields.String(
        attribute='profile',
        validate=OneOf(Profile._NAME),
        example='trusted-users',
    )
    @post_load
    def create_user_profile(self, data):
        return UserProfile(**data)


class UserCreationSchema(marshmallow.Schema):
    email = marshmallow.fields.Email(
        required=True,
        example='suri.cate@algoo.fr'
    )
    password = marshmallow.fields.String(
        example='8QLa$<w',
        required=False,
    )
    profile = marshmallow.fields.String(
        attribute='profile',
        validate=OneOf(Profile._NAME),
        example='trusted-users',
        required=False,
        default=Group.TIM_USER_GROUPNAME
    )
    timezone = marshmallow.fields.String(
        description="Timezone as tz database format",
        example="Europe/Paris",
        required=False,
        default=''
    )
    public_name = marshmallow.fields.String(
        example='Suri Cate',
        required=False,
        default=None,
    )
    lang = marshmallow.fields.String(
        description="User langage in iso639 format",
        example='en',
        required=False,
        validate=Length(min=2, max=3),
        allow_none=True,
        default=None,
    )
    email_notification = marshmallow.fields.Bool(
        example=True,
        required=False,
        default=True,
    )

    @post_load
    def create_user(self, data):
        return UserCreation(**data)


# Path Schemas

class UserIdPathSchema(marshmallow.Schema):
    user_id = marshmallow.fields.Int(
        example=3,
        required=True,
        description='id of a valid user',
        validate=Range(min=1, error="Value must be greater than 0"),
    )


class WorkspaceIdPathSchema(marshmallow.Schema):
    workspace_id = marshmallow.fields.Int(
        example=4,
        required=True,
        description='id of a valid workspace',
        validate=Range(min=1, error="Value must be greater than 0"),
    )


class ContentIdPathSchema(marshmallow.Schema):
    content_id = marshmallow.fields.Int(
        example=6,
        required=True,
        description='id of a valid content',
        validate=Range(min=1, error="Value must be greater than 0"),
    )


class RevisionIdPathSchema(marshmallow.Schema):
    revision_id = marshmallow.fields.Int(example=6, required=True)


class WorkspaceAndUserIdPathSchema(
    UserIdPathSchema,
    WorkspaceIdPathSchema
):
    @post_load
    def make_path_object(self, data):
        return WorkspaceAndUserPath(**data)


class WorkspaceAndContentIdPathSchema(
    WorkspaceIdPathSchema,
    ContentIdPathSchema
):
    @post_load
    def make_path_object(self, data):
        return WorkspaceAndContentPath(**data)


class WidthAndHeightPathSchema(marshmallow.Schema):
    width = marshmallow.fields.Int(example=256)
    height = marshmallow.fields.Int(example=256)


class AllowedJpgPreviewSizesSchema(marshmallow.Schema):
    width = marshmallow.fields.Int(example=256)
    height = marshmallow.fields.Int(example=256)


class AllowedJpgPreviewDimSchema(marshmallow.Schema):
    restricted = marshmallow.fields.Bool()
    dimensions = marshmallow.fields.Nested(
        AllowedJpgPreviewSizesSchema,
        many=True
    )


class WorkspaceAndContentRevisionIdPathSchema(
    WorkspaceIdPathSchema,
    ContentIdPathSchema,
    RevisionIdPathSchema,
):
    @post_load
    def make_path_object(self, data):
        return WorkspaceAndContentRevisionPath(**data)


class ContentPreviewSizedPathSchema(
    WorkspaceAndContentIdPathSchema,
    WidthAndHeightPathSchema
):
    @post_load
    def make_path_object(self, data):
        return ContentPreviewSizedPath(**data)


class RevisionPreviewSizedPathSchema(
    WorkspaceAndContentRevisionIdPathSchema,
    WidthAndHeightPathSchema
):
    @post_load
    def make_path_object(self, data):
        return RevisionPreviewSizedPath(**data)


class UserWorkspaceAndContentIdPathSchema(
    UserIdPathSchema,
    WorkspaceIdPathSchema,
    ContentIdPathSchema,
):
    @post_load
    def make_path_object(self, data):
        return UserWorkspaceAndContentPath(**data)


class UserWorkspaceIdPathSchema(
    UserIdPathSchema,
    WorkspaceIdPathSchema,
):
    @post_load
    def make_path_object(self, data):
        return WorkspaceAndUserPath(**data)


class CommentsPathSchema(WorkspaceAndContentIdPathSchema):
    comment_id = marshmallow.fields.Int(
        example=6,
        description='id of a valid comment related to content content_id',
        required=True,
        validate=Range(min=1, error="Value must be greater than 0"),
    )

    @post_load
    def make_path_object(self, data):
        return CommentPath(**data)


class AutocompleteQuerySchema(marshmallow.Schema):
    acp = marshmallow.fields.Str(
        example='test',
        description='search text to query',
        validate=Length(min=2),
        required=True,
    )
    @post_load
    def make_autocomplete(self, data):
        return AutocompleteQuery(**data)


class FileQuerySchema(marshmallow.Schema):
    force_download = marshmallow.fields.Int(
        example=1,
        default=0,
        description='force download of file or let browser decide if'
                    'file can be read directly from browser',
        validate=Range(min=0, max=1, error="Value must be 0 or 1"),
    )

    @post_load
    def make_query(self, data):
        return FileQuery(**data)


class PageQuerySchema(FileQuerySchema):
    page = marshmallow.fields.Int(
        example=2,
        default=1,
        description='allow to show a specific page of a pdf file',
        validate=Range(min=1, error="Value must be positive"),
    )

    @post_load
    def make_query(self, data):
        return PageQuery(**data)


class FilterContentQuerySchema(marshmallow.Schema):
    parent_id = marshmallow.fields.Int(
        example=2,
        default=0,
        description='allow to filter items in a folder.'
                    ' If not set, then return all contents.'
                    ' If set to 0, then return root contents.'
                    ' If set to another value, return all contents'
                    ' directly included in the folder parent_id',
        validate=Range(min=0, error="Value must be positive or 0"),
    )
    show_archived = marshmallow.fields.Int(
        example=0,
        default=0,
        description='if set to 1, then show archived contents.'
                    ' Default is 0 - hide archived content',
        validate=Range(min=0, max=1, error="Value must be 0 or 1"),
    )
    show_deleted = marshmallow.fields.Int(
        example=0,
        default=0,
        description='if set to 1, then show deleted contents.'
                    ' Default is 0 - hide deleted content',
        validate=Range(min=0, max=1, error="Value must be 0 or 1"),
    )
    show_active = marshmallow.fields.Int(
        example=1,
        default=1,
        description='f set to 1, then show active contents. '
                    'Default is 1 - show active content.'
                    ' Note: active content are content '
                    'that is neither archived nor deleted. '
                    'The reason for this parameter to exist is for example '
                    'to allow to show only archived documents',
        validate=Range(min=0, max=1, error="Value must be 0 or 1"),
    )
    content_type = marshmallow.fields.String(
        example=CONTENT_TYPES.Any_SLUG,
        default=CONTENT_TYPES.Any_SLUG,
        validate=all_content_types_validator
    )
    label = marshmallow.fields.String(
        example='myfilename',
        default=None,
        allow_none=True,
        description='Filter by content label'
    )

    @post_load
    def make_content_filter(self, data):
        return ContentFilter(**data)


class ActiveContentFilterQuerySchema(marshmallow.Schema):
    limit = marshmallow.fields.Int(
        example=2,
        default=0,
        description='if 0 or not set, return all elements, else return only '
                    'the first limit elem (according to offset)',
        validate=Range(min=0, error="Value must be positive or 0"),
    )
    before_content_id = marshmallow.fields.Int(
        example=41,
        default=None,
        allow_none=True,
        description='return only content updated before this content',
    )
    @post_load
    def make_content_filter(self, data):
        return ActiveContentFilter(**data)


class ContentIdsQuerySchema(marshmallow.Schema):
    contents_ids = marshmallow.fields.List(
        marshmallow.fields.Int(
            example=6,
            validate=Range(min=1, error="Value must be greater than 0"),
        )
    )
    @post_load
    def make_contents_ids(self, data):
        return ContentIdsQuery(**data)


###


class RoleUpdateSchema(marshmallow.Schema):
    role = marshmallow.fields.String(
        required=True,
        example='contributor',
        validate=OneOf(UserRoleInWorkspace.get_all_role_slug())
    )

    @post_load
    def make_role(self, data):
        return RoleUpdate(**data)


class WorkspaceMemberInviteSchema(marshmallow.Schema):
    role = marshmallow.fields.String(
        example='contributor',
        validate=OneOf(UserRoleInWorkspace.get_all_role_slug())
    )
    user_id = marshmallow.fields.Int(
        example=5,
        default=None,
        allow_none=True,
    )
    user_email_or_public_name = marshmallow.fields.String(
        example='suri@cate.fr',
        default=None,
        allow_none=True,
    )

    @post_load
    def make_role(self, data):
        return WorkspaceMemberInvitation(**data)


class ResetPasswordRequestSchema(marshmallow.Schema):
    email = marshmallow.fields.Email(
        required=True,
        example='suri.cate@algoo.fr'
    )

    @post_load
    def make_object(self, data):
        return ResetPasswordRequest(**data)


class ResetPasswordCheckTokenSchema(marshmallow.Schema):
    email = marshmallow.fields.Email(
        required=True,
        example='suri.cate@algoo.fr'
    )
    reset_password_token = marshmallow.fields.String(
        description="token to reset password of given user",
        required=True,
    )

    @post_load
    def make_object(self, data):
        return ResetPasswordCheckToken(**data)


class ResetPasswordModifySchema(marshmallow.Schema):
    email = marshmallow.fields.Email(
        required=True,
        example='suri.cate@algoo.fr'
    )
    reset_password_token = marshmallow.fields.String(
        description="token to reset password of given user",
        required=True,
    )
    new_password = marshmallow.fields.String(
        example='8QLa$<w',
        required=True
    )
    new_password2 = marshmallow.fields.String(
        example='8QLa$<w',
        required=True
    )

    @post_load
    def make_object(self, data):
        return ResetPasswordModify(**data)


class BasicAuthSchema(marshmallow.Schema):

    email = marshmallow.fields.Email(
        example='suri.cate@algoo.fr',
        required=True
    )
    password = marshmallow.fields.String(
        example='8QLa$<w',
        required=True,
        load_only=True,
    )

    class Meta:
        description = 'Entry for HTTP Basic Auth'

    @post_load
    def make_login(self, data):
        return LoginCredentials(**data)


class LoginOutputHeaders(marshmallow.Schema):
    expire_after = marshmallow.fields.String()


class WorkspaceModifySchema(marshmallow.Schema):
    label = marshmallow.fields.String(
        required=True,
        example='My Workspace',
    )
    description = marshmallow.fields.String(
        required=True,
        example='A super description of my workspace.',
    )

    @post_load
    def make_workspace_modifications(self, data):
        return WorkspaceUpdate(**data)


class WorkspaceCreationSchema(WorkspaceModifySchema):
    pass


class NoContentSchema(marshmallow.Schema):

    class Meta:
        description = 'Empty Schema'
    pass


class WorkspaceMenuEntrySchema(marshmallow.Schema):
    slug = marshmallow.fields.String(example='markdown-pages')
    label = marshmallow.fields.String(example='Markdown Documents')
    route = marshmallow.fields.String(
        example='/#/workspace/{workspace_id}/contents/?type=mardown-page',
        description='the route is the frontend route. '
                    'It may include workspace_id '
                    'which must be replaced on backend size '
                    '(the route must be ready-to-use)'
    )
    fa_icon = marshmallow.fields.String(
        example='file-text-o',
        description='CSS class of the icon. Example: file-o for using Fontawesome file-text-o icon',  # nopep8
    )
    hexcolor = marshmallow.fields.String(
        example='#F0F9DC',
        description='Hexadecimal color of the entry.'
    )

    class Meta:
        description = 'Entry element of a workspace menu'


class WorkspaceDigestSchema(marshmallow.Schema):
    workspace_id = marshmallow.fields.Int(
        example=4,
        validate=Range(min=1, error="Value must be greater than 0"),
    )
    slug = marshmallow.fields.String(example='intranet')
    label = marshmallow.fields.String(example='Intranet')
    sidebar_entries = marshmallow.fields.Nested(
        WorkspaceMenuEntrySchema,
        many=True,
    )
    is_deleted = marshmallow.fields.Bool(example=False, default=False)

    class Meta:
        description = 'Digest of workspace informations'


class WorkspaceSchema(WorkspaceDigestSchema):
    description = marshmallow.fields.String(example='All intranet data.')

    class Meta:
        description = 'Full workspace informations'


class WorkspaceMemberSchema(marshmallow.Schema):
    role = marshmallow.fields.String(
        example='contributor',
        validate=OneOf(UserRoleInWorkspace.get_all_role_slug())
    )
    user_id = marshmallow.fields.Int(
        example=3,
        validate=Range(min=1, error="Value must be greater than 0"),
    )
    workspace_id = marshmallow.fields.Int(
        example=4,
        validate=Range(min=1, error="Value must be greater than 0"),
    )
    user = marshmallow.fields.Nested(
        UserDigestSchema()
    )
    workspace = marshmallow.fields.Nested(
        WorkspaceDigestSchema(exclude=('sidebar_entries',))
    )
    is_active = marshmallow.fields.Bool()
    do_notify = marshmallow.fields.Bool(
        description='has user enabled notification for this workspace',
        example=True,
    )

    class Meta:
        description = 'Workspace Member information'


class WorkspaceMemberCreationSchema(WorkspaceMemberSchema):
    newly_created = marshmallow.fields.Bool(
        exemple=False,
        description='Is the user completely new '
                    '(and account was just created) or not ?',
    )
    email_sent = marshmallow.fields.Bool(
        exemple=False,
        description='Has an email been sent to user to inform him about '
                    'this new workspace registration and eventually his account'
                    'creation'
    )


class ApplicationConfigSchema(marshmallow.Schema):
    pass
    #  TODO - G.M - 24-05-2018 - Set this


class TimezoneSchema(marshmallow.Schema):
    name = marshmallow.fields.String(example='Europe/London')


class AboutSchema(marshmallow.Schema):
    name = marshmallow.fields.String(example='Tracim', description='Software name')  # nopep8
    version = marshmallow.fields.String(example='2.0', allow_none=True, description='Version of Tracim')  # nopep8
    datetime = marshmallow.fields.DateTime(format=DATETIME_FORMAT)
    website = marshmallow.fields.URL(allow_none=True)


class ConfigSchema(marshmallow.Schema):
    email_notification_activated = marshmallow.fields.Bool()


class ApplicationSchema(marshmallow.Schema):
    label = marshmallow.fields.String(example='Calendar')
    slug = marshmallow.fields.String(example='calendar')
    fa_icon = marshmallow.fields.String(
        example='file-o',
        description='CSS class of the icon. Example: file-o for using Fontawesome file-o icon',  # nopep8
    )
    hexcolor = marshmallow.fields.String(
        example='#FF0000',
        description='HTML encoded color associated to the application. Example:#FF0000 for red'  # nopep8
    )
    is_active = marshmallow.fields.Boolean(
        example=True,
        description='if true, the application is in use in the context',
    )
    config = marshmallow.fields.Nested(
        ApplicationConfigSchema,
    )

    class Meta:
        description = 'Tracim Application informations'


class StatusSchema(marshmallow.Schema):
    slug = marshmallow.fields.String(
        example='open',
        description='the slug represents the type of status. '
                    'Statuses are open, closed-validated, closed-invalidated, closed-deprecated'  # nopep8
    )
    global_status = marshmallow.fields.String(
        example='open',
        description='global_status: open, closed',
        validate=OneOf([status.value for status in GlobalStatus]),
    )
    label = marshmallow.fields.String(example='Open')
    fa_icon = marshmallow.fields.String(example='fa-check')
    hexcolor = marshmallow.fields.String(example='#0000FF')


class ContentTypeSchema(marshmallow.Schema):
    slug = marshmallow.fields.String(
        example='pagehtml',
        validate=all_content_types_validator,
    )
    fa_icon = marshmallow.fields.String(
        example='fa-file-text-o',
        description='CSS class of the icon. Example: file-o for using Fontawesome file-o icon',  # nopep8
    )
    hexcolor = marshmallow.fields.String(
        example="#FF0000",
        description='HTML encoded color associated to the application. Example:#FF0000 for red'  # nopep8
    )
    label = marshmallow.fields.String(
        example='Text Documents'
    )
    creation_label = marshmallow.fields.String(
        example='Write a document'
    )
    available_statuses = marshmallow.fields.Nested(
        StatusSchema,
        many=True
    )


class ContentMoveSchema(marshmallow.Schema):
    # TODO - G.M - 30-05-2018 - Read and apply this note
    # Note:
    # if the new workspace is different, then the backend
    # must check if the user is allowed to move to this workspace
    # (the user must be content manager of both workspaces)
    new_parent_id = marshmallow.fields.Int(
        example=42,
        description='id of the new parent content id.',
        allow_none=True,
        required=True,
        validate=Range(min=0, error="Value must be positive or 0"),
    )
    new_workspace_id = marshmallow.fields.Int(
        example=2,
        description='id of the new workspace id.',
        required=True,
        validate=Range(min=1, error="Value must be greater than 0"),
    )

    @post_load
    def make_move_params(self, data):
        return MoveParams(**data)


class ContentCreationSchema(marshmallow.Schema):
    label = marshmallow.fields.String(
        required=True,
        example='contract for client XXX',
        description='Title of the content to create',
        validate=Length(min=1),
    )
    content_type = marshmallow.fields.String(
        required=True,
        example='html-document',
        validate=all_content_types_validator,
    )
    parent_id = marshmallow.fields.Integer(
        example=35,
        description='content_id of parent content, if content should be placed in a folder, this should be folder content_id.', # nopep8
        allow_none=True,
        default=None,
        validate=Range(min=1, error="Value must be positive"),
    )


    @post_load
    def make_content_creation(self, data):
        return ContentCreation(**data)


class ContentDigestSchema(marshmallow.Schema):
    content_id = marshmallow.fields.Int(
        example=6,
        validate=Range(min=1, error="Value must be greater than 0"),
    )
    slug = marshmallow.fields.Str(example='intervention-report-12')
    parent_id = marshmallow.fields.Int(
        example=34,
        allow_none=True,
        default=None,
        validate=Range(min=0, error="Value must be positive or 0"),
    )
    workspace_id = marshmallow.fields.Int(
        example=19,
        validate=Range(min=1, error="Value must be greater than 0"),
    )
    label = marshmallow.fields.Str(example='Intervention Report 12')
    content_type = marshmallow.fields.Str(
        example='html-document',
        validate=all_content_types_validator,
    )
    sub_content_types = marshmallow.fields.List(
        marshmallow.fields.String(
            example='html-content',
            validate=all_content_types_validator
        ),
        description='list of content types allowed as sub contents. '
                    'This field is required for folder contents, '
                    'set it to empty list in other cases'
    )
    status = marshmallow.fields.Str(
        example='closed-deprecated',
        validate=OneOf(CONTENT_STATUS.get_all_slugs_values()),
        description='this slug is found in content_type available statuses',
        default=open_status
    )
    is_archived = marshmallow.fields.Bool(example=False, default=False)
    is_deleted = marshmallow.fields.Bool(example=False, default=False)
    show_in_ui = marshmallow.fields.Bool(
        example=True,
        description='if false, then do not show content in the treeview. '
                    'This may his maybe used for specific contents or '
                    'for sub-contents. Default is True. '
                    'In first version of the API, this field is always True',
    )


class ReadStatusSchema(marshmallow.Schema):
    content_id = marshmallow.fields.Int(
        example=6,
        validate=Range(min=1, error="Value must be greater than 0"),
    )
    read_by_user = marshmallow.fields.Bool(example=False, default=False)
#####
# Content
#####


class ContentSchema(ContentDigestSchema):
    current_revision_id = marshmallow.fields.Int(example=12)
    created = marshmallow.fields.DateTime(
        format=DATETIME_FORMAT,
        description='Content creation date',
    )
    author = marshmallow.fields.Nested(UserDigestSchema)
    modified = marshmallow.fields.DateTime(
        format=DATETIME_FORMAT,
        description='date of last modification of content',
    )
    last_modifier = marshmallow.fields.Nested(UserDigestSchema)


class TextBasedDataAbstractSchema(marshmallow.Schema):
    raw_content = marshmallow.fields.String(
        description='Content of the object, may be raw text or <b>html</b> for example'  # nopep8
    )


class FileInfoAbstractSchema(marshmallow.Schema):
    raw_content = marshmallow.fields.String(
        description='raw text or html description of the file'
    )
    page_nb = marshmallow.fields.Int(
        description='number of pages, return null value if unaivalable',
        example=1,
        allow_none=True,
    )
    mimetype = marshmallow.fields.String(
        description='file content mimetype',
        example='image/jpeg',
        required=True,
    )
    size = marshmallow.fields.Int(
        description='file size in byte, return null value if unaivalable',
        example=1024,
        allow_none=True,
    )
    pdf_available = marshmallow.fields.Bool(
        description="Is pdf version of file available ?",
        example=True,
    )
    file_extension = marshmallow.fields.String(
        example='.txt'
    )


class TextBasedContentSchema(ContentSchema, TextBasedDataAbstractSchema):
    pass


class FileContentSchema(ContentSchema, FileInfoAbstractSchema):
    pass

#####
# Revision
#####


class RevisionSchema(ContentDigestSchema):
    comment_ids = marshmallow.fields.List(
        marshmallow.fields.Int(
            example=4,
            validate=Range(min=1, error="Value must be greater than 0"),
        )
    )
    revision_id = marshmallow.fields.Int(
        example=12,
        validate=Range(min=1, error="Value must be greater than 0"),
    )
    revision_type = marshmallow.fields.String(
        example=ActionDescription.CREATION,
        validate=OneOf(ActionDescription.allowed_values()),
    )
    created = marshmallow.fields.DateTime(
        format=DATETIME_FORMAT,
        description='Content creation date',
    )
    author = marshmallow.fields.Nested(UserDigestSchema)


class TextBasedRevisionSchema(RevisionSchema, TextBasedDataAbstractSchema):
    pass


class FileRevisionSchema(RevisionSchema, FileInfoAbstractSchema):
    pass


class CommentSchema(marshmallow.Schema):
    content_id = marshmallow.fields.Int(
        example=6,
        validate=Range(min=1, error="Value must be greater than 0"),
    )
    parent_id = marshmallow.fields.Int(
        example=34,
        validate=Range(min=0, error="Value must be positive or 0"),
    )
    raw_content = marshmallow.fields.String(
        example='<p>This is just an html comment !</p>'
    )
    author = marshmallow.fields.Nested(UserDigestSchema)
    created = marshmallow.fields.DateTime(
        format=DATETIME_FORMAT,
        description='comment creation date',
    )


class SetCommentSchema(marshmallow.Schema):
    raw_content = marshmallow.fields.String(
        example='<p>This is just an html comment !</p>',
        validate=Length(min=1),
        required=True,
    )

    @post_load()
    def create_comment(self, data):
        return CommentCreation(**data)


class ContentModifyAbstractSchema(marshmallow.Schema):
    label = marshmallow.fields.String(
        required=True,
        example='contract for client XXX',
        description='New title of the content',
        validate=Length(min=1)
    )


class TextBasedContentModifySchema(ContentModifyAbstractSchema, TextBasedDataAbstractSchema):  # nopep8

    @post_load
    def text_based_content_update(self, data):
        return TextBasedContentUpdate(**data)


class FolderContentModifySchema(ContentModifyAbstractSchema, TextBasedDataAbstractSchema):  # nopep
    sub_content_types = marshmallow.fields.List(
        marshmallow.fields.String(
            example='html-document',
            validate=all_content_types_validator,
        ),
        description='list of content types allowed as sub contents. '
                    'This field is required for folder contents, '
                    'set it to empty list in other cases'
    )

    @post_load
    def folder_content_update(self, data):
        return FolderContentUpdate(**data)


class FileContentModifySchema(TextBasedContentModifySchema):
    pass


class SetContentStatusSchema(marshmallow.Schema):
    status = marshmallow.fields.Str(
        example='closed-deprecated',
        validate=OneOf(CONTENT_STATUS.get_all_slugs_values()),
        description='this slug is found in content_type available statuses',
        default=open_status,
        required=True,
    )

    @post_load
    def set_status(self, data):
        return SetContentStatus(**data)
