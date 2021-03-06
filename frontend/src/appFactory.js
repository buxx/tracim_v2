import React from 'react'
import { FETCH_CONFIG } from './helper.js'
import i18n from './i18n.js'

export function appFactory (WrappedComponent) {
  return class AppFactory extends React.Component {
    renderAppFeature = (appConfig, user, idRoleUserWorkspace, content) => GLOBAL_renderAppFeature({
      loggedUser: user.logged
        ? {...user, idRoleUserWorkspace}
        : {},
      config: {
        ...appConfig,
        domContainer: 'appFeatureContainer',
        apiUrl: FETCH_CONFIG.apiUrl,
        mockApiUrl: FETCH_CONFIG.mockApiUrl, // Côme - 2018/07/31 - this should not be used, I deprecate it
        apiHeader: FETCH_CONFIG.headers,
        translation: i18n.store.data
      },
      content
    })

    renderAppFullscreen = (appConfig, user, content) => GLOBAL_renderAppFullscreen({
      loggedUser: user.logged ? user : {},
      config: {
        ...appConfig,
        domContainer: 'appFullscreenContainer',
        apiUrl: FETCH_CONFIG.apiUrl,
        apiHeader: FETCH_CONFIG.headers,
        translation: i18n.store.data
      },
      content
    })

    renderAppPopupCreation = (appConfig, user, idWorkspace, idFolder) => GLOBAL_renderAppPopupCreation({
      loggedUser: user.logged ? user : {},
      config: {
        ...appConfig,
        domContainer: 'popupCreateContentContainer',
        apiUrl: FETCH_CONFIG.apiUrl,
        mockApiUrl: FETCH_CONFIG.mockApiUrl,
        apiHeader: FETCH_CONFIG.headers, // should this be used by app ? right now, apps have their own headers
        translation: i18n.store.data
      },
      idWorkspace,
      idFolder: idFolder === 'null' ? null : idFolder
    })

    dispatchCustomEvent = (type, data) => GLOBAL_dispatchEvent({ type, data })

    render () {
      return (
        <WrappedComponent
          {...this.props}
          renderAppFeature={this.renderAppFeature}
          renderAppFullscreen={this.renderAppFullscreen}
          renderAppPopupCreation={this.renderAppPopupCreation}
          dispatchCustomEvent={this.dispatchCustomEvent}
          // hideApp={this.hideApp}
        />
      )
    }
  }
}

export default appFactory
