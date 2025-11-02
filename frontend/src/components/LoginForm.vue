<template>
  <form class="login-card" @submit.prevent="submit">
    <h2>{{ mode === 'login' ? 'Login' : 'Create account' }}</h2>
    <label>
      Username
      <input v-model="username" type="text" autocomplete="username" required />
    </label>
    <label>
      Password
      <input v-model="password" type="password" autocomplete="current-password" required />
    </label>
    <label v-if="mode === 'register'">
      Confirm password
      <input
        v-model="confirmPassword"
        type="password"
        autocomplete="new-password"
        required
      />
    </label>
    <button type="submit" :disabled="loading">
      {{
        loading
          ? mode === 'login'
            ? 'Signing in…'
            : 'Creating account…'
          : mode === 'login'
          ? 'Enter Nexus'
          : 'Create account'
      }}
    </button>
    <p v-if="error" class="error">{{ error }}</p>
    <p v-if="success" class="success">{{ success }}</p>
    <p class="switcher">
      <button type="button" class="link-button" @click="toggleMode" :disabled="loading">
        {{
          mode === 'login'
            ? 'Need an account? Register for free'
            : 'Already registered? Back to login'
        }}
      </button>
    </p>
  </form>
</template>

<script setup>
import { ref } from 'vue';
import axios from 'axios';

const emit = defineEmits(['logged-in']);

const mode = ref('login');
const username = ref('');
const password = ref('');
const confirmPassword = ref('');
const loading = ref(false);
const error = ref('');
const success = ref('');

async function submit() {
  error.value = '';
  success.value = '';

  if (mode.value === 'register' && password.value !== confirmPassword.value) {
    error.value = 'Passwords do not match. Please try again.';
    return;
  }

  loading.value = true;
  try {
    if (mode.value === 'register') {
      await axios.post('/api/register', {
        username: username.value,
        password: password.value,
      });
      success.value = 'Account created! Signing you in with a fresh ledger identity.';
    }

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

function toggleMode() {
  if (loading.value) return;
  mode.value = mode.value === 'login' ? 'register' : 'login';
  error.value = '';
  success.value = '';
  password.value = '';
  confirmPassword.value = '';
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

.success {
  margin: 0;
  color: #2cb67d;
  font-weight: 500;
}

.switcher {
  margin: 0;
}

.link-button {
  background: none;
  border: none;
  color: #89b4ff;
  cursor: pointer;
  padding: 0;
  font-size: 0.95rem;
}

.link-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.link-button:not(:disabled):hover {
  text-decoration: underline;
}
</style>
