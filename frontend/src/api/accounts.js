import client from './client'

export const accountsApi = {
  getMe: () => client.get('/accounts/me'),
  updateMe: (data) => client.put('/accounts/me', data),
  changePassword: (data) => client.patch('/accounts/me/password', data),

  list: (params = {}) => client.get('/accounts', { params }),
  get: (id) => client.get(`/accounts/${id}`),
  create: (data) => client.post('/accounts', data),
  update: (id, data) => client.put(`/accounts/${id}`, data),
  freeze: (id) => client.patch(`/accounts/${id}/freeze`),
  unfreeze: (id) => client.patch(`/accounts/${id}/unfreeze`),
  resetPassword: (id, newPassword) =>
    client.patch(`/accounts/${id}/reset-password`, { new_password: newPassword }),
}
