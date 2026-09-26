const API_BASE = 'http://localhost:8000'

export type Course = {
  id: number
  code: string
  name: string
  capacity: number
  remaining: number
}

export async function login(username: string, password: string) {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })
  if (!res.ok) throw new Error('登录失败')
  return res.json() as Promise<{ access_token: string }>
}

export async function getCourses(token: string, deviceId: string) {
  const res = await fetch(`${API_BASE}/courses`, {
    headers: { Authorization: `Bearer ${token}`, 'X-Device-Id': deviceId },
  })
  if (!res.ok) throw new Error('课程加载失败')
  return res.json() as Promise<Course[]>
}

export async function selectCourse(token: string, deviceId: string, courseId: number, mode: 'direct' | 'queued') {
  const res = await fetch(`${API_BASE}/courses/${courseId}/select?mode=${mode}`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}`, 'X-Device-Id': deviceId },
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail ?? '请求失败')
  return data as { status: string; message: string; job_id?: string }
}

export async function getJob(token: string, deviceId: string, jobId: string) {
  const res = await fetch(`${API_BASE}/jobs/${jobId}`, {
    headers: { Authorization: `Bearer ${token}`, 'X-Device-Id': deviceId },
  })
  if (!res.ok) throw new Error('任务不存在')
  return res.json() as Promise<{ status: string; message?: string }>
}
