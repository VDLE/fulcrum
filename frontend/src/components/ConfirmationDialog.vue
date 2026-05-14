<template>
  <div class="text-center pa-4">
    <v-dialog v-model="visible" max-width="400" persistent>
      <v-card
        prepend-icon="mdi-alert-outline"
        :title="dialogDetails.title"
        :text="dialogDetails.text"
      >
        <template v-slot:actions>
          <v-spacer></v-spacer>

          <v-btn @click="cancel"> Cancel </v-btn>

          <v-btn @click="confirm"> Agree </v-btn>
        </template>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
export default {
  name: 'ConfirmationDialog',
  props: {
    modelValue: {
      type: Boolean,
      required: true,
    },
    dialogDetails: {
      type: Object,
      default: () => ({
        title: 'Confirmation',
        text: 'Are you sure?',
        source: null,
      }),
    },
  },
  computed: {
    visible: {
      get() {
        return this.modelValue
      },
      set(val) {
        this.$emit('update:modelValue', val)
      },
    },
  },
  methods: {
    confirm() {
      this.$emit('confirm', this.dialogDetails.source)
      this.visible = false
    },
    cancel() {
      this.$emit('cancel')
      this.visible = false
    },
  },
}
</script>
