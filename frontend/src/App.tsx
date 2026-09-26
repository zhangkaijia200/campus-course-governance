import { useEffect, useMemo, useState } from 'react'
import { Course, getCourses, getJob, login, selectCourse } from './api'

export default function App() {
  const [username, setUsername] = useState('student1')
  const [password, setPassword] = useState('demo123')
  const [token, setToken] = useState(localStorage.getItem('token') ?? '')
  const [courses, setCourses] = useState<Course[]>([])
  const [message, setMessage] = useState('')
  const deviceId = useMemo(() => {
    const key = 'deviceId'
    const existing = localStorage.getItem(key)
    if (existing) return existing
    const created = `browser-${crypto.randomUUID().slice(0, 8)}`
    localStorage.setItem(key, created)
    return created
  }, [])

  async function loadCourses(t = token) {
    if (!t) return
    try {
      setCourses(await getCourses(t, deviceId))
    } catch (e) {
      setMessage((e as Error).message)
    }
  }

  useEffect(() => { void loadCourses() }, [token])

  async function doLogin() {
    try {
      const data = await login(username, password)
      localStorage.setItem('token', data.access_token)
      setToken(data.access_token)
      setMessage(`登录成功，设备标识：${deviceId}`)
    } catch (e) {
      setMessage((e as Error).message)
    }
  }

  async function choose(courseId: number, mode: 'direct' | 'queued') {
    try {
      const data = await selectCourse(token, deviceId, courseId, mode)
      if (data.job_id) {
        setMessage(`已排队，任务 ${data.job_id.slice(0, 8)}…`)
        const timer = setInterval(async () => {
          const job = await getJob(token, deviceId, data.job_id!)
          setMessage(`队列任务：${job.status} - ${job.message ?? ''}`)
          if (!['queued', 'processing'].includes(job.status)) {
            clearInterval(timer)
            void loadCourses()
          }
        }, 800)
      } else {
        setMessage(`${data.status}: ${data.message}`)
        void loadCourses()
      }
    } catch (e) {
      setMessage((e as Error).message)
    }
  }

  return (
    <main className="shell">
      <section className="hero">
        <p className="eyebrow">Course Governance Lab</p>
        <h1>高校选课高并发访问治理系统</h1>
        <p>Token 身份认证 · Redis 账号级限流 · 幂等 · Stream 排队 · MySQL 一致性</p>
      </section>

      {!token ? (
        <section className="panel login">
          <h2>演示登录</h2>
          <input value={username} onChange={e => setUsername(e.target.value)} placeholder="用户名" />
          <input value={password} onChange={e => setPassword(e.target.value)} type="password" placeholder="密码" />
          <button onClick={doLogin}>登录</button>
        </section>
      ) : (
        <>
          <section className="statusbar">
            <span>Device: {deviceId}</span>
            <button className="ghost" onClick={() => { localStorage.removeItem('token'); setToken('') }}>退出</button>
          </section>
          <section className="grid">
            {courses.map(course => (
              <article className="card" key={course.id}>
                <div className="course-code">{course.code}</div>
                <h3>{course.name}</h3>
                <div className="capacity">剩余 <strong>{course.remaining}</strong> / {course.capacity}</div>
                <div className="actions">
                  <button onClick={() => choose(course.id, 'queued')}>排队选课</button>
                  <button className="secondary" onClick={() => choose(course.id, 'direct')}>直接模式</button>
                </div>
              </article>
            ))}
          </section>
        </>
      )}
      {message && <section className="toast">{message}</section>}
    </main>
  )
}
