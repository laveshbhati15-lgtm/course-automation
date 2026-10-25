document.addEventListener('DOMContentLoaded', () => {
  // 1. Mobile Menu Toggle
  const menuToggle = document.getElementById('mobileMenuToggle');
  const navLinks = document.getElementById('navLinks');

  if (menuToggle && navLinks) {
    menuToggle.addEventListener('click', () => {
      navLinks.classList.toggle('open');
      menuToggle.setAttribute('aria-expanded', navLinks.classList.contains('open'));
    });
  }

  // 2. Tabbed Code Switching (macOS vs Windows)
  const tabButtons = document.querySelectorAll('.tab-btn');
  tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const container = btn.closest('.tab-container');
      const targetId = btn.getAttribute('data-tab');

      // Update active button within this container
      container.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      // Update active content
      container.querySelectorAll('.tab-content').forEach(c => {
        if (c.id === targetId) {
          c.classList.add('active');
        } else {
          c.classList.remove('active');
        }
      });
    });
  });

  // 3. One-Click Copy for Code Blocks
  const copyButtons = document.querySelectorAll('.copy-btn');
  copyButtons.forEach(btn => {
    btn.addEventListener('click', async () => {
      const codeBlock = btn.closest('.code-block');
      const codeEl = codeBlock ? codeBlock.querySelector('pre code') : null;
      if (!codeEl) return;

      const codeText = codeEl.innerText;
      try {
        await navigator.clipboard.writeText(codeText);
        const originalText = btn.innerHTML;
        btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg> Copied!`;
        btn.classList.add('copied');

        setTimeout(() => {
          btn.innerHTML = originalText;
          btn.classList.remove('copied');
        }, 2000);
      } catch (err) {
        console.error('Failed to copy code: ', err);
      }
    });
  });

  // 4. Accordion Toggle for Troubleshooting
  const accordionTriggers = document.querySelectorAll('.accordion-trigger');
  accordionTriggers.forEach(trigger => {
    trigger.addEventListener('click', () => {
      const item = trigger.closest('.accordion-item');
      if (item) {
        item.classList.toggle('open');
      }
    });
  });

  // 5. Active Sidebar Section Highlighting on Scroll
  const sections = document.querySelectorAll('section[id]');
  const sidebarLinks = document.querySelectorAll('.sidebar-nav a[href^="#"]');

  function highlightSidebar() {
    let scrollY = window.pageYOffset;
    let currentId = '';

    sections.forEach(section => {
      const sectionTop = section.offsetTop - 120;
      const sectionHeight = section.offsetHeight;
      if (scrollY >= sectionTop && scrollY < sectionTop + sectionHeight) {
        currentId = section.getAttribute('id');
      }
    });

    if (!currentId && sections.length > 0 && scrollY < sections[0].offsetTop) {
      currentId = sections[0].getAttribute('id');
    }

    sidebarLinks.forEach(link => {
      const href = link.getAttribute('href').substring(1);
      if (href === currentId) {
        link.classList.add('active');
      } else {
        link.classList.remove('active');
      }
    });
  }

  window.addEventListener('scroll', highlightSidebar);
  highlightSidebar();
});
