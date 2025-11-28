const API_BASE = '/api'

export async function fetchIncidents(params = {}) {
  const query = new URLSearchParams()

  Object.entries(params).forEach(([key, value]) => {
    if (value !== null && value !== undefined) {
      query.append(key, value)
    }
  })

  const url = `${API_BASE}/incidents/?${query.toString()}`
  const response = await fetch(url)

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`)
  }

  return await response.json()
}

export async function fetchIncidentById(id) {
  const response = await fetch(`${API_BASE}/incidents/${id}`)

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`)
  }

  return await response.json()
}

export async function fetchStats() {
  const response = await fetch(`${API_BASE}/stats`)

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`)
  }

  return await response.json()
}

export async function fetchRestrictedAreas() {
  const response = await fetch(`${API_BASE}/restricted-areas/`)

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`)
  }

  return await response.json()
}

export async function fetchPatterns() {
  const response = await fetch(`${API_BASE}/patterns/`)

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`)
  }

  return await response.json()
}
