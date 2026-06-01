<template>
  <div class="home-page">
    <div class="hero">
      <h1>知识库助手</h1>
      <p>高效管理、快速检索你的知识资产</p>
      <div class="actions">
        <router-link to="/login" class="btn btn-primary">立即使用</router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.home-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.hero {
  text-align: center;
  color: white;
}

.hero h1 {
  font-size: 48px;
  margin-bottom: 16px;
}

.hero p {
  font-size: 18px;
  opacity: 0.9;
  margin-bottom: 32px;
}

.btn {
  display: inline-block;
  padding: 12px 32px;
  border-radius: 6px;
  text-decoration: none;
  font-size: 16px;
  transition: all 0.2s;
}

.btn-primary {
  background: white;
  color: #667eea;
  font-weight: 600;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}
</style>