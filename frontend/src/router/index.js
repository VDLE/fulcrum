import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '../layouts/MainLayout.vue'
import UserStudies from '../views/UserStudies.vue'
import StudyForm from '../views/StudyForm.vue'
import SessionReporting from '../views/SessionReporting.vue'
import DataAnalytics from '../views/DataAnalytics.vue'
import PingServer from '../views/PingServer.vue'
import TestDB from '../views/TestDB.vue'
import SessionRunner from '../views/SessionRunner.vue'
import UserLogin from '../views/UserLogin.vue'
import Confirmed from '../views/Confirmed.vue'
import UserRegister from '../views/UserRegister.vue'
import SessionSetup from '@/views/SessionSetup.vue'
import { pingServer } from '@/utility/ping'
import UserProfile from '../views/UserProfile.vue'
import AboutPage from '../views/AboutPage.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  linkExactActiveClass: 'v-item-active',
  routes: [
    {
      path: '/',
      redirect: '/UserStudies',
      component: MainLayout,
      children: [
        {
          path: '/confirmed',
          name: 'Confirmed',
          component: Confirmed,
        },
        {
          path: '/register',
          name: 'UserRegister',
          component: UserRegister,
        },
        {
          path: '/UserLogin',
          name: 'UserLogin',
          component: UserLogin,
        },
        {
          path: '/profile',
          name: 'UserProfile',
          component: UserProfile,
        },
        {
          path: '/about',
          name: 'AboutPage',
          component: AboutPage,
        },
        {
          path: '/UserStudies',
          name: 'UserStudies',
          component: UserStudies,
        },
        {
          path: '/StudyForm',
          name: 'StudyForm',
          component: StudyForm,
        },
        {
          path: '/SessionReporting',
          name: 'SessionReporting',
          component: SessionReporting,
        },
        {
          path: '/DataAnalytics',
          name: 'DataAnalytics',
          component: DataAnalytics,
        },
        // TEMP to show pinging server using router
        {
          path: '/PingServer',
          name: 'Ping',
          component: PingServer,
        },
        // TEMP to show reading database using router
        {
          path: '/Test',
          name: 'TestDB',
          component: TestDB,
        },
        {
          path: '/SessionSetup',
          name: 'SessionSetup',
          component: SessionSetup,
        },
        {
          path: '/SessionRunner',
          name: 'SessionRunner',
          component: SessionRunner,
        },
      ],
    },
  ],
})

const publicPages = ['UserLogin', 'UserRegister', 'Confirmed', 'AboutPage']

router.beforeEach(async (to, from, next) => {
  if (!publicPages.includes(to.name)) {
    try {
      await pingServer()
    } catch (err) {
      // Silently fail: no redirect, no block.
    }
  }

  next()
})

export default router
