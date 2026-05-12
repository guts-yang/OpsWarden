import client from './client'

export const chatApi = {
  /** @param {{ query: string, thread_id?: string }} body */
  send: (body) => client.post('/chat', body),
}
