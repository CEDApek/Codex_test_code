<template>
  <div class="file-list">
    <div class="list-actions">
      <div class="search-bar">
        <label class="visually-hidden" for="file-search">Search files</label>
        <input
          id="file-search"
          v-model="searchTerm"
          type="search"
          placeholder="Search by file name"
          @keyup.enter="applySearch"
        />
        <button type="button" class="secondary" @click="applySearch">Search</button>
      </div>
      <div class="action-buttons">
        <button type="button" class="secondary" @click="toggleFilters">
          {{ showFilters ? 'Hide filters' : 'Filters' }}
        </button>
        <button type="button" class="upload-button" @click="emitUploadRequest">
          Share your own file
        </button>
      </div>
    </div>

    <transition name="fade">
      <form v-if="showFilters" class="filter-panel" @submit.prevent="applyFilters">
        <div class="filter-field">
          <label for="filter-category">Category</label>
          <select id="filter-category" v-model="pendingFilters.category">
            <option value="all">All categories</option>
            <option
              v-for="option in categories"
              :key="option.value"
              :value="option.value"
            >
              {{ option.label }}
            </option>
          </select>
        </div>

        <div class="filter-field">
          <label for="filter-extension">Extension</label>
          <select id="filter-extension" v-model="pendingFilters.extension">
            <option value="all">All extensions</option>
            <option v-for="ext in extensions" :key="ext" :value="ext">
              {{ ext.toUpperCase() }}
            </option>
          </select>
        </div>

        <div class="filter-field range">
          <label>Size (MB)</label>
          <div class="range-inputs">
            <input
              v-model.number="pendingFilters.minSize"
              type="number"
              min="0"
              max="1000"
              step="1"
            />
            <span>to</span>
            <input
              v-model.number="pendingFilters.maxSize"
              type="number"
              min="0"
              max="1000"
              step="1"
            />
          </div>
        </div>

        <div class="filter-field range">
          <label>Name length (characters)</label>
          <div class="range-inputs">
            <input
              v-model.number="pendingFilters.minLength"
              type="number"
              min="0"
              max="200"
              step="1"
            />
            <span>to</span>
            <input
              v-model.number="pendingFilters.maxLength"
              type="number"
              min="0"
              max="200"
              step="1"
            />
          </div>
        </div>

        <div class="filter-actions">
          <button type="submit" class="secondary">Apply filters</button>
          <button type="button" class="link-button" @click="resetFilters">Reset</button>
        </div>
      </form>
    </transition>

    <p v-if="loading" class="status">Loading shared files…</p>
    <p v-else-if="error" class="status error">{{ error }}</p>
    <template v-else>
      <p v-if="downloadError" class="status error">{{ downloadError }}</p>
      <p v-if="!filteredFiles.length" class="status empty">
        No files match the current search or filters. Try adjusting the criteria or upload
        something awesome to get started!
      </p>
      <table v-else class="files-table">
        <thead>
          <tr>
            <th scope="col">File</th>
            <th scope="col">Size</th>
            <th scope="col">Category</th>
            <th scope="col">Uploader</th>
            <th scope="col">Seeds</th>
            <th scope="col">Peers</th>
            <th scope="col" class="actions-col">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="file in filteredFiles" :key="file.id">
            <td>
              <button type="button" class="file-link" @click="viewDetails(file)">
                {{ file.name }}
              </button>
              <p v-if="file.description" class="description">{{ file.description }}</p>
            </td>
            <td>{{ file.size }}</td>
            <td>{{ file.categoryLabel }}</td>
            <td>{{ file.uploader }}</td>
            <td>{{ file.seeds }}</td>
            <td>{{ file.peers }}</td>
            <td class="row-actions">
              <button type="button" class="secondary" @click="download(file)">
                Download
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </template>
  </div>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue';

const props = defineProps({
  files: {
    type: Array,
    default: () => [],
  },
  loading: {
    type: Boolean,
    default: false,
  },
  error: {
    type: String,
    default: '',
  },
  categories: {
    type: Array,
    default: () => [],
  },
  downloadError: {
    type: String,
    default: '',
  },
});

const emit = defineEmits(['request-upload', 'view', 'download']);

const searchTerm = ref('');
const appliedSearch = ref('');
const showFilters = ref(false);

const defaultFilters = () => ({
  category: 'all',
  extension: 'all',
  minSize: 0,
  maxSize: 100,
  minLength: 0,
  maxLength: 200,
});

const pendingFilters = reactive(defaultFilters());
const appliedFilters = reactive(defaultFilters());

watch(
  () => props.files,
  () => {
    // Adjust max size automatically based on available files
    const biggest = Math.max(
      100,
      ...props.files.map((file) => Number(file.sizeMB ?? 0))
    );
    pendingFilters.maxSize = Math.ceil(biggest);
    appliedFilters.maxSize = Math.ceil(biggest);
  },
  { immediate: true }
);

const extensions = computed(() => {
  const set = new Set();
  for (const file of props.files) {
    if (file.extension) {
      set.add(file.extension.toLowerCase());
    }
  }
  return Array.from(set).sort();
});

const filteredFiles = computed(() => {
  const term = appliedSearch.value.trim().toLowerCase();

  return props.files.filter((file) => {
    const baseName = (file.baseName || file.name || '').toLowerCase();
    if (term && !baseName.includes(term)) {
      return false;
    }

    const category = (file.category || '').toLowerCase();
    if (appliedFilters.category !== 'all' && category !== appliedFilters.category) {
      return false;
    }

    const extension = (file.extension || '').toLowerCase();
    if (appliedFilters.extension !== 'all' && extension !== appliedFilters.extension) {
      return false;
    }

    let sizeMb = Number(file.sizeMB);
    if (!Number.isFinite(sizeMb)) {
      const sizeGbValue = Number(file.sizeGB);
      sizeMb = Number.isFinite(sizeGbValue) ? sizeGbValue * 1024 : 0;
    }
    if (Number.isFinite(appliedFilters.minSize) && sizeMb < appliedFilters.minSize) {
      return false;
    }
    if (Number.isFinite(appliedFilters.maxSize) && sizeMb > appliedFilters.maxSize) {
      return false;
    }

    const length = baseName.length;
    if (Number.isFinite(appliedFilters.minLength) && length < appliedFilters.minLength) {
      return false;
    }
    if (Number.isFinite(appliedFilters.maxLength) && length > appliedFilters.maxLength) {
      return false;
    }

    return true;
  });
});

function applySearch() {
  appliedSearch.value = searchTerm.value.trim();
}

function toggleFilters() {
  showFilters.value = !showFilters.value;
}

function applyFilters() {
  Object.assign(appliedFilters, {
    category: pendingFilters.category,
    extension: pendingFilters.extension,
    minSize: pendingFilters.minSize,
    maxSize: pendingFilters.maxSize,
    minLength: pendingFilters.minLength,
    maxLength: pendingFilters.maxLength,
  });
  showFilters.value = false;
}

function resetFilters() {
  const defaults = defaultFilters();
  Object.assign(pendingFilters, defaults);
  Object.assign(appliedFilters, defaults);
  searchTerm.value = '';
  appliedSearch.value = '';
}

function emitUploadRequest() {
  emit('request-upload');
}

function viewDetails(file) {
  emit('view', file);
}

function download(file) {
  emit('download', file);
}
</script>

<style scoped>
.file-list {
  display: grid;
  gap: 1.25rem;
}

.list-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 0.75rem;
}

.search-bar {
  display: inline-flex;
  gap: 0.5rem;
  align-items: center;
}

.search-bar input {
  padding: 0.55rem 0.85rem;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  background: rgba(255, 255, 255, 0.06);
  color: #fff;
  min-width: 220px;
}

.action-buttons {
  display: inline-flex;
  gap: 0.5rem;
  align-items: center;
}

.upload-button {
  border: none;
  border-radius: 999px;
  padding: 0.55rem 1.3rem;
  font-weight: 600;
  cursor: pointer;
  color: #0f0f0f;
  background: linear-gradient(135deg, #2cb67d, #7f5af0);
  box-shadow: 0 10px 25px rgba(127, 90, 240, 0.2);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.upload-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 16px 35px rgba(44, 182, 125, 0.25);
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

.secondary:hover {
  background: rgba(255, 255, 255, 0.16);
}

.filter-panel {
  display: grid;
  gap: 1rem;
  background: rgba(0, 0, 0, 0.28);
  padding: 1rem 1.25rem;
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.filter-field {
  display: grid;
  gap: 0.5rem;
}

.filter-field select,
.filter-field input {
  padding: 0.55rem 0.8rem;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.06);
  color: #fff;
}

.range-inputs {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.range-inputs span {
  color: #c7c7c7;
}

.filter-actions {
  display: inline-flex;
  gap: 0.75rem;
  align-items: center;
}

.link-button {
  background: none;
  border: none;
  color: #7f9cff;
  cursor: pointer;
  text-decoration: underline;
  padding: 0;
}

.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  border: 0;
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

.files-table {
  width: 100%;
  border-collapse: collapse;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 16px;
  overflow: hidden;
}

th,
td {
  text-align: left;
  padding: 0.9rem 1rem;
}

th {
  background: rgba(255, 255, 255, 0.04);
  font-weight: 600;
  font-size: 0.85rem;
  letter-spacing: 0.03em;
  text-transform: uppercase;
}

.actions-col {
  text-align: right;
}

tbody tr:nth-child(odd) {
  background: rgba(255, 255, 255, 0.02);
}

tbody tr + tr {
  border-top: 1px solid rgba(255, 255, 255, 0.04);
}

.file-link {
  background: none;
  border: none;
  padding: 0;
  font-weight: 600;
  color: #89b4ff;
  cursor: pointer;
  text-align: left;
}

.file-link:hover {
  text-decoration: underline;
}

.description {
  margin: 0.25rem 0 0;
  color: #bcbcbc;
  font-size: 0.85rem;
}

.row-actions {
  text-align: right;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
