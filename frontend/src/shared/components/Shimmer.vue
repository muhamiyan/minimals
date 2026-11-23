<template>
  <div class="shimmer"><slot /></div>
</template>

<style scoped>
.shimmer {
  position: relative;
  overflow: hidden;
  background: var(--surface-green-2);
}

.shimmer::after {
  position: absolute;
  inset: 0;
  content: '';
  transform: translateX(-100%);
  background: linear-gradient(90deg, transparent, var(--surface-base), transparent);
  animation: shimmer 1.6s infinite;
}

@keyframes shimmer {
  100% {
    transform: translateX(100%);
  }
}

@media (prefers-reduced-motion: reduce) {
  .shimmer::after {
    animation: none;
  }
}
</style>
