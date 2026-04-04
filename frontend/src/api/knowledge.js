import client from './client'

export const knowledgeApi = {
  getStats: () => client.get('/knowledge/stats'),
  list: (params = {}) => client.get('/knowledge', { params }),
  create: (data) => client.post('/knowledge', data),
  update: (id, data) => client.put(`/knowledge/${id}`, data),
  remove: (id) => client.delete(`/knowledge/${id}`),
}
