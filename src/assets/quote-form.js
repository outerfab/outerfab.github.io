(() => {
  'use strict';
  const form = document.querySelector('#quote-form');
  if (!form) return;
  const panels = [...form.querySelectorAll('[data-questions]')];
  const status = document.querySelector('#quote-status');
  const button = form.querySelector('button[type="submit"]');
  const email = form.elements.email;
  let sending = false;
  let receiptText = '';

  function updateService() {
    const selected = [...form.querySelectorAll('input[data-service]:checked')];
    const selectedServices = new Set(selected.map(input => input.dataset.service));
    panels.forEach(panel => {
      const active = selectedServices.has(panel.dataset.questions);
      panel.hidden = !active;
      panel.disabled = !active;
    });
    document.querySelector('#quote-question-status').textContent = selected.length ? `Questions shown for ${selected.map(input => input.value).join(', ')}.` : '';
  }
  form.querySelectorAll('input[data-service]').forEach(input => input.addEventListener('change', updateService));
  updateService();
  // Restore selected services consistently when returning through browser history.
  window.addEventListener('pageshow', updateService);
  email.addEventListener('input', () => email.setCustomValidity(''));
  email.addEventListener('invalid', () => {
    email.setCustomValidity(email.validity.valueMissing ? 'Please add your email so we can reply.' : 'Please enter a valid email address.');
  });
  if (new URLSearchParams(window.location.search).get('submission') === 'error') {
    status.textContent = 'Your request could not be confirmed. Please try again or email bonding@outerfab.com.';
  }

  form.addEventListener('submit', async event => {
    // Website Editor blocks submissions while editing.
    if (event.defaultPrevented) return;
    event.preventDefault();
    if (sending) return;
    email.setCustomValidity('');
    if (!form.reportValidity()) return;
    updateService();
    const reference = document.querySelector('#quote-reference');
    if (!reference.value) {
      reference.value = `OF-${typeof crypto.randomUUID === 'function' ? crypto.randomUUID() : Date.now().toString(36) + Math.random().toString(36).slice(2)}`;
    }
    document.querySelector('#quote-time').value = new Date().toISOString();
    const data = { service: [...form.querySelectorAll('input[data-service]:checked')].map(input => input.value).join('; ') || 'Not specified' };
    for (const [key, value] of new FormData(form)) {
      if (key.startsWith('Service: ')) continue;
      if (key === '_honeypot' || (!key.startsWith('_') && String(value).trim())) data[key] = String(value).trim();
    }
    if (!data.service) data.service = 'Not specified';
    data['Form version'] = 'quote-v2';
    sending = true;
    button.disabled = true;
    form.setAttribute('aria-busy', 'true');
    status.textContent = 'Sending your request…';
    try {
      const response = await fetch(form.action, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
        body: JSON.stringify(data)
      });
      if (!response.ok) throw new Error(`Submission failed: ${response.status}`);
      const recap = document.querySelector('#quote-recap');
      const labels = { email: 'Email', name: 'Name', service: 'Services', notes: 'Project notes' };
      const lines = [];
      for (const [key, value] of Object.entries(data)) {
        if (key.startsWith('_') || key === 'request' || key === 'Form version') continue;
        const label = labels[key] || key;
        const term = document.createElement('dt');
        const description = document.createElement('dd');
        term.textContent = label;
        description.textContent = value;
        recap.append(term, description);
        lines.push(`${label}: ${value}`);
      }
      receiptText = `Outerfab quote request\n\n${lines.join('\n\n')}\n`;
      form.hidden = true;
      const receipt = document.querySelector('#quote-receipt');
      receipt.hidden = false;
      receipt.focus();
    } catch (_) {
      status.textContent = 'We could not confirm receipt. Your answers are still here. Please try again or email bonding@outerfab.com. If you retry, use the same request reference.';
      sending = false;
      button.disabled = false;
    } finally {
      form.removeAttribute('aria-busy');
    }
  });
  document.querySelector('#quote-download').addEventListener('click', () => {
    const url = URL.createObjectURL(new Blob([receiptText], { type: 'text/plain;charset=utf-8' }));
    const link = document.createElement('a');
    link.href = url;
    link.download = 'outerfab-quote-request.txt';
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
})();
