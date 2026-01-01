<template>
  <div class="message" :class="roleClass">
    <slot />
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{ role: "user" | "agent" }>();

const roleClass = computed(() => (props.role === "user" ? "user" : "agent"));
</script>
