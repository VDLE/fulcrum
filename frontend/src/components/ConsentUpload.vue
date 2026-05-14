<template>
  <v-container fluid>
    <FileUploadAndPreview
      :modelValue="consentUpload"
      :preview-disabled="!consentUpload"
      @update:modelValue="$emit('update:consentUpload', $event ?? null)"
      label="Consent Form (PDF)"
      accept=".pdf"
      @preview="previewConsentForm"
    />

    <ConsentAckScreen
      :display="showConsentPreview"
      @update:display="$emit('update:showConsentPreview', $event)"
      :form="consentUpload"
      :liveSession="false"
    />
  </v-container>
</template>

<script>
import FileUploadAndPreview from '@/components/FileUploadAndPreview.vue'
import ConsentAckScreen from '@/components/ConsentAckScreen.vue'

export default {
  components: {
    FileUploadAndPreview,
    ConsentAckScreen,
  },
  props: {
    consentUpload: File,
    showConsentPreview: Boolean,
  },
  emits: ['update:consentUpload', 'update:showConsentPreview'],
  methods: {
    previewConsentForm() {
      if (this.consentUpload) {
        this.$emit('update:showConsentPreview', true)
      }
    },
  },
}
</script>
