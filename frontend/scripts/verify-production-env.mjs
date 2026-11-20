import fs from 'node:fs';

if (!process.env.VERCEL) {
  process.exit(0);
}

const apiUrl = process.env.VITE_API_URL?.trim();
if (!apiUrl) {
  throw new Error('VITE_API_URL is required for Vercel builds.');
}

if (
  apiUrl.includes('localhost') ||
  apiUrl.includes('127.0.0.1') ||
  !apiUrl.startsWith('https://')
) {
  throw new Error('VITE_API_URL must be an HTTPS public API URL for Vercel.');
}

console.log('Production frontend API configuration verified.');
