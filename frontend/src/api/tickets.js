import client from './client'

export const ticketsApi = {
  list: (params = {}) => client.get('/tickets', { params }),
  get: (id) => client.get(`/tickets/${id}`),
  getLogs: (id) => client.get(`/tickets/${id}/logs`),
  createManual: (data) => client.post('/tickets/manual', data),
  createAuto: (data) => client.post('/tickets/auto', data),
  update: (id, data) => client.put(`/tickets/${id}`, data),
  resolve: (id, data) => client.post(`/tickets/${id}/resolve`, data),
  close: (id) => client.post(`/tickets/${id}/close`),
}
