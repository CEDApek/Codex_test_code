<template>
  <div class="file-list">
    <p v-if="loading" class="status">Loading shared files…</p>
    <p v-else-if="error" class="status error">{{ error }}</p>
    <p v-else-if="!files.length" class="status empty">
      No files have been shared yet. Upload something awesome to get started!
    </p>
    <table v-else class="files-table">
      <thead>
        <tr>
          <th scope="col">File</th>
          <th scope="col">Size</th>
          <th scope="col">Uploader</th>
          <th scope="col">Seeds</th>
          <th scope="col">Peers</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="file in files" :key="file.id">
          <td>
            <span class="file-name">{{ file.name }}</span>
            <p v-if="file.description" class="description">{{ file.description }}</p>
          </td>
          <td>{{ file.size }}</td>
          <td>{{ file.uploader }}</td>
          <td>{{ file.seeds }}</td>
          <td>{{ file.peers }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
defineProps({
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
});
</script>

<style scoped>
.file-list {
  display: grid;
  gap: 1rem;
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

tbody tr:nth-child(odd) {
  background: rgba(255, 255, 255, 0.02);
}

tbody tr + tr {
  border-top: 1px solid rgba(255, 255, 255, 0.04);
}

.file-name {
  font-weight: 600;
}

.description {
  margin: 0.25rem 0 0;
  color: #bcbcbc;
  font-size: 0.85rem;
}
</style>
