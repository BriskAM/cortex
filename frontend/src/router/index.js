import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '../stores/auth';
import LandingView from '../views/LandingView.vue';
import DashboardView from '../views/DashboardView.vue';
import RepoView from '../views/RepoView.vue';
import PrView from '../views/PrView.vue';

const routes = [
  {
    path: '/',
    name: 'landing',
    component: LandingView,
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: DashboardView,
    meta: { requiresAuth: true },
  },
  {
    path: '/:owner/:repo',
    name: 'repo',
    component: RepoView,
  },
  {
    path: '/:owner/:repo/pr/:number',
    name: 'pr',
    component: PrView,
  },
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
});

// Navigation guard to protect dashboard and user routes
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore();
  
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'landing' });
  } else {
    next();
  }
});

export default router;
