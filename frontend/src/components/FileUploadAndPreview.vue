<template>
  <v-row class="mt-2">
    <!-- File upload field -->
    <v-col cols="6">
      <v-file-input
        :model-value="modelValue"
        :label="label"
        :accept="accept"
        variant="outlined"
        show-size
        hide-details
        clearable
        @update:modelValue="$emit('update:modelValue', $event)"
      ></v-file-input>
    </v-col>

    <!-- Preview button -->
    <v-col cols="2" class="d-flex align-center">
      <v-btn
        variant="text"
        color="primary"
        prepend-icon="mdi-eye-outline"
        @click="$emit('preview')"
        :disabled="previewDisabled"
      >
        Preview
      </v-btn>
    </v-col>
  </v-row>
</template>

<script>
export default {
  props: {
    modelValue: {
      type: [File, Object, null],
      required: false,
      default: null,
    },
    label: {
      type: String,
      required: true,
    },
    accept: {
      type: String,
      required: true,
    },
    previewDisabled: {
      type: Boolean,
      default: true,
    },
  },
  emits: ['update:modelValue', 'preview'],
  watch: {
    modelValue(newVal) {
      if (newVal == undefined || newVal == null) {
        this.$emit('update:modelValue', null)
      }
    },
  },
}
</script>
