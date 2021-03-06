describe('navigate :: workspace > create_new > thread', function () {
    before(function () {
        //login
        cy.visit('/login')
        cy.get('input[type=email]').should('be.visible')
        cy.get('input[type=email]').type('admin@admin.admin')
        cy.get('input[type=password]').type('admin@admin.admin')
        cy.get('form').find('button').get('.connection__form__btnsubmit').click()
    })
    after(function() {
        cy.get('#dropdownMenuButton').click()
        cy.get('div.setting__link').click()
        cy.url().should('include', '/login')
    })
    it ('dashboard > button', function() {
        var titre1='thread1'
        // cy.url().should('include', 'http://localhost:6543/workspaces/1/dashboard')
        cy.get('.dashboard__calltoaction .fa-comments-o').click()
        cy.get('.cardPopup__container').should('be.visible')
        cy.get('.cardPopup__header').should('be.visible')
        cy.get('.cardPopup__close').should('be.visible')
        cy.get('.cardPopup__body').should('be.visible')
        cy.get('.cardPopup__container .createcontent .createcontent__contentname').should('be.visible')
        cy.get('.cardPopup__container .createcontent .createcontent__form__input').should('have.attr', 'placeholder')
        cy.get('.cardPopup__container .createcontent .createcontent__form__input').type(titre1)
        cy.get('.cardPopup__container .createcontent .createcontent__form__input').should('have.attr', 'value', titre1)
        cy.get('.cardPopup__container .cardPopup__close').click()
        cy.get('.cardPopup__container .createcontent .createcontent__contentname').should('not.be.visible')
    })
    it ('header button', function () {
        var titre1='thread1'
        cy.get('#dropdownCreateBtn.workspace__header__btnaddcontent__label').click()
        cy.get('.show .subdropdown__link__thread__icon').click()
        cy.get('.cardPopup__container').should('be.visible')
        cy.get('.cardPopup__header').should('be.visible')
        cy.get('.cardPopup__close').should('be.visible')
        cy.get('.cardPopup__body').should('be.visible')
        cy.get('.cardPopup__container .createcontent .createcontent__contentname').should('be.visible')
        cy.get('.cardPopup__container .createcontent .createcontent__form__input').should('have.attr', 'placeholder')
        cy.get('.cardPopup__container .createcontent .createcontent__form__input').type(titre1)
        cy.get('.cardPopup__container .createcontent .createcontent__form__input').should('have.attr', 'value', titre1)
        cy.get('.cardPopup__container .cardPopup__close').click()
        cy.get('.cardPopup__container .createcontent .createcontent__contentname').should('not.be.visible')
    })
    it ('content button', function () {
        var titre1='thread1'
        cy.get('.workspace__content__button.dropdownCreateBtn .__label').click()
        cy.get('.show .subdropdown__link__thread__icon').click()
        cy.get('.cardPopup__container').should('be.visible')
        cy.get('.cardPopup__header').should('be.visible')
        cy.get('.cardPopup__close').should('be.visible')
        cy.get('.cardPopup__body').should('be.visible')
        cy.get('.cardPopup__container .createcontent .createcontent__contentname').should('be.visible')
        cy.get('.cardPopup__container .createcontent .createcontent__form__input').should('have.attr', 'placeholder')
        cy.get('.cardPopup__container .createcontent .createcontent__form__input').type(titre1)
        cy.get('.cardPopup__container .createcontent .createcontent__form__input').should('have.attr', 'value', titre1)
        cy.get('.cardPopup__container .cardPopup__close').click()
        cy.get('.cardPopup__container .createcontent .createcontent__contentname').should('not.be.visible')
    })
})
