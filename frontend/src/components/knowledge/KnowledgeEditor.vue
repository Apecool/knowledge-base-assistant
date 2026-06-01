<template>
  <div class="max-w-3xl mx-auto">
    <!-- File Upload Area (only show in create mode, not edit mode) -->
    <div v-if="!editMode" class="mb-6">
      <div
        class="border-2 border-dashed border-gray-300 rounded-xl p-6 text-center cursor-pointer
               hover:border-blue-400 hover:bg-blue-50/30 transition"
        :class="{ 'border-blue-400 bg-blue-50/50': dragging }"
        @dragover.prevent="dragging = true"
        @dragleave="dragging = false"
        @drop.prevent="handleDrop"
        @click="triggerFileInput"
      >
        <input
          ref="fileInput"
          type="file"
          accept=".txt,.md,.pdf,.docx"
          class="hidden"
          @change="handleFileSelect"
        />
        <div v-if="!uploading">
          <div class="text-3xl mb-2">📄</div>
          <p class="text-gray-600 text-sm">拖拽文件到此处，或点击选择文件</p>
          <p class="text-gray-400 text-xs mt-1">支持 .txt .md .pdf .docx 格式</p>
        </div>
        <div v-else class="flex flex-col items-center">
          <div class="w-48 h-2 bg-gray-200 rounded-full overflow-hidden mb-2">
            <div class="h-full bg-blue-500 rounded-full animate-pulse" style="width: 60%"></div>
          </div>
          <p class="text-gray-500 text-sm">正在上传解析...</p>
        </div>
      </div>
      <p v-if="uploadError" class="text-red-500 text-xs mt-1">{{ uploadError }}</p>
    </div>

    <div class="border-t border-gray-200 pt-6">
      <div class="editor-form space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">标题</label>
          <input v-model="form.title" type="text" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent" placeholder="请输入标题" />
        </div>
        <div class="flex gap-4">
          <div class="flex-1">
            <label class="block text-sm font-medium text-gray-700 mb-1">分类</label>
            <input v-model="form.category" type="text" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent" placeholder="分类名称" />
          </div>
          <div class="flex-1">
            <label class="block text-sm font-medium text-gray-700 mb-1">标签（逗号分隔）</label>
            <input v-model="form.tags" type="text" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent" placeholder="tag1, tag2" />
          </div>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">内容</label>
          <textarea v-model="form.content" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent" rows="12" placeholder="请输入内容"></textarea>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">来源</label>
          <input v-model="form.source" type="text" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent" placeholder="来源链接或备注" />
        </div>
        <div class="flex gap-3 justify-end pt-4 border-t border-gray-200">
          <button @click="$emit('cancel')" class="px-5 py-2 text-sm text-gray-600 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition">取消</button>
          <button @click="handleSave" :disabled="!isValid" class="px-5 py-2 text-sm text-white bg-blue-500 rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, computed, ref } from 'vue'
import type { KnowledgeItemResponse } from '../../types/api'
import { uploadAPI } from '../../api/upload'

const props = defineProps<{
  initialData?: KnowledgeItemResponse | null
  editMode?: boolean
}>()

const emit = defineEmits<{
  save: [data: { title: string; content: string; category?: string; tags?: string; source?: string }]
  cancel: []
}>()

const form = reactive({
  title: props.initialData?.title || '',
  content: props.initialData?.content || '',
  category: props.initialData?.category || '',
  tags: props.initialData?.tags || '',
  source: props.initialData?.source || '',
})

const dragging = ref(false)
const uploading = ref(false)
const uploadError = ref('')
const fileInput = ref<HTMLInputElement | null>(null)

function triggerFileInput() {
  fileInput.value?.click()
}

const isValid = computed(() => form.title.trim().length > 0 && form.content.trim().length > 0)

async function handleFileSelect(e: Event) {
  const target = e.target as HTMLInputElement
  if (target.files?.length) {
    await processFile(target.files[0])
    target.value = '' // Reset so same file can be re-uploaded
  }
}

async function handleDrop(e: DragEvent) {
  dragging.value = false
  const file = e.dataTransfer?.files?.[0]
  if (file) {
    await processFile(file)
  }
}

async function processFile(file: File) {
  const ext = '.' + file.name.split('.').pop()?.toLowerCase()
  const supported = ['.txt', '.md', '.pdf', '.docx']
  if (!supported.includes(ext)) {
    uploadError.value = `不支持的文件格式: ${ext}。支持: .txt .md .pdf .docx`
    return
  }

  uploadError.value = ''
  uploading.value = true

  try {
    // Only parse the file, don't save it yet — user clicks Save to persist
    const result = await uploadAPI.parseFile(file)
    form.title = result.title
    form.content = result.content
    form.source = file.name
    uploadError.value = ''
  } catch (err: any) {
    uploadError.value = err.response?.data?.detail || err.message || '上传失败'
  } finally {
    uploading.value = false
  }
}

function handleSave() {
  if (!isValid.value) return
  emit('save', {
    title: form.title.trim(),
    content: form.content.trim(),
    category: form.category.trim() || undefined,
    tags: form.tags.trim() || undefined,
    source: form.source.trim() || undefined,
  })
}
</script>