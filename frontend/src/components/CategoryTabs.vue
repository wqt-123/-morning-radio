<template>
  <div class="category-tabs">
    <button
      v-for="cat in categories"
      :key="cat.value"
      class="tab-btn"
      :class="{ active: modelValue === cat.value }"
      @click="$emit('update:modelValue', cat.value)"
    >
      {{ cat.label }}
    </button>
  </div>
</template>

<script setup>
defineProps({
  categories: {
    type: Array,
    required: true,
    default: () => []
  },
  modelValue: {
    type: String,
    default: ''
  }
})

defineEmits(['update:modelValue'])
</script>

<style scoped>
.category-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tab-btn {
  padding: 6px 16px;
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.04);
  color: #9090a8;
  font-size: 0.82rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.25s ease;
  font-family: inherit;
  white-space: nowrap;
}

.tab-btn:hover {
  color: #c0c0d8;
  background: rgba(102, 126, 234, 0.1);
  border-color: rgba(102, 126, 234, 0.25);
}

.tab-btn.active {
  color: #fff;
  background: linear-gradient(135deg, #667eea, #764ba2);
  border-color: transparent;
  box-shadow: 0 2px 12px rgba(102, 126, 234, 0.3);
}
</style>
