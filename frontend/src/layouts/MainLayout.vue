<template>
  <v-app>
    <v-main>
      <GlobalTopBar />
      <GlobalNavBar v-if="showNavBar" />
      <router-view :key="$route.fullPath" />
    </v-main>
  </v-app>
</template>

<!-- <style scoped>
.global-background {
  background: linear-gradient(to right, #f5f7fa, #c3cfe2);
  min-height: 100vh;
}
</style> -->

<script>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import GlobalNavBar from '../components/GlobalNavBar.vue'
import GlobalTopBar from '../components/GlobalTopBar.vue'

export default {
  components: {
    GlobalNavBar,
    GlobalTopBar,
  },
  setup() {
    const route = useRoute()

    // Do not show side bar on certain routes
    const hiddenRoutes = ['UserLogin', 'UserRegister', 'Confirmed']

    const showNavBar = computed(() => !hiddenRoutes.includes(route.name))

    return {
      showNavBar,
    }
  },
}
</script>
