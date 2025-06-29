<template>
  <div 
    ref="containerRef"
    class="virtual-list"
    :style="{ height: `${containerHeight}px`, overflow: 'auto' }"
    @scroll="handleScroll"
  >
    <div 
      class="virtual-list-phantom" 
      :style="{ height: `${totalHeight}px` }"
    >
      <div 
        class="virtual-list-content"
        :style="{ 
          transform: `translateY(${startOffset}px)` 
        }"
      >
        <div
          v-for="(item, index) in visibleItems"
          :key="getItemKey(item, startIndex + index)"
          class="virtual-list-item"
          :style="{ height: `${itemHeight}px` }"
        >
          <slot 
            :item="item" 
            :index="startIndex + index"
            :is-visible="true"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'

interface Props {
  items: any[]
  itemHeight: number
  containerHeight: number
  buffer?: number
  keyField?: string
}

interface Emits {
  (e: 'scroll', event: Event): void
}

const props = withDefaults(defineProps<Props>(), {
  buffer: 5,
  keyField: 'id'
})

const emit = defineEmits<Emits>()

const containerRef = ref<HTMLElement>()
const scrollTop = ref(0)

// Computed properties for virtual scrolling
const totalHeight = computed(() => props.items.length * props.itemHeight)
const visibleCount = computed(() => Math.ceil(props.containerHeight / props.itemHeight))
const startIndex = computed(() => Math.floor(scrollTop.value / props.itemHeight))
const endIndex = computed(() => Math.min(startIndex.value + visibleCount.value + props.buffer, props.items.length))

const visibleItems = computed(() => {
  const start = Math.max(0, startIndex.value - props.buffer)
  const end = Math.min(props.items.length, endIndex.value + props.buffer)
  return props.items.slice(start, end)
})

const startOffset = computed(() => {
  const start = Math.max(0, startIndex.value - props.buffer)
  return start * props.itemHeight
})

const getItemKey = (item: any, index: number) => {
  return props.keyField && item[props.keyField] ? item[props.keyField] : index
}

const handleScroll = (event: Event) => {
  const target = event.target as HTMLElement
  scrollTop.value = target.scrollTop
  emit('scroll', event)
}

// Scroll to specific item
const scrollToItem = (index: number) => {
  if (containerRef.value) {
    const targetScrollTop = index * props.itemHeight
    containerRef.value.scrollTop = targetScrollTop
    scrollTop.value = targetScrollTop
  }
}

// Scroll to top
const scrollToTop = () => {
  if (containerRef.value) {
    containerRef.value.scrollTop = 0
    scrollTop.value = 0
  }
}

// Expose methods
defineExpose({
  scrollToItem,
  scrollToTop
})

// Throttle scroll events for better performance
let scrollTimeout: ReturnType<typeof setTimeout> | null = null
const throttledHandleScroll = (event: Event) => {
  if (scrollTimeout) {
    clearTimeout(scrollTimeout)
  }
  scrollTimeout = setTimeout(() => {
    handleScroll(event)
  }, 16) // ~60fps
}

onMounted(() => {
  if (containerRef.value) {
    containerRef.value.addEventListener('scroll', throttledHandleScroll, { passive: true })
  }
})

onUnmounted(() => {
  if (containerRef.value) {
    containerRef.value.removeEventListener('scroll', throttledHandleScroll)
  }
  if (scrollTimeout) {
    clearTimeout(scrollTimeout)
  }
})
</script>

<style scoped>
.virtual-list {
  position: relative;
}

.virtual-list-phantom {
  position: absolute;
  left: 0;
  top: 0;
  right: 0;
  z-index: -1;
}

.virtual-list-content {
  position: relative;
  left: 0;
  right: 0;
  top: 0;
}

.virtual-list-item {
  position: relative;
  box-sizing: border-box;
}
</style> 