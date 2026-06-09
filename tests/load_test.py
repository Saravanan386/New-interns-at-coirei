import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  vus: 10,
  duration: '30s',
};

const BASE_URL = __ENV.BASE_URL || 'http://127.0.0.1:8000';
const TOKEN = __ENV.TOKEN || '';

function authHeaders() {
  return {
    headers: {
      Authorization: TOKEN ? `Bearer ${TOKEN}` : '',
      'Content-Type': 'application/json',
    },
  };
}

export default function () {
  const endpoints = [
    { name: 'auth_login', method: 'POST', url: `${BASE_URL}/auth/login`, body: JSON.stringify({ email: 'test@example.com', password: 'password' }) },
    { name: 'dashboard_courses', method: 'GET', url: `${BASE_URL}/dashboard/courses` },
    { name: 'classes_summary', method: 'GET', url: `${BASE_URL}/dashboard/classes-summary` },
    { name: 'list_classrooms', method: 'GET', url: `${BASE_URL}/classrooms/` },
    { name: 'get_course_classrooms', method: 'GET', url: `${BASE_URL}/classrooms/course/1` },
    { name: 'get_classroom', method: 'GET', url: `${BASE_URL}/classrooms/1` },
    { name: 'get_classroom_schedule', method: 'GET', url: `${BASE_URL}/classrooms/1/schedule` },
    { name: 'get_attendance', method: 'GET', url: `${BASE_URL}/attendance/session/1` },
    { name: 'get_course_overview', method: 'GET', url: `${BASE_URL}/courses/1/full-overview` },
    { name: 'student_dashboard', method: 'GET', url: `${BASE_URL}/student/dashboard` },
    { name: 'student_materials', method: 'GET', url: `${BASE_URL}/student/materials` },
    { name: 'student_assignments', method: 'GET', url: `${BASE_URL}/student/assignments` },
    { name: 'student_tests', method: 'GET', url: `${BASE_URL}/student/tests` },
    { name: 'student_certificates', method: 'GET', url: `${BASE_URL}/student/certificates` },
  ];

  for (const ep of endpoints) {
    let res;

    if (ep.method === 'GET') {
      res = http.get(ep.url, { tags: { name: ep.name }, ...authHeaders() });
    } else {
      res = http.request(ep.method, ep.url, ep.body || null, {
        tags: { name: ep.name },
        ...authHeaders(),
      });
    }

    check(res, {
      [`${ep.name} status is 2xx`]: (r) => r.status >= 200 && r.status < 300,
    });
  }

  sleep(1);
}