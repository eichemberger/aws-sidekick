<template>
  <div class="h-screen bg-white dark:bg-gray-900 text-gray-900 dark:text-white overflow-y-auto">
    <div class="max-w-6xl mx-auto p-6">
      <!-- AWS Account Manager -->
      <AWSAccountManager />

    </div>
  </div>
</template>

<script setup lang="ts">
import AWSAccountManager from '@/components/AWSAccountManager.vue'
</script> 