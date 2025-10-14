<template>
  <form class="login-card" @submit.prevent="submit">
    <h2>Login</h2>
    <label>
      Username
      <input v-model="username" type="text" autocomplete="username" required />
    </label>
    <label>
      Password
      <input v-model="password" type="password" autocomplete="current-password" required />
    </label>
    <button type="submit" :disabled="loading">
      {{ loading ? 'Signing in…' : 'Enter Nexus' }}
    </button>
    <p v-if="error" class="error">{{ error }}</p>
  </form>
</template>

<script setup>
import { ref } from 'vue';
import axios from 'axios';

const emit = defineEmits(['logged-in']);

const username = ref('admin');
const password = ref('admin');
const loading = ref(false);
const error = ref('');

async function submit() {
  error.value = '';
  loading.value = true;
  try {
    const response = await axios.post('/api/login', {
      username: username.value,
      password: password.value,
    });
    emit('logged-in', response.data);
  } catch (err) {
    error.value = err.response?.data?.message || 'Unable to login.';
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.login-card {
  background: rgba(0, 0, 0, 0.4);
  border-radius: 16px;
  padding: 2rem;
  display: grid;
  gap: 1.25rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

label {
  display: grid;
  gap: 0.5rem;
  font-size: 0.95rem;
}

input {
  padding: 0.75rem 1rem;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.05);
  color: #fff;
}

button {
  padding: 0.85rem 1.4rem;
  border-radius: 999px;
  border: none;
  background: linear-gradient(135deg, #7f5af0, #2cb67d);
  color: #0f0f0f;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

button:disabled {
  cursor: wait;
  opacity: 0.6;
}

button:not(:disabled):hover {
  transform: translateY(-1px);
  box-shadow: 0 10px 30px rgba(127, 90, 240, 0.35);
}

.error {
  margin: 0;
  color: #ff6b6b;
  font-weight: 500;
}
</style>
