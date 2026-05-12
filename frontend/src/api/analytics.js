import client from './client'

export const analyticsApi = {
  getSummary: () => client.get('/analytics/summary'),
}
