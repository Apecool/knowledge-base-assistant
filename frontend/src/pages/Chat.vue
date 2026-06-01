<template>
  <div class="flex flex-col h-full max-w-4xl mx-auto">
    <!-- Header -->
    <div class="flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-white">
      <h2 class="text-lg font-semibold text-gray-800">智能对话</h2>
      <div class="flex items-center gap-2">
        <button
          @click="clearMessages"
          class="px-3 py-1.5 text-sm text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition"
          title="清空对话"
        >
          🗑️ 清空
        </button>
        <button
          @click="newSession"
          class="px-3 py-1.5 text-sm bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition"
        >
          + 新对话
        </button>
      </div>
    </div>

    <!-- Messages -->
    <div class="flex-1 overflow-y-auto p-4 space-y-4" ref="messagesContainer">
      <div v-if="messages.length === 0" class="flex flex-col items-center justify-center h-full text-gray-400">
        <div class="text-5xl mb-4">💬</div>
        <p class="text-lg">开始与知识库对话</p>
        <p class="text-sm mt-2">输入问题，AI 将基于知识库内容回答</p>
      </div>

      <div v-for="msg in messages" :key="msg.id" class="flex" :class="msg.role === 'user' ? 'justify-end' : 'justify-start'">
        <div
          class="max-w-[75%] rounded-2xl px-4 py-3 shadow-sm"
          :class="msg.role === 'user'
            ? 'bg-blue-500 text-white rounded-br-md'
            : 'bg-gray-100 text-gray-800 rounded-bl-md'"
        >
          <div v-if="msg.role === 'assistant' && msg.streaming && !msg.content" class="flex items-center gap-2">
            <span class="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style="animation-delay: 0ms"></span>
            <span class="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style="animation-delay: 150ms"></span>
            <span class="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style="animation-delay: 300ms"></span>
          </div>
          <div v-else class="whitespace-pre-wrap text-sm leading-relaxed">{{ msg.content }}</div>
        </div>
      </div>

      <!-- Sources display -->
      <div v-if="sources.length > 0" class="border-t border-gray-100 pt-3 mt-2">
        <details class="text-xs text-gray-500">
          <summary class="cursor-pointer hover:text-gray-700 font-medium">📄 参考来源 ({{ sources.length }} 条)</summary>
          <div class="mt-2 space-y-2">
            <div v-for="(src, i) in sources" :key="i"
                 class="p-2 bg-gray-50 rounded-lg border border-gray-100">
              <div class="flex items-center justify-between mb-1">
                <span class="font-medium text-gray-600 truncate">{{ src.title || src.heading || `来源 ${i+1}` }}</span>
                <span class="ml-2 text-blue-500 shrink-0">相似度: {{ (src.score * 100).toFixed(0) }}%</span>
              </div>
              <p class="text-gray-400 line-clamp-2">{{ src.document }}</p>
            </div>
          </div>
        </details>
      </div>

      <!-- Error -->
      <div v-if="error" class="text-center p-3 bg-red-50 text-red-500 rounded-lg text-sm">
        ❌ {{ error }}
      </div>
    </div>

    <!-- Input -->
    <div class="border-t border-gray-200 p-4 bg-white">
      <form @submit.prevent="handleSend" class="flex gap-2">
        <input
          v-model="input"
          type="text"
          placeholder="输入你的问题..."
          class="flex-1 px-4 py-2.5 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent text-sm"
          :disabled="loading"
        />
        <button
          v-if="loading"
          type="button"
          @click="abortStream"
          class="px-4 py-2.5 bg-red-500 text-white rounded-xl hover:bg-red-600 transition text-sm font-medium"
        >
          停止
        </button>
        <button
          v-else
          type="submit"
          :disabled="!input.trim()"
          class="px-6 py-2.5 bg-blue-500 text-white rounded-xl hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition text-sm font-medium"
        >
          发送
        </button>
      </form>
      <p class="text-xs text-gray-400 mt-2 text-center">
        基于知识库内容回答，结果仅供参考
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'
import { useChat } from '../composables/useChat'

const { messages, loading, error, sources, sendMessage, abortStream, clearMessages, newSession } = useChat()

const input = ref('')
const messagesContainer = ref<HTMLElement | null>(null)

async function handleSend() {
  if (!input.value.trim() || loading.value) return
  const query = input.value.trim()
  input.value = ''
  await sendMessage(query)
  await nextTick()
  // Auto-scroll to bottom
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}
</script>