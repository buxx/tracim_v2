import React from 'react'
import { connect } from 'react-redux'
import classnames from 'classnames'
import { withRouter } from 'react-router-dom'
import { translate } from 'react-i18next'
import appFactory from '../appFactory.js'
import { workspaceConfig } from '../helper.js'
import Card from '../component/common/Card/Card.jsx'
import CardHeader from '../component/common/Card/CardHeader.jsx'
import CardBody from '../component/common/Card/CardBody.jsx'
import HomeNoWorkspace from '../component/Home/HomeNoWorkspace.jsx'
import HomeHasWorkspace from '../component/Home/HomeHasWorkspace.jsx'

class Home extends React.Component {
  handleClickCreateWorkspace = e => {
    e.preventDefault()
    const { props } = this
    props.renderAppPopupCreation(workspaceConfig, props.user, null, null)
  }

  render () {
    const { props } = this

    if (!props.system.workspaceListLoaded) return null

    const styleHomepage = {
      display: 'flex',
      width: '100%',
      height: '100%'
    }

    return (
      <section
        className={classnames('homepage', props.workspaceList.length === 0 ? 'primaryColorBg' : '')}
        style={styleHomepage}
      >
        <div className='container-fluid nopadding'>
          <Card customClass='homepagecard'>
            <CardHeader displayHeader={false} />

            <CardBody customClass='homepagecard'>
              {props.workspaceList.length > 0
                ? <HomeHasWorkspace user={props.user} />
                : <HomeNoWorkspace
                  canCreateWorkspace={props.canCreateWorkspace}
                  onClickCreateWorkspace={this.handleClickCreateWorkspace}
                />
              }
            </CardBody>
          </Card>
        </div>
      </section>
    )
  }
}

const mapStateToProps = ({ user, workspaceList, system }) => ({ user, workspaceList, system })
export default connect(mapStateToProps)(withRouter(appFactory(translate()(Home))))
