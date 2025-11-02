<template>
  <div class="file-detail">
    <button type="button" class="back-button" @click="emitBack">← Back to files</button>

    <p v-if="loading" class="status">Loading file information…</p>
    <p v-else-if="error" class="status error">{{ error }}</p>
    <template v-else-if="file">
      <header class="detail-header">
        <h3>{{ file.name }}</h3>
        <p class="uploader">Uploaded by {{ file.uploader }}</p>
      </header>

      <section class="summary">
        <dl>
          <div>
            <dt>Category</dt>
            <dd>{{ file.categoryLabel }}</dd>
          </div>
          <div>
            <dt>Extension</dt>
            <dd>{{ extensionLabel }}</dd>
          </div>
          <div>
            <dt>Size</dt>
            <dd>{{ sizeLabel }}</dd>
          </div>
          <div>
            <dt>Seeds</dt>
            <dd>{{ file.seeds }}</dd>
          </div>
          <div>
            <dt>Peers</dt>
            <dd>{{ file.peers }}</dd>
          </div>
        </dl>
      </section>

      <section class="description" v-if="file.description">
        <h4>Description</h4>
        <p>{{ file.description }}</p>
      </section>

      <section class="actions">
        <button type="button" :disabled="downloading" @click="emitDownload">
          {{ downloading ? 'Preparing download…' : 'Download file' }}
        </button>
        <p v-if="downloadError" class="status error">{{ downloadError }}</p>
      </section>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  file: {
    type: Object,
    default: null,
  },
  loading: {
    type: Boolean,
    default: false,
  },
  error: {
    type: String,
    default: '',
  },
  downloading: {
    type: Boolean,
    default: false,
  },
  downloadError: {
    type: String,
    default: '',
  },
});

const emit = defineEmits(['back', 'download']);

const sizeLabel = computed(() => props.file?.sizeText || props.file?.size || 'Unknown');
const extensionLabel = computed(() =>
  props.file?.extension ? props.file.extension.toUpperCase() : 'N/A'
);

function emitBack() {
  emit('back');
}

function emitDownload() {
  if (props.file) {
    emit('download', props.file);
  }
}
</script>

<style scoped>
.file-detail {
  display: grid;
  gap: 1.5rem;
}

.back-button {
  align-self: start;
  background: none;
  border: none;
  color: #89b4ff;
  cursor: pointer;
  padding: 0;
  font-size: 0.95rem;
}

.back-button:hover {
  text-decoration: underline;
}

.status {
  margin: 0;
  font-size: 0.95rem;
  color: #d8d8d8;
}

.status.error {
  color: #ff6b6b;
}

.detail-header h3 {
  margin: 0;
  font-size: 1.75rem;
}

.detail-header .uploader {
  margin: 0.35rem 0 0;
  color: #c5c5c5;
}

.summary dl {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 1rem;
  margin: 0;
}

.summary dt {
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #9c9c9c;
}

.summary dd {
  margin: 0.25rem 0 0;
  font-size: 1.05rem;
  font-weight: 600;
}

.description h4 {
  margin: 0 0 0.5rem;
}

.description p {
  margin: 0;
  color: #d7d7d7;
  line-height: 1.7;
  max-height: 9rem;
  overflow-y: auto;
  padding-right: 0.25rem;
}

.actions {
  display: grid;
  gap: 0.75rem;
  align-content: start;
}

.actions button {
  border: none;
  border-radius: 999px;
  padding: 0.75rem 1.5rem;
  background: linear-gradient(135deg, #7f5af0, #2cb67d);
  color: #0f0f0f;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.actions button:disabled {
  opacity: 0.65;
  cursor: wait;
}

.actions button:not(:disabled):hover {
  transform: translateY(-1px);
  box-shadow: 0 10px 30px rgba(127, 90, 240, 0.35);
}
</style>
