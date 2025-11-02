<template>
  <div class="mined-blocks">
    <header class="blocks-header">
      <h3>Mined blocks</h3>
      <button type="button" class="secondary" @click="emitRefresh" :disabled="loading">
        {{ loading ? 'Refreshing…' : 'Refresh' }}
      </button>
    </header>

    <form class="block-filters" @submit.prevent="submitFilters">
      <div class="field">
        <label for="block-search">Search</label>
        <input
          id="block-search"
          v-model="localFilters.search"
          type="search"
          placeholder="Block number, hash fragment…"
        />
      </div>
      <div class="field">
        <label for="block-number">Block number</label>
        <input
          id="block-number"
          v-model="localFilters.block"
          type="number"
          min="0"
          step="1"
        />
      </div>
      <div v-if="isAdmin" class="field">
        <label for="block-miner">Miner</label>
        <input
          id="block-miner"
          v-model="localFilters.miner"
          type="text"
          placeholder="Username"
        />
      </div>
      <div class="filter-actions">
        <button type="submit" class="secondary">Apply</button>
        <button type="button" class="link-button" @click="resetFilters">Reset</button>
      </div>
    </form>

    <p v-if="loading" class="status">Loading blocks…</p>
    <p v-else-if="error" class="status error">{{ error }}</p>

    <div v-else class="blocks-table-wrapper">
      <table v-if="blocks.length" class="blocks-table">
        <thead>
          <tr>
            <th scope="col">Block</th>
            <th scope="col">Hash</th>
            <th scope="col">Mined by</th>
            <th scope="col">Date</th>
            <th scope="col">Time</th>
            <th scope="col">Transactions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="block in blocks" :key="block.index ?? Math.random()">
            <td>#{{ block.index ?? '—' }}</td>
            <td><span class="hash">{{ block.hash || '—' }}</span></td>
            <td>{{ block.miner || '—' }}</td>
            <td>{{ block.date || '—' }}</td>
            <td>{{ block.time || '—' }}</td>
            <td>{{ block.transactionCount ?? 0 }}</td>
          </tr>
        </tbody>
      </table>
      <p v-else class="status empty">
        No blocks found yet. Mine a block to populate this timeline.
      </p>
    </div>
  </div>
</template>

<script setup>
import { reactive, watch } from 'vue';

const props = defineProps({
  blocks: {
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
  isAdmin: {
    type: Boolean,
    default: false,
  },
  filters: {
    type: Object,
    default: () => ({}),
  },
});

const emit = defineEmits(['search', 'refresh']);

const localFilters = reactive({
  search: '',
  block: '',
  miner: '',
});

watch(
  () => props.filters,
  (value) => {
    if (!value) {
      localFilters.search = '';
      localFilters.block = '';
      localFilters.miner = '';
      return;
    }
    localFilters.search = value.search ?? '';
    localFilters.block = value.block ?? '';
    localFilters.miner = value.miner ?? '';
  },
  { immediate: true, deep: true }
);

watch(
  () => props.isAdmin,
  (admin) => {
    if (!admin) {
      localFilters.miner = '';
    }
  }
);

function submitFilters() {
  emit('search', { ...localFilters });
}

function resetFilters() {
  localFilters.search = '';
  localFilters.block = '';
  localFilters.miner = '';
  emit('search', { ...localFilters });
}

function emitRefresh() {
  emit('refresh');
}
</script>

<style scoped>
.mined-blocks {
  display: grid;
  gap: 1.25rem;
}

.blocks-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

.blocks-header h3 {
  margin: 0;
}

.block-filters {
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  background: rgba(255, 255, 255, 0.04);
  padding: 1rem;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.field {
  display: grid;
  gap: 0.4rem;
}

label {
  font-size: 0.85rem;
  color: #cfcfcf;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

input {
  padding: 0.65rem 0.9rem;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(0, 0, 0, 0.35);
  color: #f1f1f1;
}

.filter-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.secondary {
  border: none;
  border-radius: 999px;
  padding: 0.55rem 1.2rem;
  background: rgba(255, 255, 255, 0.12);
  color: #f5f5f5;
  cursor: pointer;
  transition: background 0.2s ease, transform 0.2s ease;
}

.secondary:not(:disabled):hover {
  background: rgba(127, 90, 240, 0.35);
  transform: translateY(-1px);
}

.secondary:disabled {
  opacity: 0.6;
  cursor: wait;
}

.link-button {
  background: none;
  border: none;
  color: #89b4ff;
  cursor: pointer;
  padding: 0;
  font-size: 0.95rem;
}

.link-button:hover {
  text-decoration: underline;
}

.status {
  margin: 0;
  color: #d5d5d5;
}

.status.error {
  color: #ff6b6b;
}

.status.empty {
  color: #a8a8a8;
  font-style: italic;
}

.blocks-table-wrapper {
  max-height: 320px;
  overflow-y: auto;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.blocks-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.95rem;
}

.blocks-table thead {
  position: sticky;
  top: 0;
  background: rgba(12, 12, 12, 0.92);
}

.blocks-table th,
.blocks-table td {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  text-align: left;
}

.blocks-table th {
  font-size: 0.8rem;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: #cfcfcf;
}

.blocks-table td {
  color: #f2f2f2;
}

.hash {
  font-family: 'Fira Code', 'Courier New', monospace;
  font-size: 0.85rem;
  word-break: break-all;
  color: #9ddcff;
}

@media (max-width: 640px) {
  .block-filters {
    grid-template-columns: 1fr;
  }

  .filter-actions {
    justify-content: flex-start;
  }
}
</style>
