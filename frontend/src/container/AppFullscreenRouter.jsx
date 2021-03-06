import React from 'react'
import { connect } from 'react-redux'
import { withRouter } from 'react-router'
import { Route, Redirect } from 'react-router-dom'
import { PAGE, PROFILE } from '../helper.js'
import appFactory from '../appFactory.js'

class AppFullscreenRouter extends React.Component {
  constructor (props) {
    super(props)
    this.state = {
      isMounted: false
    }
  }

  componentDidMount = () => this.setState({isMounted: true})

  componentWillUnmount = () => this.props.dispatchCustomEvent('unmount_app')

  render () {
    const { props } = this

    return (
      <div className='AppFullScreenManager'>

        {this.state.isMounted && (// we must wait for the component to be fully mounted to be sure the div#appFullscreenContainer exists in DOM
          <div className='emptyDivForRoute'>
            <Route exact path={PAGE.ADMIN.WORKSPACE} render={() => {
              if (props.user.profile !== PROFILE.ADMINISTRATOR.slug) return <Redirect to={{pathname: '/'}} />

              const content = {
                workspaceList: [],
                userList: []
              }

              props.renderAppFullscreen({slug: 'admin_workspace_user', hexcolor: '#7d4e24', type: 'workspace'}, props.user, content)
              return null
            }} />

            <Route exact path={PAGE.ADMIN.USER} render={() => {
              if (props.user.profile !== PROFILE.ADMINISTRATOR.slug) return <Redirect to={{pathname: '/'}} />

              const content = {
                profile: PROFILE,
                workspaceList: [],
                userList: []
              }

              props.renderAppFullscreen({slug: 'admin_workspace_user', hexcolor: '#7d4e24', type: 'user'}, props.user, content)
              return null
            }} />
          </div>
        )}
      </div>
    )
  }
}

const mapStateToProps = ({ user }) => ({ user })
export default withRouter(connect(mapStateToProps)(appFactory(AppFullscreenRouter)))
