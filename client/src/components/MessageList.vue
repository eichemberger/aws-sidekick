<template>
  <div class="flex-1 overflow-y-auto">
    <div class="max-w-4xl mx-auto">
      <!-- Welcome Message -->
      <div v-if="messages.length === 0" class="flex items-center justify-center h-full min-h-[60vh]">
        <div class="text-center">
          <div class="w-16 h-16 mx-auto mb-6 bg-gradient-to-br from-blue-500 via-purple-600 to-indigo-700 rounded-2xl flex items-center justify-center shadow-xl">
            <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
            </svg>
          </div>
          <h1 class="text-3xl font-bold text-primary mb-3">AWS Sidekick</h1>
          <p class="text-secondary mb-10 text-lg max-w-md mx-auto">How can I help you with your AWS infrastructure today?</p>
          
          <!-- Example Prompts -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-3xl mx-auto">
            <button
              v-for="example in examplePrompts"
              :key="example"
              @click="$emit('use-example', example)"
              class="group p-5 text-left rounded-xl border border-gray-200 dark:border-gray-700 hover:border-blue-500/50 bg-gray-50/50 dark:bg-gray-800/50 hover:bg-gray-100 dark:hover:bg-gray-800 transition-all duration-200 hover:shadow-lg hover:shadow-blue-500/10"
            >
              <div class="text-sm text-secondary group-hover:text-primary transition-colors">{{ example }}</div>
            </button>
          </div>
        </div>
      </div>

      <!-- Chat Messages -->
      <div v-else class="py-8">
        <div
          v-for="(message, index) in messages"
          :key="message.id"
          v-memo="[message.id, message.content, message.role]"
          class="group mb-8"
        >
          <div class="px-6 py-8 rounded-2xl mx-4" 
               :class="message.role === 'user' 
                 ? 'bg-gradient-to-r from-blue-600/10 to-purple-600/10 border border-blue-500/20' 
                 : 'bg-gray-50/50 dark:bg-gray-800/50 border border-gray-200/50 dark:border-gray-700/50'">
            <div class="flex gap-4">
              <!-- Avatar -->
              <div class="flex-shrink-0">
                <div class="w-10 h-10 rounded-xl flex items-center justify-center shadow-lg" 
                     :class="message.role === 'user' 
                       ? 'bg-gradient-to-br from-blue-500 to-purple-600' 
                       : 'bg-gradient-to-br from-green-500 to-emerald-600'">
                  <span class="text-white text-sm font-semibold">
                    {{ message.role === 'user' ? 'You' : 'AI' }}
                  </span>
                </div>
              </div>
              
              <!-- Message Content -->
              <div class="flex-1 min-w-0">
                <div class="markdown-content" v-html="formatMessage(message.content)"></div>
              </div>
              
              <!-- Actions -->
              <div class="opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                <button
                  @click="$emit('copy-message', message.content)"
                  class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700/50 text-secondary hover:text-primary transition-colors"
                  title="Copy message"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
import 'highlight.js/styles/github-dark.css'
import type { ChatMessage } from '@/types/api'

interface Props {
  messages: ChatMessage[]
  examplePrompts: string[]
}

interface Emits {
  (e: 'use-example', example: string): void
  (e: 'copy-message', content: string): void
}

defineProps<Props>()
defineEmits<Emits>()

// Enhanced markdown-it configuration with syntax highlighting
const md: MarkdownIt = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true,
  breaks: true,
  highlight: function (str: string, lang: string): string {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return `<pre class="hljs-pre"><code class="hljs hljs-${lang}">${hljs.highlight(str, { language: lang }).value}</code></pre>`
      } catch (__) {}
    }
    return `<pre class="hljs-pre"><code class="hljs">${md.utils.escapeHtml(str)}</code></pre>`
  }
})

const formatMessage = (content: string | undefined | null) => {
  try {
    if (!content || typeof content !== 'string') {
      console.warn('Invalid content provided to formatMessage:', content)
      return `<p class="text-yellow-400">⚠️ No content to display</p>`
    }
    
    let cleanContent = content.trim()
    if (!cleanContent) {
      return `<p class="text-yellow-400">⚠️ Empty message</p>`
    }
    
    let html = md.render(cleanContent)
    html = enhanceAWSContent(html)
    
    return html
  } catch (error) {
    console.error('Markdown parsing error:', error)
    return `<p class="text-red-400">Error rendering markdown: ${error}</p>`
  }
}

const enhanceAWSContent = (html: string) => {
  return html
    // Enhance AWS resource IDs with modern styling
    .replace(/(i-[a-f0-9]{8,17})/g, '<span class="aws-resource ec2">$1</span>')
    .replace(/(sg-[a-f0-9]{8,17})/g, '<span class="aws-resource security-group">$1</span>')
    .replace(/(vol-[a-f0-9]{8,17})/g, '<span class="aws-resource volume">$1</span>')
    .replace(/(subnet-[a-f0-9]{8,17})/g, '<span class="aws-resource subnet">$1</span>')
    .replace(/(vpc-[a-f0-9]{8,17})/g, '<span class="aws-resource vpc">$1</span>')
    .replace(/(ami-[a-f0-9]{8,17})/g, '<span class="aws-resource ami">$1</span>')
    .replace(/(eni-[a-f0-9]{8,17})/g, '<span class="aws-resource eni">$1</span>')
    .replace(/(rtb-[a-f0-9]{8,17})/g, '<span class="aws-resource route-table">$1</span>')
    
    // Enhance status indicators
    .replace(/\b(RUNNING|running|Running)\b/g, '<span class="status-badge success">✅ $1</span>')
    .replace(/\b(STOPPED|stopped|Stopped)\b/g, '<span class="status-badge warning">⚠️ $1</span>')
    .replace(/\b(TERMINATED|terminated|Terminated)\b/g, '<span class="status-badge error">❌ $1</span>')
    .replace(/\b(PENDING|pending|Pending)\b/g, '<span class="status-badge info">⏳ $1</span>')
    
    // Enhance AWS regions
    .replace(/\b(us-[a-z]+-\d+|eu-[a-z]+-\d+|ap-[a-z]+-\d+|ca-[a-z]+-\d+|sa-[a-z]+-\d+|af-[a-z]+-\d+|me-[a-z]+-\d+)\b/g, '<span class="aws-region">🌍 $1</span>')
    
    // Enhance table wrapper
    .replace(/<table>/g, '<div class="table-wrapper"><table class="aws-table">')
    .replace(/<\/table>/g, '</table></div>')
}
</script>

<style scoped>
/* Modern Markdown Styling */
.markdown-content {
  @apply text-gray-800 dark:text-gray-100 leading-relaxed;
  font-size: 15px;
  line-height: 1.7;
}

/* Typography */
.markdown-content :deep(h1) {
  @apply text-2xl font-bold text-gray-900 dark:text-white mb-4 mt-6 pb-2 border-b-2 border-blue-500/30;
}

.markdown-content :deep(h2) {
  @apply text-xl font-semibold text-blue-700 dark:text-blue-300 mb-3 mt-5;
}

.markdown-content :deep(h3) {
  @apply text-lg font-semibold text-green-700 dark:text-green-300 mb-2 mt-4;
}

.markdown-content :deep(h4) {
  @apply text-base font-semibold text-yellow-700 dark:text-yellow-300 mb-2 mt-3;
}

.markdown-content :deep(p) {
  @apply mb-4 text-gray-700 dark:text-gray-200;
}

.markdown-content :deep(strong) {
  @apply font-semibold text-gray-900 dark:text-white;
}

.markdown-content :deep(em) {
  @apply italic text-gray-700 dark:text-gray-300;
}

/* Lists */
.markdown-content :deep(ul) {
  @apply list-disc list-inside mb-4 space-y-1 text-gray-700 dark:text-gray-200;
}

.markdown-content :deep(ol) {
  @apply list-decimal list-inside mb-4 space-y-1 text-gray-700 dark:text-gray-200;
}

.markdown-content :deep(li) {
  @apply ml-4;
}

/* Code */
.markdown-content :deep(code) {
  @apply bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-200 px-2 py-1 rounded text-sm font-mono;
}

.markdown-content :deep(pre) {
  @apply bg-gray-100 dark:bg-gray-800 rounded-lg p-4 mb-4 overflow-x-auto border border-gray-200 dark:border-gray-700;
}

.markdown-content :deep(.hljs-pre) {
  @apply bg-gray-100 dark:bg-gray-800 rounded-lg p-4 mb-4 overflow-x-auto border border-gray-200 dark:border-gray-700;
}

.markdown-content :deep(.hljs) {
  @apply text-gray-800 dark:text-gray-200 bg-transparent;
}

/* Tables */
.markdown-content :deep(.table-wrapper) {
  @apply overflow-x-auto mb-4 rounded-lg border border-gray-200 dark:border-gray-700;
}

.markdown-content :deep(.aws-table) {
  @apply w-full border-collapse bg-white dark:bg-gray-800;
}

.markdown-content :deep(.aws-table th) {
  @apply bg-gray-50 dark:bg-gray-700 px-4 py-3 text-left font-semibold text-gray-900 dark:text-white border-b border-gray-200 dark:border-gray-600;
}

.markdown-content :deep(.aws-table td) {
  @apply px-4 py-3 text-gray-700 dark:text-gray-300 border-b border-gray-100 dark:border-gray-700;
}

/* AWS Resource Styling */
.markdown-content :deep(.aws-resource) {
  @apply inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 border border-blue-200 dark:border-blue-800;
}

.markdown-content :deep(.aws-resource.ec2) {
  @apply bg-orange-100 dark:bg-orange-900/30 text-orange-800 dark:text-orange-300 border-orange-200 dark:border-orange-800;
}

.markdown-content :deep(.aws-resource.security-group) {
  @apply bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300 border-red-200 dark:border-red-800;
}

.markdown-content :deep(.aws-resource.vpc) {
  @apply bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300 border-green-200 dark:border-green-800;
}

/* Status Badges */
.markdown-content :deep(.status-badge) {
  @apply inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium;
}

.markdown-content :deep(.status-badge.success) {
  @apply bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300;
}

.markdown-content :deep(.status-badge.warning) {
  @apply bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300;
}

.markdown-content :deep(.status-badge.error) {
  @apply bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300;
}

.markdown-content :deep(.status-badge.info) {
  @apply bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300;
}

/* AWS Region Badge */
.markdown-content :deep(.aws-region) {
  @apply inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-300;
}

/* Blockquotes */
.markdown-content :deep(blockquote) {
  @apply border-l-4 border-blue-500 pl-4 py-2 mb-4 bg-blue-50 dark:bg-blue-900/20 text-gray-700 dark:text-gray-300 italic;
}

/* Links */
.markdown-content :deep(a) {
  @apply text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 underline transition-colors;
}
</style> 