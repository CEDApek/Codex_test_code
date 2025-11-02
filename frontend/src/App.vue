<template>
  <main class="app-shell">
    <section class="branding">
      <h1>Nexus Demo</h1>
      <p class="tagline">Share resources, earn wealth, and track the blockchain.</p>
    </section>

    <LoginForm v-if="!user" @logged-in="handleLoggedIn" />

    <section v-else class="dashboard">
      <transition name="fade">
        <div v-if="miningOverlay" class="mining-overlay" role="status" aria-live="polite">
          <div class="mining-card">
            <h3>Mining in progress…</h3>
            <p>Simulating block confirmation. Hang tight while we validate the ledger.</p>
            <div class="loader" aria-hidden="true"></div>
          </div>
        </div>
      </transition>

      <header class="dashboard-header">
        <div class="user-summary">
          <h2>Hello, {{ user.username }}!</h2>
          <p class="identity">Ledger identity: {{ user.ledgerIdentity }}</p>
          <p class="role">Role: {{ user.role }}</p>
        </div>
        <button type="button" class="logout-button" @click="logout">Log out</button>
      </header>

      <section class="ledger-summary">
        <div class="wealth-card">
          <h3>Your wealth</h3>
          <p class="wealth-amount">{{ wealthDisplay }}</p>
          <p class="wealth-meta">
            Pending transactions:
            <strong>{{ wealth?.pendingTransactions ?? 0 }}</strong>
          </p>
          <button type="button" class="secondary" @click="minePending" :disabled="mining">
            {{ mining ? 'Mining…' : 'Mine pending transactions' }}
          </button>
          <p v-if="wealthError" class="status error">{{ wealthError }}</p>
          <p v-else-if="miningError" class="status error">{{ miningError }}</p>
        </div>
        <div v-if="isAdmin" class="wealth-board">
          <div class="board-header">
            <h4>Account balances</h4>
            <button
              type="button"
              class="secondary"
              @click="refreshWealthBoard"
              :disabled="wealthBoardLoading"
            >
              {{ wealthBoardLoading ? 'Refreshing…' : 'Refresh' }}
            </button>
          </div>
          <p v-if="wealthBoardError" class="status error">{{ wealthBoardError }}</p>
          <ul v-else-if="wealthBoard.length" class="board-list">
            <li v-for="entry in wealthBoard" :key="entry.account">
              <span class="account">{{ entry.account }}</span>
              <span class="balance">
                <template v-if="entry.error">{{ entry.error }}</template>
                <template v-else>{{ formatCredits(entry.wealth) }}</template>
              </span>
            </li>
          </ul>
          <p v-else class="status empty">
            Balances will appear after the first refresh.
          </p>
        </div>
        <div v-else class="wealth-board notice">
          <h4>Account balances</h4>
          <p class="status">
            Only administrators can review other members’ balances.
          </p>
        </div>
      </section>

      <nav class="dashboard-nav" aria-label="Dashboard sections">
        <button
          type="button"
          :class="{ active: activeTab === 'files' }"
          @click="switchTab('files')"
        >
          Community files
        </button>
        <button
          type="button"
          :class="{ active: activeTab === 'upload' }"
          @click="switchTab('upload')"
        >
          Upload a file
        </button>
      </nav>

      <section v-if="activeTab === 'files'" class="dashboard-panel">
        <FileDetail
          v-if="selectedFile"
          :file="detailData"
          :loading="detailLoading"
          :error="detailError"
          :downloading="downloading"
          :download-error="downloadError"
          @back="closeFileDetails"
          @download="downloadFile"
        />
        <FileList
          v-else
          :files="files"
          :loading="filesLoading"
          :error="filesError"
          :categories="categories"
          :download-error="downloadError"
          @request-upload="openUploadTab"
          @view="openFileDetails"
          @download="downloadFile"
        />
      </section>

      <section v-else class="dashboard-panel">
        <UploadForm
          :username="user.username"
          :busy="uploading"
          :categories="categories"
          @upload-start="uploading = true"
          @upload-finish="uploading = false"
          @uploaded="handleUploaded"
        />
      </section>

      <section v-if="minedBlocks.length" class="mined-history">
        <h4>Recent mining activity</h4>
        <ul>
          <li v-for="block in minedBlocks" :key="block.key">
            <span class="block-index">Block #{{ block.index }}</span>
            <span class="block-hash">{{ block.hash }}</span>
            <span class="block-time">{{ block.time }}</span>
          </li>
        </ul>
      </section>
    </section>

    <section v-if="user" class="post-login">
      <h2>Welcome back, {{ user.username }}!</h2>
      <p>Your ledger identity: <strong>{{ user.ledgerIdentity }}</strong></p>
      <article class="next-steps">
        <h3>Next steps</h3>
        <ol>
          <li>Use the community tab to search and filter shared files.</li>
          <li>Upload your own files with categories so others can discover them faster.</li>
          <li>Mine pending transactions to confirm rewards and watch balances update.</li>
        </ol>
      </article>
    </section>
  </main>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import axios from 'axios';
import LoginForm from './components/LoginForm.vue';
import FileList from './components/FileList.vue';
import UploadForm from './components/UploadForm.vue';
import FileDetail from './components/FileDetail.vue';

const user = ref(null);
const categories = ref([]);
const files = ref([]);
const filesLoading = ref(false);
const filesError = ref('');
const activeTab = ref('files');
const uploading = ref(false);

const wealth = ref(null);
const wealthError = ref('');
const mining = ref(false);
const miningOverlay = ref(false);
const miningError = ref('');
const minedBlocks = ref([]);

const MINING_SIM_BASE = 3000;
const MINING_SIM_VARIANCE = 2000;

const knownAccounts = ref(['admin', 'alice', 'bob']);
const wealthBoard = ref([]);
const wealthBoardError = ref('');
const wealthBoardLoading = ref(false);

const selectedFile = ref(null);
const selectedFileDetail = ref(null);
const detailLoading = ref(false);
const detailError = ref('');

const downloading = ref(false);
const downloadError = ref('');

onMounted(() => {
  fetchCategories();
});

const isAdmin = computed(() => user.value?.role === 'administrator');

const wealthDisplay = computed(() => {
  if (!wealth.value || wealth.value.wealth === undefined) {
    return '—';
  }
  return `${formatCredits(wealth.value.wealth)} credits`;
});

const detailData = computed(() => selectedFileDetail.value || selectedFile.value);

function formatCredits(value) {
  if (value === undefined || value === null || Number.isNaN(Number(value))) {
    return '—';
  }
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(Number(value));
}

async function fetchCategories() {
  try {
    const response = await axios.get('/api/files/categories');
    categories.value = response.data;
  } catch (error) {
    // Non-fatal; the upload form will fall back to default categories.
  }
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function ensureKnownAccount(account) {
  if (!account) return;
  if (!knownAccounts.value.includes(account)) {
    knownAccounts.value.push(account);
  }
}

function handleLoggedIn(payload) {
  user.value = payload;
  if (payload.categories) {
    categories.value = payload.categories;
  }
  ensureKnownAccount(payload.username);
  activeTab.value = 'upload';
  fetchFiles();
  refreshWealth();
}

async function fetchFiles() {
  if (!user.value) return;
  filesLoading.value = true;
  filesError.value = '';
  try {
    const response = await axios.get('/api/files');
    files.value = response.data;
  } catch (error) {
    filesError.value =
      error.response?.data?.message || 'Unable to load shared files right now.';
  } finally {
    filesLoading.value = false;
  }
}

async function refreshWealth() {
  if (!user.value) return;
  wealthError.value = '';
  try {
    const response = await axios.get('/api/ledger/balance', {
      params: { username: user.value.username, viewer: user.value.username },
    });
    wealth.value = response.data;
  } catch (error) {
    wealthError.value =
      error.response?.data?.message || 'Unable to load your wealth information.';
  }
  if (isAdmin.value) {
    await refreshWealthBoard();
  } else {
    wealthBoard.value = [];
    wealthBoardError.value = '';
    wealthBoardLoading.value = false;
  }
}

async function refreshWealthBoard() {
  if (!user.value || !isAdmin.value) {
    wealthBoardLoading.value = false;
    if (!isAdmin.value) {
      wealthBoard.value = [];
    }
    return;
  }
  wealthBoardLoading.value = true;
  wealthBoardError.value = '';
  const accounts = Array.from(new Set([...knownAccounts.value, user.value.username]));
  try {
    const entries = await Promise.all(
      accounts.map(async (account) => {
        try {
          const response = await axios.get('/api/ledger/balance', {
            params: { username: account, viewer: user.value.username },
          });
          return {
            account,
            wealth: response.data.wealth,
            pendingTransactions: response.data.pendingTransactions,
          };
        } catch (error) {
          return {
            account,
            error: error.response?.data?.message || 'Unavailable',
            wealth: 0,
          };
        }
      })
    );
    entries.sort((a, b) => (b.wealth ?? 0) - (a.wealth ?? 0));
    wealthBoard.value = entries;
  } catch (error) {
    wealthBoardError.value =
      error.response?.data?.message || 'Unable to refresh the wealth board.';
  } finally {
    wealthBoardLoading.value = false;
  }
}

async function handleUploaded() {
  await fetchFiles();
  await refreshWealth();
  activeTab.value = 'files';
}

function openUploadTab() {
  activeTab.value = 'upload';
  closeFileDetails();
}

function switchTab(tab) {
  activeTab.value = tab;
  if (tab === 'files') {
    fetchFiles();
  }
  if (tab === 'upload') {
    closeFileDetails();
  }
}

function closeFileDetails() {
  selectedFile.value = null;
  selectedFileDetail.value = null;
  detailError.value = '';
  downloadError.value = '';
}

async function openFileDetails(file) {
  if (!file || file.fileId === undefined || file.fileId === null) {
    downloadError.value = 'This file is not yet ready for download.';
    return;
  }
  selectedFile.value = file;
  selectedFileDetail.value = null;
  detailError.value = '';
  downloadError.value = '';
  detailLoading.value = true;
  try {
    const owner = encodeURIComponent(file.owner || 'community');
    const response = await axios.get(`/api/files/${owner}/${file.fileId}`);
    selectedFileDetail.value = response.data;
  } catch (error) {
    detailError.value =
      error.response?.data?.message || 'Unable to load file details right now.';
  } finally {
    detailLoading.value = false;
  }
}

async function downloadFile(file) {
  if (!file || file.fileId === undefined || file.fileId === null) {
    downloadError.value = 'This file is not yet ready for download.';
    return;
  }
  if (!user.value) {
    downloadError.value = 'Please sign in before downloading files.';
    return;
  }
  downloading.value = true;
  downloadError.value = '';
  try {
    const owner = encodeURIComponent(file.owner || 'community');
    const response = await axios.get(`/api/files/${owner}/${file.fileId}/download`, {
      responseType: 'blob',
      params: { downloader: user.value.username },
    });

    const blob = new Blob([response.data], {
      type: response.headers['content-type'] || 'application/octet-stream',
    });
    const disposition = response.headers['content-disposition'] || '';
    const match = disposition.match(/filename="?([^";]+)"?/i);
    const filename = match ? decodeURIComponent(match[1]) : file.name;

    const url = window.URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = filename;
    document.body.appendChild(anchor);
    anchor.click();
    document.body.removeChild(anchor);
    window.URL.revokeObjectURL(url);
    await refreshWealth();
    await fetchFiles();
    if (selectedFile.value?.fileId === file.fileId) {
      const updated = files.value.find(
        (entry) => entry.fileId === file.fileId && entry.owner === file.owner
      );
      if (updated) {
        await openFileDetails(updated);
      }
    }
  } catch (error) {
    downloadError.value =
      error.response?.data?.message || 'Unable to download this file right now.';
  } finally {
    downloading.value = false;
  }
}

async function minePending() {
  if (!user.value) return;
  mining.value = true;
  miningOverlay.value = true;
  miningError.value = '';
  try {
    const requestPromise = axios.post('/api/ledger/reward', {
      username: user.value.username,
    });
    const simulatedDelay =
      MINING_SIM_BASE + Math.floor(Math.random() * MINING_SIM_VARIANCE);
    const delayPromise = delay(simulatedDelay);
    let response;
    try {
      response = await requestPromise;
    } finally {
      await delayPromise;
    }
    const block = response.data?.block || {};
    const entry = {
      index: block.index ?? minedBlocks.value.length + 1,
      hash: block.hash ? String(block.hash).slice(0, 18) : 'pending…',
      time: new Date().toLocaleTimeString(),
      key: `${Date.now()}-${Math.random()}`,
    };
    minedBlocks.value = [entry, ...minedBlocks.value].slice(0, 6);
  } catch (error) {
    miningError.value =
      error.response?.data?.message || 'No pending transactions to mine right now.';
  } finally {
    mining.value = false;
    miningOverlay.value = false;
    await refreshWealth();
    await fetchFiles();
  }
}

function logout() {
  user.value = null;
  files.value = [];
  wealth.value = null;
  knownAccounts.value = ['admin', 'alice', 'bob'];
  wealthBoard.value = [];
  wealthBoardError.value = '';
  minedBlocks.value = [];
  selectedFile.value = null;
  selectedFileDetail.value = null;
  detailError.value = '';
  downloadError.value = '';
  activeTab.value = 'files';
}
</script>

<style scoped>
.app-shell {
  width: min(980px, 94vw);
  padding: 3rem;
  background: rgba(30, 30, 30, 0.85);
  border-radius: 24px;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.45);
  display: grid;
  gap: 2.25rem;
}

.branding h1 {
  font-size: 3rem;
  margin: 0;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.tagline {
  margin-top: 0.5rem;
  color: #cccccc;
}

.dashboard {
  background: rgba(0, 0, 0, 0.35);
  border-radius: 16px;
  padding: 1.75rem;
  border: 1px solid rgba(255, 255, 255, 0.08);
  display: grid;
  gap: 1.75rem;
  position: relative;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 1rem;
}

.user-summary h2 {
  margin: 0;
  font-size: 1.8rem;
}

.identity {
  margin: 0.35rem 0 0;
  color: #c1c1c1;
}

.role {
  margin: 0.35rem 0 0;
  background: rgba(255, 255, 255, 0.08);
  padding: 0.35rem 0.75rem;
  border-radius: 999px;
  font-size: 0.9rem;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  display: inline-block;
}

.logout-button {
  align-self: center;
  border: 1px solid rgba(255, 255, 255, 0.25);
  background: rgba(255, 255, 255, 0.08);
  color: #f5f5f5;
  border-radius: 999px;
  padding: 0.45rem 1.2rem;
  cursor: pointer;
  transition: background 0.2s ease;
}

.logout-button:hover {
  background: rgba(255, 255, 255, 0.18);
}

.mining-overlay {
  position: absolute;
  inset: 0;
  background: rgba(12, 12, 18, 0.82);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 16px;
  z-index: 5;
}

.mining-card {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 18px;
  padding: 2.25rem;
  text-align: center;
  box-shadow: 0 18px 40px rgba(0, 0, 0, 0.35);
  max-width: 420px;
  display: grid;
  gap: 1rem;
}

.mining-card h3 {
  margin: 0;
  font-size: 1.6rem;
  letter-spacing: 0.04em;
}

.mining-card p {
  margin: 0;
  color: #d5d5d5;
}

.loader {
  margin: 0 auto;
  width: 3.25rem;
  height: 3.25rem;
  border-radius: 50%;
  border: 4px solid rgba(127, 90, 240, 0.35);
  border-top-color: #2cb67d;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

.ledger-summary {
  display: grid;
  gap: 1.5rem;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
}

.wealth-card,
.wealth-board {
  background: rgba(0, 0, 0, 0.28);
  border-radius: 16px;
  padding: 1.25rem;
  border: 1px solid rgba(255, 255, 255, 0.07);
  display: grid;
  gap: 0.75rem;
}

.wealth-board.notice {
  align-content: start;
  gap: 0.5rem;
}

.wealth-board.notice .status {
  color: #c1c1c1;
}

.wealth-card h3,
.wealth-board h4 {
  margin: 0;
}

.wealth-amount {
  margin: 0;
  font-size: 2rem;
  font-weight: 700;
}

.wealth-meta {
  margin: 0;
  color: #d0d0d0;
}

.secondary {
  border: 1px solid rgba(255, 255, 255, 0.25);
  background: rgba(255, 255, 255, 0.08);
  color: #f5f5f5;
  border-radius: 999px;
  padding: 0.45rem 1rem;
  cursor: pointer;
  transition: background 0.2s ease;
}

.secondary:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.16);
}

.secondary:disabled {
  opacity: 0.6;
  cursor: wait;
}

.status {
  margin: 0;
  font-size: 0.95rem;
  color: #d8d8d8;
}

.status.error {
  color: #ff6b6b;
}

.status.empty {
  color: #a6a6a6;
  font-style: italic;
}

.board-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.75rem;
}

.board-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 0.5rem;
}

.board-list li {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.45rem 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.board-list li:last-child {
  border-bottom: none;
}

.board-list .account {
  font-weight: 600;
}

.board-list .balance {
  font-variant-numeric: tabular-nums;
}

.dashboard-nav {
  display: inline-flex;
  align-items: center;
  gap: 0.75rem;
  background: rgba(255, 255, 255, 0.04);
  border-radius: 999px;
  padding: 0.35rem;
}

.dashboard-nav button {
  border: none;
  background: transparent;
  color: #f9f9f9;
  padding: 0.5rem 1.1rem;
  border-radius: 999px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s ease, color 0.2s ease;
}

.dashboard-nav button.active,
.dashboard-nav button:hover {
  background: rgba(255, 255, 255, 0.18);
  color: #0f0f0f;
}

.dashboard-panel {
  background: rgba(0, 0, 0, 0.22);
  border-radius: 16px;
  padding: 1.5rem;
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.mined-history {
  background: rgba(0, 0, 0, 0.22);
  border-radius: 16px;
  padding: 1.25rem 1.5rem;
  border: 1px solid rgba(255, 255, 255, 0.06);
  display: grid;
  gap: 0.75rem;
}

.mined-history h4 {
  margin: 0;
}

.mined-history ul {
  margin: 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 0.5rem;
}

.mined-history li {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  font-size: 0.9rem;
}

.block-index {
  font-weight: 600;
}

.block-hash {
  font-family: 'Fira Code', 'Courier New', monospace;
  color: #9ddcff;
}

.block-time {
  color: #c5c5c5;
}

.post-login {
  background: rgba(0, 0, 0, 0.28);
  border-radius: 16px;
  padding: 1.5rem;
  border: 1px solid rgba(255, 255, 255, 0.07);
  display: grid;
  gap: 1rem;
}

.next-steps ol {
  margin: 0;
  padding-left: 1.25rem;
}

@media (max-width: 720px) {
  .app-shell {
    padding: 2rem;
  }

  .dashboard {
    padding: 1.25rem;
  }

  .dashboard-panel {
    padding: 1.25rem;
  }
}
</style>
