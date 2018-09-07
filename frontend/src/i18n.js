import i18n from 'i18next'
import { reactI18nextModule } from 'react-i18next'
import { libFrTranslation, libEnTranslation } from 'tracim_frontend_lib'
import en from '../i18next.scanner/en/translation.json'
import fr from '../i18next.scanner/fr/translation.json'

// get translation files of apps
// theses files are generated by build_appname.sh
const htmlDocEnTranslation = require('../dist/app/html-document_en_translation.json') || {}
const htmlDocFrTranslation = require('../dist/app/html-document_fr_translation.json') || {}
const threadEnTranslation = require('../dist/app/thread_en_translation.json') || {}
const threadFrTranslation = require('../dist/app/thread_fr_translation.json') || {}
const fileEnTranslation = require('../dist/app/file_en_translation.json') || {}
const fileFrTranslation = require('../dist/app/file_fr_translation.json') || {}

i18n
  .use(reactI18nextModule)
  .init({
    fallbackLng: 'en',
    // have a common namespace used around the full app
    ns: ['translation'], // namespace
    defaultNS: 'translation',
    debug: true,
    react: {
      wait: true
    },
    resources: {
      en: {
        translation: {
          ...libEnTranslation, // fronted_lib
          ...en, // frontend
          ...htmlDocEnTranslation, // html-document
          ...threadEnTranslation, // thread
          ...fileEnTranslation // file
        }
      },
      fr: {
        translation: {
          ...libFrTranslation, // fronted_lib
          ...fr, // frontend
          ...htmlDocFrTranslation, // html-document
          ...threadFrTranslation, // thread
          ...fileFrTranslation // file
        }
      }
    }
  })

i18n.idTracim = 'frontend'

export default i18n
