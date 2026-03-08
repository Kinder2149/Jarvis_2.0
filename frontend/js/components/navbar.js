/**
 * Navbar Component - JARVIS 2.0
 * Barre de navigation principale
 */

import router from '../core/router.js';
import state from '../core/state.js';
import { createElement } from '../utils/dom.js';

class Navbar {
    constructor() {
        this.element = null;
        this.currentRoute = '/';
    }

    /**
     * Crée la navbar
     * @returns {HTMLElement}
     */
    render() {
        this.element = createElement('nav', { className: 'navbar' }, [
            this.renderBrand(),
            this.renderNav()
        ]);

        // Écouter les changements de route
        window.addEventListener('hashchange', () => this.updateActiveLink());

        return this.element;
    }

    /**
     * Crée le logo/brand
     * @returns {HTMLElement}
     */
    renderBrand() {
        const brand = createElement('div', { className: 'navbar-brand' }, [
            createElement('span', {}, '🤖'),
            createElement('span', {}, 'JARVIS 2.0')
        ]);

        brand.addEventListener('click', () => router.navigate('/'));

        return brand;
    }

    /**
     * Crée la navigation
     * @returns {HTMLElement}
     */
    renderNav() {
        const nav = createElement('ul', { className: 'navbar-nav' }, [
            this.createNavLink('/', '🏠 Home'),
            this.createNavLink('/chat', '💬 Chat'),
            this.createNavLink('/projects', '📁 Projets'),
            this.createNavLink('/missions', '🎯 Missions'),
            this.createNavLink('/agents', '🤖 Agents'),
            this.createNavLink('/library', '📚 Librairie')
        ]);

        return nav;
    }

    /**
     * Crée un lien de navigation
     * @param {string} path - Chemin
     * @param {string} label - Label
     * @returns {HTMLElement}
     */
    createNavLink(path, label) {
        const li = createElement('li', {});
        const link = createElement('a', {
            className: 'nav-link',
            href: `#${path}`,
            dataset: { path }
        }, label);

        link.addEventListener('click', (e) => {
            e.preventDefault();
            router.navigate(path);
        });

        li.appendChild(link);
        return li;
    }

    /**
     * Met à jour le lien actif
     */
    updateActiveLink() {
        const hash = window.location.hash.slice(1) || '/';
        const links = this.element.querySelectorAll('.nav-link');

        links.forEach(link => {
            const path = link.dataset.path;
            if (path === hash || (hash.startsWith(path) && path !== '/')) {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        });
    }
}

export default Navbar;
