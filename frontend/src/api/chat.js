import client from './client'

export const chatApi = {
  send: (query) => client.post('/chat', { query }),
}
