import client from './client'

export const authApi = {
  login: (username, password) =>
    client.post('/auth/login', { username, password }),
}
