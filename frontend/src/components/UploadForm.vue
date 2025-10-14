<template>
  <form class="upload-form" @submit.prevent="submit">
    <h3>Share a new file</h3>
    <p class="helper">
      Logged in as <strong>{{ username }}</strong>. Provide the file details below to
      broadcast it to the community catalogue.
    </p>

    <label>
      File name
      <input v-model="name" type="text" placeholder="ClientSetup_v2.zip" required />
    </label>

    <label>
      Size
      <input v-model="size" type="text" placeholder="e.g. 42.7 MB" required />
    </label>

    <label>
      Description <span class="optional">optional</span>
      <textarea
        v-model="description"
        rows="3"
        placeholder="Tell other users what makes this torrent special"
      ></textarea>
    </label>

    <button type="submit" :disabled="busy">
      {{ busy ? 'Publishing…' : 'Publish to Nexus' }}
    </button>

    <p v-if="error" class="feedback error">{{ error }}</p>
    <p v-else-if="success" class="feedback success">{{ success }}</p>
  </form>
</template>

<script setup>
import { ref } from 'vue';
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
});

const emit = defineEmits(['upload-start', 'upload-finish', 'uploaded']);

const name = ref('');
const size = ref('');
const description = ref('');
const error = ref('');
const success = ref('');

async function submit() {
  if (!name.value.trim() || !size.value.trim()) {
    error.value = 'Please provide both a file name and size.';
    return;
  }

  error.value = '';
  success.value = '';
  emit('upload-start');

  try {
    const response = await axios.post('/api/files', {
      name: name.value,
      size: size.value,
      description: description.value,
      username: props.username,
    });

    emit('uploaded', response.data);
    success.value = `"${response.data.name}" is now listed for other users.`;
    name.value = '';
    size.value = '';
    description.value = '';
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
