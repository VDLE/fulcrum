<template>
  <v-container fluid>
    <v-text-field
      :modelValue="studyName"
      @update:modelValue="$emit('update:studyName', $event)"
      :counter="25"
      label="Study Name *"
      :rules="studyNameRules"
    />

    <v-text-field
      :modelValue="studyDescription"
      @update:modelValue="$emit('update:studyDescription', $event)"
      :counter="250"
      label="Study Description"
      :rules="studyDescriptionRules"
    />

    <div class="flex-row">
      <v-select
        :modelValue="studyDesignType"
        @update:modelValue="$emit('update:studyDesignType', $event)"
        :items="['Between', 'Within']"
        label="Study Design Type *"
        :rules="studyDesignTypeRules"
      />

      <v-text-field
        :modelValue="participantCount"
        @update:modelValue="$emit('update:participantCount', $event)"
        type="number"
        label="Expected # of Participants *"
        :rules="participantCountRules"
      />
    </div>
  </v-container>
</template>

<script>
export default {
  props: {
    studyName: String,
    studyDescription: String,
    studyDesignType: String,
    participantCount: [String, Number],
    studyNameRules: Array,
    studyDescriptionRules: Array,
    studyDesignTypeRules: Array,
    participantCountRules: Array,
  },
  emits: [
    'update:studyName',
    'update:studyDescription',
    'update:studyDesignType',
    'update:participantCount',
  ],
}
</script>
