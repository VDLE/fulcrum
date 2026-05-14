<template>
  <v-card class="component-surface pa-0">
    <v-text-field
      :modelValue="modelValue"
      @update:modelValue="$emit('update:modelValue', $event)"
      label="Search"
      prepend-inner-icon="mdi-magnify"
      variant="outlined"
      hide-details
      single-line
      density="comfortable"
    />
  </v-card>
</template>

<script>
export default {
  props: {
    modelValue: String,
  },
  emits: ['update:modelValue'],
}
</script>
