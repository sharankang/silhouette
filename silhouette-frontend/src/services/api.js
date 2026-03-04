import axios from 'axios'

const client = axios.create({
  baseURL: '/api',
  timeout: 300000,
})

client.interceptors.response.use(
  res => res.data,
  err => { throw err.response?.data || err }
)

const api = {
  
  getWardrobe: (filters = {}) =>
    client.get('/wardrobe', { params: filters }),

  autoTag: (formData) =>
    client.post('/wardrobe/auto-tag', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }),

  addClothingItem: (formData) =>
    client.post('/wardrobe', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }),

  updateClothingItem: (id, tags) =>
    client.patch(`/wardrobe/${id}`, tags),

  deleteClothingItem: (id) =>
    client.delete(`/wardrobe/${id}`),

  
  sendMessage: (formData) =>
    client.post('/chat', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }),

  
  getOutfits: () =>
    client.get('/outfits'),

  saveManualOutfit: (items) =>
    client.post('/outfits/manual', { items }),

  rateOutfit: (id, rating) =>
    client.patch(`/outfits/${id}/rate`, { rating }),

  deleteOutfit: (id) =>
    client.delete(`/outfits/${id}`),

  regenerateOutfit: (id) =>
    client.post(`/outfits/${id}/regenerate`),
}

export default api