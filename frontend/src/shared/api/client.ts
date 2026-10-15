import { emitApiStatus } from './status'
import axios from 'axios'

export const api = axios.create({
  baseURL: '/api/v1',
  withCredentials: true,
})

let csrfToken: string | null = null

async function fetchCsrfToken(): Promise<string> {
  if (csrfToken) return csrfToken
  const { data } = await axios.get('/api/v1/csrf', { withCredentials: true })
  csrfToken = data.csrfToken
  return csrfToken!
}

api.interceptors.request.use(async (config) => {
  if (config.method && ['post', 'put', 'patch', 'delete'].includes(config.method.toLowerCase())) {
    const token = await fetchCsrfToken()
    config.headers['X-CSRFToken'] = token
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const config = error.config
    const message = error.response?.data?.message
    const isCsrfError =
      error.response?.status === 400 &&
      typeof message === 'string' &&
      message.toLowerCase().includes('csrf')

    if (isCsrfError && config && !config._csrfRetried) {
      config._csrfRetried = true
      csrfToken = null
      return api(config)
    }
    if (error.response?.status === 401 || error.response?.status === 403) {
      emitApiStatus(error.response.status)
    }
    return Promise.reject(error)
  },
)
