<template>
  <form class="upload-form" @submit.prevent="submit">
    <h3>Share a new file</h3>
    <p class="helper">
      Logged in as <strong>{{ username }}</strong>. Drag a file onto the dropzone or
      browse from disk, then describe it for the catalogue.
    </p>

    <div
      class="dropzone"
      :class="{ active: dragActive, filled: !!selectedFile }"
      @dragenter.prevent="onDragEnter"
      @dragover.prevent="onDragOver"
      @dragleave.prevent="onDragLeave"
      @drop.prevent="onDrop"
    >
      <input ref="fileInput" type="file" class="file-input" @change="onFileChange" />
      <div class="dropzone-content" @click="openFilePicker">
        <p v-if="!selectedFile" class="dropzone-title">
          Drop your file here or <span class="link">browse</span>
        </p>
        <div v-else class="dropzone-details">
          <p class="file-name">{{ selectedFile.name }}</p>
          <p class="file-size">{{ formattedSize }}</p>
        </div>
        <p class="hint">Files up to 100 MB are supported.</p>
      </div>
    </div>

    <label>
      File name
      <input
        v-model="name"
        type="text"
        placeholder="ClientSetup_v2.zip"
        required
        @input="onNameInput"
      />
    </label>

    <label class="category-field">
      Category
      <select v-model="category" :disabled="!categoryOptions.length">
        <option v-for="option in categoryOptions" :key="option.value" :value="option.value">
          {{ option.label }}
        </option>
        <option v-if="!categoryOptions.length" value="other">Other</option>
      </select>
    </label>

    <div class="size-readout" v-if="selectedFile">
      <span class="label">Calculated size</span>
      <span class="value">{{ formattedSize }}</span>
    </div>

    <label>
      Description <span class="optional">optional</span>
      <textarea
        v-model="description"
        rows="3"
        placeholder="Tell other users what makes this torrent special"
      ></textarea>
    </label>

    <button type="submit" :disabled="busy">
      {{ busy ? 'Uploading…' : 'Upload and publish' }}
    </button>

    <p v-if="error" class="feedback error">{{ error }}</p>
    <p v-else-if="success" class="feedback success">{{ success }}</p>
  </form>
</template>

<script setup>
import { computed, ref, watch } from 'vue';
import axios from 'axios';

const props = defineProps({
  username: {
    type: String,
    required: true,
  },
  busy: {
    type: Boolean,
    default: false,
  },
  categories: {
    type: Array,
    default: () => [],
  },
});

const emit = defineEmits(['upload-start', 'upload-finish', 'uploaded']);

const MAX_UPLOAD_BYTES = 100 * 1024 * 1024;

const name = ref('');
const description = ref('');
const category = ref('other');
const error = ref('');
const success = ref('');
const selectedFile = ref(null);
const fileInput = ref(null);
const dragActive = ref(false);
const nameManuallyEdited = ref(false);

const categoryOptions = computed(() => props.categories || []);

const formattedSize = computed(() => {
  if (!selectedFile.value) return 'No file selected yet';
  return humanFileSize(selectedFile.value.size);
});

watch(
  categoryOptions,
  (options) => {
    if (!options.length) {
      category.value = 'other';
      return;
    }
    const found = options.find((option) => option.value === category.value);
    if (!found) {
      category.value = options[0].value;
    }
  },
  { immediate: true }
);

function humanFileSize(bytes) {
  if (!bytes) return '0 MB';
  const mb = bytes / (1024 * 1024);
  if (mb >= 1) return `${mb.toFixed(mb >= 10 ? 1 : 2)} MB`;
  const kb = bytes / 1024;
  return `${kb.toFixed(0)} KB`;
}

function openFilePicker() {
  fileInput.value?.click();
}

function onFileChange(event) {
  const [file] = event.target.files || [];
  processSelectedFile(file);
  event.target.value = '';
}

function onDragEnter() {
  dragActive.value = true;
}

function onDragOver() {
  dragActive.value = true;
}

function onDragLeave() {
  dragActive.value = false;
}

function onDrop(event) {
  dragActive.value = false;
  const [file] = event.dataTransfer?.files || [];
  processSelectedFile(file);
}

function processSelectedFile(file) {
  if (!file) return;

  if (file.size === 0) {
    error.value = 'The selected file is empty. Please choose a different file.';
    selectedFile.value = null;
    return;
  }

  if (file.size > MAX_UPLOAD_BYTES) {
    error.value = 'Files larger than 100 MB are not supported.';
    selectedFile.value = null;
    return;
  }

  selectedFile.value = file;
  error.value = '';
  success.value = '';

  if (!nameManuallyEdited.value) {
    name.value = file.name;
  }
}

function onNameInput() {
  nameManuallyEdited.value = true;
}

async function submit() {
  if (!selectedFile.value) {
    error.value = 'Please choose a file to upload.';
    return;
  }

  if (!name.value.trim()) {
    error.value = 'Please provide a name for the file.';
    return;
  }

  error.value = '';
  success.value = '';
  emit('upload-start');

  const formData = new FormData();
  formData.append('file', selectedFile.value);
  formData.append('username', props.username);
  formData.append('name', name.value.trim());
  formData.append('description', description.value.trim());
  formData.append('category', category.value);

  try {
    const response = await axios.post('/api/files', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });

    emit('uploaded', response.data);
    success.value = `"${response.data.name}" is now listed for other users.`;
    name.value = '';
    description.value = '';
    const defaultCategory = categoryOptions.value[0]?.value || 'other';
    category.value = defaultCategory;
    selectedFile.value = null;
    nameManuallyEdited.value = false;
  } catch (err) {
    error.value = err.response?.data?.message || 'Unable to publish the file right now.';
  } finally {
    emit('upload-finish');
  }
}
</script>

<style scoped>
.upload-form {
  display: grid;
  gap: 1rem;
}

h3 {
  margin: 0;
  font-size: 1.5rem;
}

.helper {
  margin: 0;
  color: #c1c1c1;
  font-size: 0.95rem;
}

.dropzone {
  position: relative;
  border: 2px dashed rgba(255, 255, 255, 0.25);
  border-radius: 16px;
  padding: 1.75rem;
  display: grid;
  place-items: center;
  text-align: center;
  transition: border-color 0.2s ease, background 0.2s ease;
  background: rgba(255, 255, 255, 0.05);
}

.dropzone.active {
  border-color: #7f5af0;
  background: rgba(127, 90, 240, 0.15);
}

.dropzone.filled {
  border-color: rgba(44, 182, 125, 0.75);
  background: rgba(44, 182, 125, 0.15);
}

.file-input {
  position: absolute;
  inset: 0;
  opacity: 0;
  cursor: pointer;
}

.dropzone-content {
  display: grid;
  gap: 0.35rem;
}

.dropzone-title {
  margin: 0;
  font-weight: 600;
  font-size: 1.05rem;
}

.dropzone-details {
  display: grid;
  gap: 0.25rem;
}

.file-name {
  margin: 0;
  font-weight: 600;
}

.file-size,
.hint {
  margin: 0;
  color: #c1c1c1;
  font-size: 0.9rem;
}

.link {
  color: #7f5af0;
}

label {
  display: grid;
  gap: 0.5rem;
  font-size: 0.95rem;
}

input,
textarea {
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.05);
  color: #fff;
  padding: 0.75rem 1rem;
  font: inherit;
}

textarea {
  resize: vertical;
}

.size-readout {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 0.75rem 1rem;
  font-size: 0.95rem;
}

.size-readout .label {
  color: #c1c1c1;
}

.size-readout .value {
  font-weight: 600;
}

.optional {
  font-size: 0.8rem;
  color: #9b9b9b;
}

button {
  justify-self: start;
  padding: 0.85rem 1.6rem;
  border-radius: 999px;
  border: none;
  background: linear-gradient(135deg, #2cb67d, #7f5af0);
  color: #0f0f0f;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

button:disabled {
  cursor: wait;
  opacity: 0.65;
}

button:not(:disabled):hover {
  transform: translateY(-1px);
  box-shadow: 0 10px 30px rgba(127, 90, 240, 0.35);
}

.feedback {
  margin: 0;
  font-size: 0.9rem;
}

.feedback.error {
  color: #ff6b6b;
}

.feedback.success {
  color: #2cb67d;
}
</style>
.category-field select {
  margin-top: 0.35rem;
  padding: 0.7rem 1rem;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.05);
  color: #fff;
}

