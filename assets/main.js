/* Progressive enhancement only: all academic content is pre-rendered HTML. */
(() => {
  'use strict';

  // A keyboard-accessible mobile menu, with ordinary anchor links as fallback.
  const menuButton = document.querySelector('.menu-toggle');
  const navigation = document.querySelector('#site-nav');
  if (menuButton && navigation) {
    menuButton.hidden = false;
    navigation.dataset.collapsible = 'true';
    const setMenuOpen = (open) => {
      menuButton.setAttribute('aria-expanded', String(open));
      navigation.classList.toggle('is-open', open);
      menuButton.querySelector('span').textContent = open ? '−' : '＋';
    };
    menuButton.addEventListener('click', () => {
      setMenuOpen(menuButton.getAttribute('aria-expanded') !== 'true');
    });
    navigation.addEventListener('click', (event) => {
      if (event.target.closest('a')) setMenuOpen(false);
    });
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && menuButton.getAttribute('aria-expanded') === 'true') {
        setMenuOpen(false);
        menuButton.focus();
      }
    });
  }

  // Search and year filters combine, and work for newly added papers automatically.
  const filters = document.querySelector('.publication-filters');
  if (filters) {
    const search = filters.querySelector('#paper-search');
    const year = filters.querySelector('#paper-year');
    const cards = [...document.querySelectorAll('.publication-card')];
    const status = document.querySelector('.filter-status');
    const emptyState = document.querySelector('.empty-state');

    const applyFilters = () => {
      const terms = search.value.toLowerCase().trim().split(/\s+/).filter(Boolean);
      let visibleCount = 0;
      for (const card of cards) {
        const matchesYear = year.value === 'all' || card.dataset.year === year.value;
        const matchesSearch = terms.every((term) => card.dataset.search.includes(term));
        card.hidden = !(matchesYear && matchesSearch);
        if (!card.hidden) visibleCount += 1;
      }
      status.hidden = terms.length === 0 && year.value === 'all';
      status.textContent = `${visibleCount} of ${cards.length} publications shown.`;
      emptyState.hidden = visibleCount !== 0;
    };
    const resetFilters = () => {
      search.value = '';
      year.value = 'all';
      applyFilters();
    };

    filters.hidden = false;
    filters.addEventListener('submit', (event) => event.preventDefault());
    search.addEventListener('input', applyFilters);
    year.addEventListener('change', applyFilters);
    filters.addEventListener('reset', (event) => {
      event.preventDefault();
      resetFilters();
    });
    document.querySelector('[data-reset-filters]')?.addEventListener('click', () => {
      resetFilters();
      search.focus();
    });
    applyFilters();
  }
  // Repeat the reviewing strip at a fixed speed, without duplicate announcements.
  const marquee = document.querySelector('.service-marquee');
  if (marquee) {
    const track = marquee.querySelector('.service-track');
    const list = track.querySelector('.service-list');
    const pauseButton = document.querySelector('.service-pause');
    const originalItems = [...list.children];
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
    const speed = Number(marquee.dataset.scrollSpeed) || 36;
    let paused = false;
    let motionOverride = false;
    let animation = null;
    let lastLayout = '';

    const rebuildStrip = (force = false) => {
      const viewportWidth = marquee.clientWidth;
      const cellWidth = originalItems[0]?.getBoundingClientRect().width || 0;
      const allowMotion = !reducedMotion.matches || motionOverride;
      const layout = `${viewportWidth}:${cellWidth}:${allowMotion}`;
      // ResizeObserver can fire after setup without any width change. Keep the
      // running animation rather than repeatedly resetting it to the beginning.
      if (!force && layout === lastLayout) return;
      lastLayout = layout;
      animation?.cancel();
      animation = null;
      track.querySelectorAll('.service-copy').forEach((copy) => copy.remove());
      list.querySelectorAll('[data-fill-copy]').forEach((copy) => copy.remove());
      marquee.classList.remove('is-animated');
      pauseButton.hidden = true;
      if (!originalItems.length || !viewportWidth || !cellWidth || typeof track.animate !== 'function') return;
      pauseButton.hidden = false;
      if (!allowMotion) {
        pauseButton.textContent = 'Start scrolling';
        return;
      }

      // Fill a whole viewport even when the configured list contains one entry.
      let width = list.getBoundingClientRect().width;
      if (!width) return;
      const repeatCount = Math.ceil(viewportWidth / width);
      for (let repeat = 1; repeat < repeatCount; repeat += 1) {
        for (const item of originalItems) {
          const copy = item.cloneNode(true);
          copy.dataset.fillCopy = '';
          copy.setAttribute('aria-hidden', 'true');
          copy.setAttribute('inert', '');
          list.append(copy);
        }
      }
      width = list.getBoundingClientRect().width;
      const duplicate = list.cloneNode(true);
      duplicate.classList.add('service-copy');
      duplicate.setAttribute('aria-hidden', 'true');
      duplicate.setAttribute('inert', '');
      track.append(duplicate);
      marquee.classList.add('is-animated');
      // Animate the measured group width so the two copies join seamlessly.
      animation = track.animate(
        [{ transform: 'translateX(0)' }, { transform: `translateX(-${width}px)` }],
        { duration: (width / speed) * 1000, iterations: Infinity, easing: 'linear' }
      );
      if (paused) animation.pause();
      pauseButton.textContent = paused ? 'Resume scrolling' : 'Pause scrolling';
    };

    pauseButton.addEventListener('click', () => {
      if (!animation) {
        motionOverride = true;
        paused = false;
        rebuildStrip(true);
        return;
      }
      paused = !paused;
      if (paused) animation.pause();
      else animation.play();
      pauseButton.textContent = paused ? 'Resume scrolling' : 'Pause scrolling';
    });
    reducedMotion.addEventListener('change', () => {
      motionOverride = false;
      rebuildStrip(true);
    });
    if ('ResizeObserver' in window) {
      const resizeObserver = new ResizeObserver(() => rebuildStrip());
      resizeObserver.observe(marquee);
    } else {
      window.addEventListener('resize', () => rebuildStrip());
    }
    rebuildStrip();
  }
})();
