<template>
  <main class="app-shell">
    <section class="branding">
      <h1>Nexus Demo</h1>
      <p class="tagline">
        Share resources, earn wealth, and climb the leaderboards.
      </p>
    </section>
    <LoginForm @logged-in="handleLoggedIn" />
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
import LoginForm from './components/LoginForm.vue';

const user = ref(null);

function handleLoggedIn(payload) {
  user.value = payload;
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
