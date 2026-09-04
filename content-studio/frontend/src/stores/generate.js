import { defineStore } from 'pinia'

/**
 * 选题预填 Store
 * 用于从"选题库"页面一键跳转到"文案生成"页时携带数据
 */
export const useGenerateStore = defineStore('generate', {
  state: () => ({
    prefillTopic: null, // { title, description, keyword, platform, product_doc_ids, viral_analysis_ids, autoGenerate }
  }),
  actions: {
    setPrefillTopic(topic) {
      this.prefillTopic = topic
    },
    clearPrefillTopic() {
      this.prefillTopic = null
    },
  },
})
