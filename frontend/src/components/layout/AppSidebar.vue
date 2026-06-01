<template>
  <aside class="w-[220px] bg-white border-r border-gray-200 py-4 min-h-[calc(100vh-60px)]">
    <nav class="flex flex-col gap-1">
      <router-link to="/"
                   class="flex items-center gap-2.5 px-6 py-2.5 text-gray-700 text-[15px] no-underline
                          transition border-r-[3px] border-transparent
                          hover:bg-[#f0f2ff] hover:text-[#667eea]"
                   exact-active-class="!bg-[#f0f2ff] !text-[#667eea] !border-r-[#667eea] !font-medium">
        <span class="text-lg">📚</span>
        <span>知识库</span>
      </router-link>
      <router-link to="/search"
                   class="flex items-center gap-2.5 px-6 py-2.5 text-gray-700 text-[15px] no-underline
                          transition border-r-[3px] border-transparent
                          hover:bg-[#f0f2ff] hover:text-[#667eea]"
                   active-class="bg-[#f0f2ff] text-[#667eea] border-r-[#667eea] font-medium">
        <span class="text-lg">🔍</span>
        <span>搜索</span>
      </router-link>
      <router-link to="/chat"
                   class="flex items-center gap-2.5 px-6 py-2.5 text-gray-700 text-[15px] no-underline
                          transition border-r-[3px] border-transparent
                          hover:bg-[#f0f2ff] hover:text-[#667eea]"
                   active-class="bg-[#f0f2ff] text-[#667eea] border-r-[#667eea] font-medium">
        <span class="text-lg">💬</span>
        <span>智能对话</span>
      </router-link>
    </nav>
  </aside>
</template>
