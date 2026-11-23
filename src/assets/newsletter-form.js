(() => {
  const form = document.querySelector('#newsletter-form');
  if (!form || !window.fetch) return;
  const button = form.querySelector('button');
  const email = form.querySelector('[name="email"]');
  const status = document.querySelector('#newsletter-status');
  let sending = false;
  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (sending || button.disabled || !form.reportValidity()) return;
    sending = true;
    button.disabled = true;
    form.setAttribute('aria-busy', 'true');
    status.textContent = 'Subscribing…';
    try {
      const response = await fetch(form.action, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
        body: JSON.stringify({ email: email.value.trim() })
      });
      if (!response.ok) throw new Error('Subscription failed');
      form.reset();
      status.textContent = 'Thanks for subscribing.';
    } catch (_) {
      status.textContent = 'We could not save your email. Please try again.';
    } finally {
      sending = false;
      button.disabled = false;
      form.removeAttribute('aria-busy');
    }
  });
})();
