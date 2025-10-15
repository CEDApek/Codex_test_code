<template>
  <main class="app-shell">
    <section class="branding">
      <h1>Nexus Demo</h1>
      <p class="tagline">
        Share resources, earn wealth, and climb the leaderboards.
      </p>
    </section>

    <!-- Login form shown if not logged in -->
    <LoginForm v-if="!user" @logged-in="handleLoggedIn" />

    <!-- Dashboard shown after login -->
    <section v-else class="dashboard">
      <header class="dashboard-header">
        <div>
          <h2>Hello, {{ user.username }}!</h2>
          <p class="identity">Ledger identity: {{ user.ledgerIdentity }}</p>
        </div>
        <p class="role">Role: {{ user.role }}</p>
      </header>

      <nav class="dashboard-nav" aria-label="Dashboard sections">
        <button
          type="button"
          :class="{ active: activeTab === 'files' }"
          @click="activeTab = 'files'"
        >
          Community files
        </button>
        <button
          type="button"
          :class="{ active: activeTab === 'upload' }"
          @click="activeTab = 'upload'"
        >
          Upload a file
        </button>
      </nav>

      <section v-if="activeTab === 'files'" class="dashboard-panel">
        <FileList
          :files="files"
          :loading="filesLoading"
          :error="filesError"
          @request-upload="openUploadTab"
        />
      </section>

      <section v-else class="dashboard-panel">
        <UploadForm
          :username="user.username"
          :busy="uploading"
          @upload-start="uploading = true"
          @upload-finish="uploading = false"
          @uploaded="handleUploaded"
        />
      </section>
    </section>

    <!-- Optional welcome panel below -->
    <section v-if="user" class="post-login">
      <h2>Welcome back, {{ user.username }}!</h2>
      <p>Your ledger identity: <strong>{{ user.ledgerIdentity }}</strong></p>
      <article class="next-steps">
        <h3>Next steps</h3>
        <ol>
          <li>Keep the client running to earn wealth rewards.</li>
          <li>Accumulate upload to increase your site rank.</li>
          <li>
            Explore the Hyperledger Fabric network to connect with other
            seeders.
          </li>
        </ol>
      </article>
    </section>
  </main>
</template>

<script setup>
import { ref } from 'vue';
import axios from 'axios';
import LoginForm from './components/LoginForm.vue';
import FileList from './components/FileList.vue';
import UploadForm from './components/UploadForm.vue';

const user = ref(null);
const files = ref([]);
const filesLoading = ref(false);
const filesError = ref('');
const activeTab = ref('files');
const uploading = ref(false);

function handleLoggedIn(payload) {
  user.value = payload;
  activeTab.value = 'upload';
  fetchFiles();
}

async function fetchFiles() {
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

function handleUploaded(newFile) {
  files.value = [newFile, ...files.value];
  activeTab.value = 'files';
}

function openUploadTab() {
  activeTab.value = 'upload';
}
</script>

<style scoped>
.app-shell {
  width: min(900px, 92vw);
  padding: 3rem;
  background: rgba(30, 30, 30, 0.85);
  border-radius: 24px;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.45);
  display: grid;
  gap: 2rem;
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
  gap: 1.5rem;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.dashboard-header h2 {
  margin: 0;
  font-size: 1.75rem;
}

.identity {
  margin: 0.35rem 0 0;
  color: #c1c1c1;
}

.role {
  margin: 0;
  align-self: center;
  background: rgba(255, 255, 255, 0.08);
  padding: 0.35rem 0.75rem;
  border-radius: 999px;
  font-size: 0.9rem;
  letter-spacing: 0.04em;
  text-transform: uppercase;
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

.dashboard-nav button.active {
  background: linear-gradient(135deg, #7f5af0, #2cb67d);
  color: #111;
}

.dashboard-panel {
  background: rgba(0, 0, 0, 0.35);
  border-radius: 20px;
  padding: 1.5rem;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.post-login {
  background: rgba(0, 0, 0, 0.35);
  border-radius: 16px;
  padding: 1.5rem;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.post-login h2 {
  margin-top: 0;
}

.next-steps ol {
  padding-left: 1.5rem;
}
</style>
