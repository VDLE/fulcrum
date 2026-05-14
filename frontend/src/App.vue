<script setup>
import { useRoute } from 'vue-router'
import { useStudyStore } from '@/stores/study'
import { computed } from 'vue'
const route = useRoute()
const studyStore = useStudyStore()
studyStore.initializeFromSession()

// Use custom key only for StudyForm
const routerViewKey = computed(() => {
  return route.name === 'StudyForm'
    ? `StudyForm-${studyStore.formResetKey}`
    : route.fullPath
})
</script>

<template>
  <v-app>
    <v-main>
      <RouterView :key="routerViewKey" />
    </v-main>
  </v-app>
</template>
