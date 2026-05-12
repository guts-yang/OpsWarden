import client from './client'

export const knowledgeApi = {
  getStats: () => client.get('/knowledge/stats'),
  /** @param {{ limit?: number }} params */
  quickPrompts: (params = {}) => client.get('/knowledge/quick-prompts', { params }),
  list: (params = {}) => client.get('/knowledge', { params }),
  create: (data) => client.post('/knowledge', data),
  update: (id, data) => client.put(`/knowledge/${id}`, data),
  remove: (id) => client.delete(`/knowledge/${id}`),
  /** @param {{ doc_id: string, page_index?: number }} params */
  removeByDoc: (params) => client.delete('/knowledge/by-doc', { params }),
}
