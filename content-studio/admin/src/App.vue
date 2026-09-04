<template>
  <n-config-provider :theme="darkTheme" :locale="zhCN" :date-locale="dateZhCN">
    <n-message-provider>
      <n-dialog-provider>
        <router-view />
        <a
          class="icp-footer-link"
          href="https://beian.miit.gov.cn/"
          target="_blank"
          rel="noopener noreferrer"
        >
          鲁ICP备2026021587号
        </a>
      </n-dialog-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup>
import { darkTheme, zhCN, dateZhCN } from 'naive-ui'
</script>

<style>
body {
  margin: 0;
  padding: 0;
  background: #1a1a2e;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.icp-footer-link {
  position: fixed;
  left: 50%;
  bottom: 8px;
  transform: translateX(-50%);
  z-index: 130;
  color: rgba(255, 255, 255, 0.42);
  font-size: 12px;
  line-height: 1;
  text-decoration: none;
  white-space: nowrap;
}
.icp-footer-link:hover {
  color: rgba(255, 255, 255, 0.72);
}
</style>
