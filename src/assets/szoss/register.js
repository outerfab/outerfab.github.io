(() => {
  'use strict';
  const form = document.querySelector('#szoss-registration');
  if (!form || !form.getAttribute('action')) return;
  const status = document.querySelector('#registration-status');
  const button = form.querySelector('button[type="submit"]');
  const idle = button.textContent;
  let sending = false;
  let reference = '';
  function show(message) { status.textContent = message; status.focus(); }
  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (sending || !form.reportValidity()) return;
    const data = new FormData(form);
    if (data.get('_gotcha')) return;
    sending = true;
    reference ||= 'SZOSS-' + crypto.randomUUID();
    button.disabled = true;
    button.textContent = 'Registering… / 正在报名……';
    status.textContent = '';
    const payload = Object.fromEntries(data.entries());
    delete payload._redirect;
    delete payload._append;
    delete payload._error;
    payload.registration_reference = reference;
    payload.submitted_at = new Date().toISOString();
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 20000);
    try {
      const response = await fetch(form.action, {
        method: 'POST', headers: {'Content-Type': 'application/json', 'Accept': 'application/json'},
        body: JSON.stringify(payload), signal: controller.signal, redirect: 'error'
      });
      if (!response.ok) throw new Error('Submission not accepted');
      const accepted = await response.json();
      if (accepted.registration_reference !== reference || accepted.event_id !== payload.event_id) {
        throw new Error('Unverified submission response');
      }
      form.hidden = true;
      const title = document.createElement('h3'); title.textContent = 'Registration received / 已收到报名信息';
      const message = document.createElement('p'); message.textContent = 'We will follow up by email shortly to confirm your place and send directions and further details.';
      const chinese = document.createElement('p'); chinese.lang = 'zh-Hans'; chinese.textContent = '我们会尽快通过邮件确认你的名额，并提供到场路线及更多活动详情。';
      const receipt = document.createElement('p'); receipt.textContent = 'Registration reference / 报名编号: ' + reference;
      status.replaceChildren(title, message, chinese, receipt); status.focus();
    } catch {
      show('We could not confirm your registration. Your answers are still here. Try again when your connection is working. / 暂时无法确认报名是否成功。你填写的信息仍保留在此，网络恢复后请重试。');
      button.disabled = false; button.textContent = idle;
    } finally { clearTimeout(timeout); sending = false; }
  });
})();
