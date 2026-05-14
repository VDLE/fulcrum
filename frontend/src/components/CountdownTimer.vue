<template>
  <div v-if="start" class="timer-counter">
    <v-progress-circular
      :model-value="progressTimer"
      :size="150"
      :width="15"
      color="primary"
    >
    </v-progress-circular>
    <div class="timer-msgs">
      <p class="timer-msg">Starting in {{ timer }} seconds...</p>
      <p class="timer-mini-msg">
        {{ description }}
      </p>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    duration: {
      type: Number,
      default: 15,
    },
    start: {
      type: Boolean,
      default: false,
    },
    description: {
      type: String,
      default: 'About to begin',
    },
  },
  data() {
    return {
      timer: 0,
      timerInterval: null,
    }
  },
  mounted() {
    if (this.start) {
      this.startCountdown()
    }
  },
  computed: {
    // Updates UI of circular progress
    progressTimer() {
      return (this.timer / this.duration) * 100
    },
  },

  watch: {
    // Trigger the countdown start
    start(newVal) {
      if (newVal) {
        this.startCountdown()
      }
    },
  },

  methods: {
    // Logic for the countdown itself, including emitting signal upon completion
    startCountdown() {
      this.timer = this.duration
      this.timerInterval = setInterval(() => {
        if (this.timer > 0) {
          this.timer -= 1
        } else {
          clearInterval(this.timerInterval)
          this.$emit('countdown-complete')
        }
      }, 1000)
    },
  },
}
</script>

<style scoped>
.v-progress-circular {
  margin: 1rem;
}
.timer-counter {
  width: 100%;
  margin: 2rem auto;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.timer-msgs {
  text-align: center;
  margin-top: 1rem;
}
.timer-msg {
  font-size: 1.5rem;
  color: #555;
}
.timer-mini-msg {
  font-size: 1rem;
  color: #777;
  margin-top: 0.5rem;
}
</style>
