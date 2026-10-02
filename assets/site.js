// Copyright (c) 2026 Hiago Kin Levi. All rights reserved. SPDX-License-Identifier: LicenseRef-Proprietary
document.querySelectorAll('[data-copy]').forEach(button => {
  button.addEventListener('click', async () => {
    const text = document.getElementById(button.dataset.copy).textContent;
    const status = button.parentElement.querySelector('[role="status"]');
    try {
      await navigator.clipboard.writeText(text);
      status.textContent = button.dataset.success;
    } catch {
      status.textContent = document.documentElement.lang.startsWith('pt') ? 'Selecione e copie o texto acima.' : 'Select and copy the text above.';
    }
  });
});
