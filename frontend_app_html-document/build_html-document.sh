#!/bin/bash

# shellcheck disable=SC1091
. ../bash_library.sh # source bash_library.sh

windoz=""
if [[ $1 = "-w" ]]; then
    windoz="windoz"
fi

log "build frontend_app_html-document"
npm run build$windoz && loggood "success" || logerror "some error"
log "copying built file to frontend/"
cp dist/html-document.app.js ../frontend/dist/app && loggood "success" || logerror "some error"
log "copying en translation.json"
cp i18next.scanner/en/translation.json ../frontend/dist/app/html-document_en_translation.json && loggood "success" || logerror "some error"
log "copying fr translation.json"
cp i18next.scanner/fr/translation.json ../frontend/dist/app/html-document_fr_translation.json && loggood "success" || logerror "some error"
