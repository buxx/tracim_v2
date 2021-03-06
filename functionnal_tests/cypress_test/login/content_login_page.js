describe('content :: login_page', function () {
    before(function () {
        cy.visit('/')
    })
    it('check all content', function () {
        cy.url().should('include', '/login')
        cy.get('.card-header.connection__header.text-center').should('be.visible')
        cy.get('.languagedropdown__btnlanguage__imgselected').should('be.visible')
        cy.get('.loginpage__footer__text').should('be.visible')
        })
})
// @philippe 08/08/2018 - Not implemented in Tracim_V2.0
//
//describe('Content :: homepage > login > research', function () {
//    before(function () {
//        cy.visit('/')
//    })
//    it('check all content', function () {
//        cy.get('.search__input.form-control').should('be.visible')
//        cy.get('.search__input.form-control').should('have.attr','placeholder')
//        cy.get('#headerInputSearch').should('be.visible')
//    })
//})

describe('Content :: homepage > login > loginbox', function () {
    before(function () {
        cy.visit('/')
    })
    it('check all content', function () {
        cy.get('input[type=email]').should('be.visible')
        cy.get('input[type=email]').should('have.attr','placeholder')
        cy.get('input[type=password]').should('be.visible')
        cy.get('input[type=password]').should('have.attr','placeholder')
        cy.get('.connection__form__btnsubmit').should('be.visible')
        cy.get('.connection__form__btnsubmit').should('have.attr','type','button')
        cy.get('.connection__form__pwforgot').should('be.visible')
    })
})
