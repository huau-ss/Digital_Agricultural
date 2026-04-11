import api from '@/utils/request'

export const authAPI = {
  register(data) {
    return api.post('/auth/register/', data)
  },
  
  login(data) {
    return api.post('/auth/login/', data)
  },
  
  logout(data) {
    return api.post('/auth/logout/', data)
  },
  
  getProfile() {
    return api.get('/auth/profile/')
  },
  
  updateProfile(data) {
    return api.patch('/auth/profile/', data)
  },
  
  changePassword(data) {
    return api.post('/auth/change-password/', data)
  },
  
  refreshToken(refresh) {
    return api.post('/auth/token/refresh/', { refresh })
  }
}
