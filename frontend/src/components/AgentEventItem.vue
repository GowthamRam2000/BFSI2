<template>
  <div class="event-item">
    <div class="event-header">
      <span class="pill">{{ displayName || event.agent }}</span>
      <span>{{ time }}</span>
    </div>
    <div><strong>{{ event.action }}</strong> - {{ event.detail }}</div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  event: { agent: string; action: string; detail: string; ts: string };
  displayName?: string;
}>();

const time = computed(() => {
  const date = new Date(props.event.ts);
  if (Number.isNaN(date.getTime())) {
    return "";
  }
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
});
</script>
