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

    <fieldset class="category-picker">
      <legend>Category</legend>
      <p class="category-hint">Choose the grouping that best matches your upload.</p>
      <div class="category-options" role="list">
        <button
          v-for="option in categoryOptions"
          :key="option.value"
          type="button"
          class="category-option"
          :class="{ active: category === option.value }"
          role="listitem"
          @click="selectCategory(option.value)"
        >
          <span class="label">{{ option.label }}</span>
        </button>
      </div>
    </fieldset>

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

    <button type="submit" :disabled="busy || isValidating">
      {{ busy ? 'Uploading…' : 'Upload and publish' }}
    </button>

    <p v-if="error" class="feedback error">{{ error }}</p>
    <p v-else-if="success" class="feedback success">{{ success }}</p>

    <transition name="fade">
      <div v-if="isValidating" class="validation-overlay" role="status" aria-live="polite">
        <div class="overlay-card">
          <span class="spinner" aria-hidden="true"></span>
          <p>{{ validationMessage }}</p>
        </div>
      </div>
    </transition>
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
const validationStage = ref('idle');

const categoryOptions = computed(() => {
  if (Array.isArray(props.categories) && props.categories.length) {
    return props.categories;
  }
  return [{ value: 'other', label: 'Other' }];
});

const isValidating = computed(() => validationStage.value !== 'idle');

const validationMessage = computed(() => {
  switch (validationStage.value) {
    case 'checking-name':
      return 'Checking for duplicate names in the community…';
    case 'validating':
      return 'Validating file contents for originality…';
    default:
      return '';
  }
});

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

function selectCategory(value) {
  category.value = value;
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
  validationStage.value = 'checking-name';

  try {
    const nameCheck = await axios.get('/api/files/validate-name', {
      params: { username: props.username, name: name.value.trim() },
    });
    if (nameCheck.data?.conflict) {
      validationStage.value = 'idle';
      const conflictName = nameCheck.data?.conflictFile?.name || name.value.trim();
      const conflictOwner = nameCheck.data?.conflictOwner
        ? ` (uploaded by ${nameCheck.data.conflictOwner})`
        : '';
      error.value = `A file named "${conflictName}" already exists in the community${conflictOwner}.`;
      return;
    }
  } catch (err) {
    validationStage.value = 'idle';
    error.value = err.response?.data?.message || 'Unable to validate the file name right now.';
    return;
  }

  validationStage.value = 'validating';
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
    validationStage.value = 'idle';
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

.validation-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 15, 15, 0.75);
  display: grid;
  place-items: center;
  z-index: 20;
}

.overlay-card {
  background: rgba(18, 18, 26, 0.92);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 1.5rem 2rem;
  display: grid;
  gap: 0.75rem;
  text-align: center;
  max-width: 320px;
}

.overlay-card p {
  margin: 0;
  font-size: 1rem;
}

.spinner {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 3px solid rgba(127, 90, 240, 0.25);
  border-top-color: #7f5af0;
  animation: spin 0.9s linear infinite;
  margin: 0 auto;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
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

.category-picker {
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(0, 0, 0, 0.24);
  padding: 1rem 1.25rem;
  display: grid;
  gap: 0.75rem;
}

.category-picker legend {
  padding: 0 0.35rem;
  font-weight: 600;
  font-size: 0.95rem;
}

.category-hint {
  margin: 0;
  font-size: 0.85rem;
  color: #b8b8b8;
}

.category-options {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 0.6rem;
}

.category-option {
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.05);
  color: #f5f5f5;
  padding: 0.65rem 0.75rem;
  cursor: pointer;
  transition: transform 0.2s ease, background 0.2s ease, box-shadow 0.2s ease;
  text-align: left;
}

.category-option .label {
  pointer-events: none;
}

.category-option:hover {
  transform: translateY(-1px);
  background: rgba(127, 90, 240, 0.18);
  box-shadow: 0 10px 24px rgba(127, 90, 240, 0.25);
}

.category-option.active {
  border-color: rgba(44, 182, 125, 0.8);
  background: linear-gradient(135deg, rgba(44, 182, 125, 0.25), rgba(127, 90, 240, 0.3));
  box-shadow: 0 10px 26px rgba(44, 182, 125, 0.3);
}
</style>

