import {
  SET,
  UPDATE,
  USER_WORKSPACE_DO_NOTIFY,
  WORKSPACE_LIST,
  WORKSPACE_LIST_MEMBER
} from '../action-creator.sync.js'
import { handleRouteFromApi } from '../helper.js'

export function workspaceList (state = [], action) {
  switch (action.type) {
    case `${SET}/${WORKSPACE_LIST}`:
      return action.workspaceList.map(ws => ({
        id: ws.workspace_id,
        label: ws.label,
        slug: ws.slug,
        // description: ws.description, // not returned by /api/v2/users/:idUser/workspaces
        sidebarEntry: ws.sidebar_entries.map(sbe => ({
          slug: sbe.slug,
          route: handleRouteFromApi(sbe.route),
          faIcon: sbe.fa_icon,
          hexcolor: sbe.hexcolor,
          label: sbe.label
        })),
        isOpenInSidebar: false,
        memberList: []
      }))

    case `${SET}/${WORKSPACE_LIST}/isOpenInSidebar`:
      return state.map(ws => ws.id === action.workspaceId
        ? {...ws, isOpenInSidebar: action.isOpenInSidebar}
        : ws
      )

    case `${SET}/${WORKSPACE_LIST_MEMBER}`:
      return state.map(ws => ({
        ...ws,
        memberList: action.workspaceListMemberList.find(wlml => wlml.idWorkspace === ws.id).memberList
      }))

    case `${UPDATE}/${USER_WORKSPACE_DO_NOTIFY}`:
      return state.map(ws => ws.id === action.idWorkspace
        ? {
          ...ws,
          memberList: ws.memberList.map(u => u.user_id === action.idUser
            ? {...u, do_notify: action.doNotify}
            : u
          )
        }
        : ws
      )

    default:
      return state
  }
}

export default workspaceList
