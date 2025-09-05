document.addEventListener('DOMContentLoaded', () => {
  let refreshIntervalId = null;

  async function fetchData(url) {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  }

  function processSummaryData(summaryData) {
    if (!summaryData || !summaryData.queries) {
      return {
        total: 0,
        blocked: 0,
        percentage: 0,
        clients: 0,
        rate: 0,
        cached: 0,
        forwarded: 0,
        unique: 0,
        domains: 0,
      };
    }

    const queries = summaryData.queries;
    const clients = summaryData.clients;
    const gravity = summaryData.gravity;

    return {
      total: Number(queries.total) || 0,
      blocked: Number(queries.blocked) || 0,
      percentage: Number(queries.percent_blocked) || 0,
      clients: Number(clients.active) || 0,
      rate: Number(queries.frequency) || 0,
      cached: Number(queries.cached) || 0,
      forwarded: Number(queries.forwarded) || 0,
      unique: Number(queries.unique_domains) || 0,
      domains: Number(gravity.domains_being_blocked) || 0,
    };
  }

  async function updatePiholeUI(pihole) {
    const section = document.getElementById(`pihole-${pihole.name}-section`);
    if (!section) return;

    const nameEl = section.querySelector('.pihole-name');
    const totalEl = section.querySelector('.pihole-total');
    const blockedEl = section.querySelector('.pihole-blocked');
    const percentEl = section.querySelector('.pihole-percent');
    const clientsEl = section.querySelector('.pihole-clients');
    const statusDotEl = section.querySelector('.status-dot');
    const cacheEl = section.querySelector('.pihole-cache');
    const uniqueEl = section.querySelector('.pihole-unique');
    const domainsEl = section.querySelector('.pihole-domains');

    try {
      const rawData = await fetchData(`proxy?name=${pihole.name}`);
      if (rawData.error) throw new Error(rawData.error);

      const stats = processSummaryData(rawData);

      let rateValue;
      let rateUnit;
      if (stats.rate < 1.0) {
        rateValue = (stats.rate * 60).toFixed(1);
        rateUnit = '/min';
      } else {
        rateValue = stats.rate.toFixed(1);
        rateUnit = '/sec';
      }
      nameEl.innerHTML = `${pihole.name} <span class="text-sm font-normal text-teal-500 dark:text-teal-400">(${rateValue}${rateUnit})</span>`;

      totalEl.textContent = stats.total.toLocaleString();
      blockedEl.textContent = stats.blocked.toLocaleString();
      percentEl.textContent = `${stats.percentage.toFixed(1)}%`;
      clientsEl.textContent = stats.clients.toLocaleString();
      cacheEl.textContent = `${stats.cached.toLocaleString()} / ${stats.forwarded.toLocaleString()}`;
      uniqueEl.textContent = stats.unique.toLocaleString();
      domainsEl.textContent = stats.domains.toLocaleString();

      statusDotEl.classList.remove('bg-gray-500', 'bg-red-500');
      statusDotEl.classList.add('bg-green-500');
    } catch (error) {
      console.error(`Failed to update Pi-hole ${pihole.name} data:`, error);
      nameEl.innerHTML = `${pihole.name} <span class="text-sm font-normal text-gray-500 dark:text-gray-400">(--/sec)</span>`;
      [totalEl, blockedEl, clientsEl, uniqueEl, domainsEl].forEach((el) => (el.textContent = '--'));
      percentEl.textContent = '--%';
      cacheEl.textContent = '-- / --';
      statusDotEl.classList.remove('bg-gray-500', 'bg-green-500');
      statusDotEl.classList.add('bg-red-500');
    }
  }

  function updateTimestamp() {
    const timestampEl = document.getElementById('last-updated');
    const now = new Date();
    timestampEl.textContent = `Last updated: ${now.toLocaleTimeString()}`;
  }

  async function refreshDashboard() {
    const config = await fetch('config').then((res) => res.json());
    const enabledPiholes = config.piholes.filter((p) => p.enabled);
    enabledPiholes.forEach((pihole) => updatePiholeUI(pihole));
    updateTimestamp();
  }

  function startTimer() {
    if (refreshIntervalId) return;
    fetch('config')
      .then((res) => res.json())
      .then((config) => {
        const interval = config.refresh_interval || 1000;
        refreshDashboard();
        refreshIntervalId = setInterval(refreshDashboard, interval);
      });
  }

  function stopTimer() {
    clearInterval(refreshIntervalId);
    refreshIntervalId = null;
  }

  async function init() {
    const config = await fetch('config').then((res) => res.json());
    const mainContent = document.querySelector('main');
    mainContent.innerHTML = '';

    const enabledPiholes = config.piholes.filter((p) => p.enabled);

    enabledPiholes.forEach((pihole) => {
      const section = document.createElement('section');
      section.id = `pihole-${pihole.name}-section`;
      section.className = 'bg-white dark:bg-gray-900 p-4 rounded-lg shadow-lg w-full';
      section.innerHTML = `
                <div class="flex justify-between items-baseline mb-3">
                    <h2 class="text-xl font-semibold text-gray-700 dark:text-cyan-400 pihole-name">${pihole.name}</h2>
                    <span class="status-dot bg-gray-500"></span>
                </div>
                <div class="space-y-1.5 text-sm">
                    <div class="flex justify-between items-center">
                        <span class="text-gray-500 dark:text-gray-400">Total Queries</span>
                        <span class="font-medium text-blue-500 dark:text-blue-400 pihole-total">--</span>
                    </div>
                    <div class="flex justify-between items-center">
                        <span class="text-gray-500 dark:text-gray-400">Queries Blocked</span>
                        <span class="font-medium text-red-500 dark:text-red-400 pihole-blocked">--</span>
                    </div>
                    <div class="flex justify-between items-center">
                        <span class="text-gray-500 dark:text-gray-400">Percent Blocked</span>
                        <span class="font-medium text-yellow-600 dark:text-yellow-500 pihole-percent">--%</span>
                    </div>
                    <div class="flex justify-between items-center">
                        <span class="text-gray-500 dark:text-gray-400">Cachd / Fwded</span>
                        <span class="font-medium text-indigo-500 dark:text-indigo-400 pihole-cache">-- / --</span>
                    </div>
                    <div class="flex justify-between items-center">
                        <span class="text-gray-500 dark:text-gray-400">Unique Domains</span>
                        <span class="font-medium text-orange-500 dark:text-orange-400 pihole-unique">--</span>
                    </div>
                    <div class="flex justify-between items-center">
                        <span class="text-gray-500 dark:text-gray-400">Active Clients</span>
                        <span class="font-medium text-purple-500 dark:text-purple-400 pihole-clients">--</span>
                    </div>
                    <div class="flex justify-between items-center">
                        <span class="text-gray-500 dark:text-gray-400">Domains on Lists</span>
                        <span class="font-medium text-green-600 dark:text-green-500 pihole-domains">--</span>
                    </div>
                </div>
            `;
      mainContent.appendChild(section);
    });

    startTimer();
  }

  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      stopTimer();
    } else {
      startTimer();
    }
  });

  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('sw.js').then(
        (registration) => {
          console.log('ServiceWorker registration successful with scope: ', registration.scope);
        },
        (err) => {
          console.log('ServiceWorker registration failed: ', err);
        }
      );
    });
  }

  init();
});