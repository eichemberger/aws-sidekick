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
          <h1 class="text-3xl font-bold text-white mb-3">AWS Sidekick</h1>
          <p class="text-gray-400 mb-10 text-lg max-w-md mx-auto">How can I help you with your AWS infrastructure today?</p>
          
          <!-- Example Prompts -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-3xl mx-auto">
            <button
              v-for="example in examplePrompts"
              :key="example"
              @click="$emit('use-example', example)"
              class="group p-5 text-left rounded-xl border border-gray-700 hover:border-blue-500/50 bg-gray-800/50 hover:bg-gray-800 transition-all duration-200 hover:shadow-lg hover:shadow-blue-500/10"
            >
              <div class="text-sm text-gray-300 group-hover:text-white transition-colors">{{ example }}</div>
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
                 : 'bg-gray-800/50 border border-gray-700/50'">
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
                  class="p-2 rounded-lg hover:bg-gray-700/50 text-gray-400 hover:text-white transition-colors"
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
        
        <!-- Typing Indicator -->
        <TypingIndicator v-if="isLoading" :loading-message="loadingMessage" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineAsyncComponent } from 'vue'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
import 'highlight.js/styles/github-dark.css'
import type { ChatMessage } from '@/types/api'

// Lazy load typing indicator
const TypingIndicator = defineAsyncComponent(() => import('./TypingIndicator.vue'))

interface Props {
  messages: ChatMessage[]
  isLoading: boolean
  loadingMessage: string
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
  @apply text-gray-100 leading-relaxed;
  font-size: 15px;
  line-height: 1.7;
}

/* Typography */
.markdown-content :deep(h1) {
  @apply text-2xl font-bold text-white mb-4 mt-6 pb-2 border-b-2 border-blue-500/30;
}

.markdown-content :deep(h2) {
  @apply text-xl font-semibold text-blue-300 mb-3 mt-5;
}

.markdown-content :deep(h3) {
  @apply text-lg font-semibold text-green-300 mb-2 mt-4;
}

.markdown-content :deep(h4) {
  @apply text-base font-semibold text-yellow-300 mb-2 mt-3;
}

.markdown-content :deep(p) {
  @apply mb-4 text-gray-200;
}

.markdown-content :deep(strong) {
  @apply font-semibold text-white;
}

.markdown-content :deep(em) {
  @apply italic text-gray-300;
}

/* Lists */
.markdown-content :deep(ul) {
  @apply mb-4 space-y-1;
}

.markdown-content :deep(ol) {
  @apply mb-4 space-y-1;
}

.markdown-content :deep(li) {
  @apply text-gray-200 leading-relaxed;
  padding-left: 0.5rem;
  margin-left: 1.5rem;
  position: relative;
}

.markdown-content :deep(ul li::before) {
  content: "•";
  @apply absolute -left-6 text-blue-400 font-bold;
}

.markdown-content :deep(ol li::before) {
  counter-increment: list-item;
  content: counter(list-item) ".";
  @apply absolute -left-8 text-blue-400 font-semibold text-sm;
}

/* Code Blocks & Inline Code */
.markdown-content :deep(code:not(.hljs)) {
  @apply px-2 py-1 bg-gray-700/60 text-purple-300 rounded-md text-sm font-mono border border-gray-600/50;
}

.markdown-content :deep(.hljs-pre) {
  @apply my-4 rounded-xl overflow-hidden shadow-lg border border-gray-600/30;
}

.markdown-content :deep(.hljs) {
  @apply p-4 bg-gray-800/80 text-sm leading-relaxed;
  font-family: 'JetBrains Mono', 'Monaco', 'Consolas', monospace;
}

/* Tables */
.markdown-content :deep(.table-wrapper) {
  @apply my-6 overflow-x-auto rounded-xl shadow-lg border border-gray-600/30;
}

.markdown-content :deep(.aws-table) {
  @apply w-full border-collapse bg-gray-800/50;
}

.markdown-content :deep(.aws-table thead) {
  @apply bg-gray-700/50;
}

.markdown-content :deep(.aws-table th) {
  @apply px-4 py-3 text-left text-xs font-semibold text-gray-300 uppercase tracking-wider border-b border-gray-600/50;
}

.markdown-content :deep(.aws-table td) {
  @apply px-4 py-3 text-sm text-gray-200 border-b border-gray-700/30;
}

.markdown-content :deep(.aws-table tbody tr:hover) {
  @apply bg-gray-700/30;
}

/* Blockquotes */
.markdown-content :deep(blockquote) {
  @apply my-4 pl-4 py-2 border-l-4 border-blue-500/50 bg-blue-500/5 rounded-r-lg italic text-gray-300;
}

/* Links */
.markdown-content :deep(a) {
  @apply text-blue-400 hover:text-blue-300 underline underline-offset-2 transition-colors;
}

/* Horizontal Rules */
.markdown-content :deep(hr) {
  @apply my-6 border-0 h-px bg-gradient-to-r from-transparent via-gray-600 to-transparent;
}

/* AWS-specific Styling */
.markdown-content :deep(.aws-resource) {
  @apply px-2 py-0.5 rounded-md text-xs font-mono font-semibold border;
}

.markdown-content :deep(.aws-resource.ec2) {
  @apply bg-blue-500/15 text-blue-300 border-blue-500/30;
}

.markdown-content :deep(.aws-resource.security-group) {
  @apply bg-green-500/15 text-green-300 border-green-500/30;
}

.markdown-content :deep(.aws-resource.volume) {
  @apply bg-purple-500/15 text-purple-300 border-purple-500/30;
}

.markdown-content :deep(.aws-resource.subnet) {
  @apply bg-yellow-500/15 text-yellow-300 border-yellow-500/30;
}

.markdown-content :deep(.aws-resource.vpc) {
  @apply bg-indigo-500/15 text-indigo-300 border-indigo-500/30;
}

.markdown-content :deep(.aws-resource.ami) {
  @apply bg-orange-500/15 text-orange-300 border-orange-500/30;
}

.markdown-content :deep(.aws-resource.eni) {
  @apply bg-cyan-500/15 text-cyan-300 border-cyan-500/30;
}

.markdown-content :deep(.aws-resource.route-table) {
  @apply bg-pink-500/15 text-pink-300 border-pink-500/30;
}

/* Status Badges */
.markdown-content :deep(.status-badge) {
  @apply inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-semibold;
}

.markdown-content :deep(.status-badge.success) {
  @apply bg-green-500/15 text-green-300 border border-green-500/30;
}

.markdown-content :deep(.status-badge.warning) {
  @apply bg-yellow-500/15 text-yellow-300 border border-yellow-500/30;
}

.markdown-content :deep(.status-badge.error) {
  @apply bg-red-500/15 text-red-300 border border-red-500/30;
}

.markdown-content :deep(.status-badge.info) {
  @apply bg-blue-500/15 text-blue-300 border border-blue-500/30;
}

/* AWS Regions */
.markdown-content :deep(.aws-region) {
  @apply inline-flex items-center gap-1 px-2 py-0.5 bg-gray-600/20 text-gray-300 rounded-md text-sm font-mono border border-gray-600/30;
}

/* Syntax Highlighting Overrides */
.markdown-content :deep(.hljs-keyword) {
  @apply text-purple-400;
}

.markdown-content :deep(.hljs-string) {
  @apply text-green-400;
}

.markdown-content :deep(.hljs-number) {
  @apply text-orange-400;
}

.markdown-content :deep(.hljs-comment) {
  @apply text-gray-500 italic;
}
</style> 